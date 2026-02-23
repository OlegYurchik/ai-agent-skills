"""
Nextcloud CLI Client

A client for interacting with Nextcloud via WebDAV API for managing files,
calendars, and contacts.
"""

import argparse
import base64
import datetime
import logging
import os
import re
import sys
import uuid
import urllib.error
import urllib.request
from dataclasses import dataclass
from http.client import HTTPResponse
from typing import Any, Optional

import xml.etree.ElementTree as ET

DEFAULT_TIMEOUT: int = 30
DAV_NAMESPACE: str = "DAV:"
CAL_NAMESPACE: str = "urn:ietf:params:xml:ns:caldav"
CARD_NAMESPACE: str = "urn:ietf:params:xml:ns:carddav"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)


class NextcloudError(Exception):
    pass


class HTTPRequestError(NextcloudError):
    def __init__(self, status: int, url: str, message: str | None = None):
        self.status = status
        self.url = url
        self.message = message or f"HTTP error {status} for {url}"
        super().__init__(self.message)


class HTTPRequestStatusException(HTTPRequestError):
    def __init__(self, status: int, url: str):
        super().__init__(status, url, f"Incorrect status '{status}' for {url}")


class NextcloudAuthError(NextcloudError):
    def __init__(self, url: str):
        super().__init__(f"Authentication error for {url}")


@dataclass
class FileEntry:
    name: str
    path: str
    is_directory: bool = False


@dataclass
class CalendarEntry:
    name: str
    href: str


@dataclass
class EventEntry:
    href: str


@dataclass
class CardEntry:
    href: str


class NextcloudClient:
    """Base client for interacting with Nextcloud API."""

    def __init__(
            self,
            url: str,
            user: str,
            password: str,
            timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        Initialize the client.

        Args:
            url: Nextcloud server URL (e.g., https://nextcloud.example.com)
            user: Username
            password: User password
            timeout: Request timeout in seconds

        Raises:
            ValueError: If URL is empty or invalid
        """
        if not url:
            raise ValueError("URL cannot be empty")
        self.url: str = url.rstrip("/")
        self.user: str = user
        self.password: str = password
        self.timeout: int = timeout
        self.auth: str = self._build_auth_header(user, password)

    @staticmethod
    def _build_auth_header(user: str, password: str) -> str:
        credentials = f"{user}:{password}".encode("utf-8")
        return base64.b64encode(credentials).decode("utf-8")

    def _request(
            self,
            method: str,
            path: str,
            data: bytes | None = None,
            headers: dict[str, str] | None = None,
    ) -> HTTPResponse:
        full_url = f"{self.url}{path}"
        request = urllib.request.Request(full_url, method=method, data=data)
        request.add_header("Authorization", f"Basic {self.auth}")

        if headers:
            for key, value in headers.items():
                request.add_header(key, value)

        try:
            return urllib.request.urlopen(request, timeout=self.timeout)
        except urllib.error.HTTPError as e:
            raise HTTPRequestError(status=e.code, url=full_url) from e
        except urllib.error.URLError as e:
            raise NextcloudError(
                f"Network error when requesting {full_url}: {e.reason}"
            ) from e

    def _parse_xml_data(
            self,
            xml_data: str | bytes,
            href_tag: str = f"{{{DAV_NAMESPACE}}}href",
    ) -> list[str]:
        if isinstance(xml_data, bytes):
            xml_data = xml_data.decode()
        try:
            root = ET.fromstring(xml_data)
        except ET.ParseError as e:
            raise NextcloudError(f"XML parsing error: {e}") from e

        results: list[str] = []
        for response_elem in root.iter(f"{{{DAV_NAMESPACE}}}response"):
            element = response_elem.find(href_tag)
            if element is not None and element.text:
                results.append(element.text.strip())
        return results

    def raise_for_status(self, response: HTTPResponse) -> None:
        if response.status // 100 >= 4:
            raise HTTPRequestStatusException(status=response.status, url=response.url)


class NextcloudFilesClient(NextcloudClient):
    def _build_file_path(self, path: str) -> str:
        clean_path = path.lstrip("/")
        return f"/remote.php/dav/files/{self.user}/{clean_path}"

    def list_files(self, path: str = "/", depth: str = "1") -> list[FileEntry]:
        full_path = self._build_file_path(path)
        response = self._request(
            "PROPFIND",
            full_path,
            headers={"Depth": depth, "Content-Type": "application/xml"},
        )

        if response.status != 207:
            return []

        hrefs = self._parse_xml_data(response.read().decode())
        entries: list[FileEntry] = []

        for href in hrefs:
            name = href.rstrip("/").split("/")[-1] if "/" in href else href
            if name in ("", self.user):
                continue
            entries.append(
                FileEntry(name=name, path=href, is_directory=href.endswith("/")),
            )

        return entries

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"File not found: {local_path}")

        with open(local_path, "rb") as f:
            data = f.read()

        full_path = self._build_file_path(remote_path)
        response = self._request(
            "PUT",
            full_path,
            data,
            {"Content-Type": "application/octet-stream"},
        )
        self.raise_for_status(response)
        return response.status in (201, 204)

    def download_file(self, remote_path: str, local_path: str) -> bool:
        full_path = self._build_file_path(remote_path)
        response = self._request("GET", full_path)

        if response.status == 200:
            os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(response.read())
            return True
        return False

    def delete_file(self, path: str) -> bool:
        full_path = self._build_file_path(path)
        response = self._request("DELETE", full_path)
        return response.status in (200, 204)

    def mkdir(self, path: str) -> bool:
        full_path = self._build_file_path(path)
        try:
            response = self._request(
                "MKCOL",
                full_path,
                headers={"Content-Type": "application/xml"},
            )
            return response.status == 201
        except HTTPRequestError as e:
            if e.status in (405, 409):
                return True
            raise e
        except NextcloudError:
            return False


class NextcloudCalendarClient(NextcloudClient):
    def list_calendars(self) -> list[CalendarEntry]:
        response = self._request(
            "PROPFIND",
            f"/remote.php/dav/calendars/{self.user}/",
            headers={"Depth": "1", "Content-Type": "application/xml"},
        )

        if response.status != 207:
            return []

        hrefs = self._parse_xml_data(response.read().decode())
        entries: list[CalendarEntry] = []

        for href in hrefs:
            parts = href.rstrip("/").split("/")
            name = parts[-1] if len(parts) > 2 else href
            entries.append(CalendarEntry(name=name, href=href))

        return entries

    def list_events(
            self,
            calendar_path: str,
            start_date: str,
            end_date: str,
    ) -> list[EventEntry]:
        begin = f"{start_date.replace('-', '')}T000000Z"
        end = f"{end_date.replace('-', '')}T235959Z"

        xml = (
            '<?xml version="1.0" encoding="utf-8"?>'
            f'<cal:calendar-query xmlns:cal="{CAL_NAMESPACE}">'
            '<cal:filter><cal:comp-filter name="VCALENDAR">'
            '<cal:comp-filter name="VEVENT">'
            f'<cal:time-range start="{begin}" end="{end}"/>'
            '</cal:comp-filter>'
            '</cal:comp-filter>'
            '</cal:filter>'
            '</cal:calendar-query>'
        )

        full_path = calendar_path.rstrip("/") + "/"
        response = self._request(
            "REPORT",
            full_path,
            data=xml.encode(),
            headers={"Content-Type": "application/xml", "Depth": "1"},
        )

        if response.status != 207:
            return []

        entries: list[EventEntry] = []
        for href in self._parse_xml_data(response.read()):
            entries.append(EventEntry(href=href))

        return entries

    def create_calendar(self, name: str) -> bool:
        full_path = f"/remote.php/dav/calendars/{self.user}/{name}/"
        xml_body = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<D:mkcol xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:caldav">'
            '<D:set>'
            '<D:prop>'
            '<D:resourcetype>'
            '<D:collection/>'
            '<C:calendar/>'
            '</D:resourcetype>'
            f'<D:displayname>{name}</D:displayname>'
            '</D:prop>'
            '</D:set>'
            '</D:mkcol>'
        )

        try:
            response = self._request(
                "MKCOL",
                full_path,
                data=xml_body.encode("utf-8"),
                headers={"Content-Type": "application/xml; charset=utf-8"},
            )
            return response.status == 201
        except HTTPRequestError as e:
            if e.status in (405, 409):
                return True
            raise

    def delete_calendar(self, name: str) -> bool:
        full_path = f"/remote.php/dav/calendars/{self.user}/{name}/"
        response = self._request("DELETE", full_path)
        self.raise_for_status(response)
        return response.status == 204

    def get_event(self, calendar_path: str, event_href: str) -> str | None:
        full_path = calendar_path.rstrip("/") + "/" + event_href.lstrip("/")
        response = self._request("GET", full_path)
        if response.status == 200:
            return response.read().decode()
        return None

    def create_event(self, calendar_path: str, icalendar_content: str) -> str | None:
        uid_match = re.search(r"UID:(.+)", icalendar_content)
        uid = uid_match.group(1).strip() if uid_match else uuid.uuid4().hex
        filename = re.sub(r"[^a-zA-Z0-9._-]", "_", uid) + ".ics"

        full_path = calendar_path.rstrip("/") + "/" + filename
        response = self._request(
            "PUT",
            full_path,
            icalendar_content.encode("utf-8"),
            {"Content-Type": "text/calendar; charset=utf-8"},
        )
        self.raise_for_status(response)
        return filename

    def update_event(
        self, calendar_path: str, event_href: str, icalendar_content: str
    ) -> bool:
        """
        Update existing event.

        Args:
            calendar_path: Path to calendar
            event_href: Event href
            icalendar_content: Updated iCalendar content

        Returns:
            True on success
        """
        full_path = calendar_path.rstrip("/") + "/" + event_href.lstrip("/")
        response = self._request(
            "PUT",
            full_path,
            icalendar_content.encode("utf-8"),
            {"Content-Type": "text/calendar; charset=utf-8"},
        )

        self.raise_for_status(response)
        return response.status in (200, 204, 201)

    def delete_event(self, calendar_path: str, event_href: str) -> bool:
        full_path = calendar_path.rstrip("/") + "/" + event_href.lstrip("/")
        response = self._request("DELETE", full_path)
        return response.status in (200, 204)

    def _format_datetime(self, dt_str: str) -> str:
        dt_str = dt_str.strip()
        if "T" in dt_str:
            try:
                return datetime.datetime.fromisoformat(
                    dt_str.replace("Z", "+00:00")
                ).strftime("%Y%m%dT%H%M%SZ")
            except ValueError:
                pass
        try:
            return datetime.datetime.fromisoformat(dt_str).strftime("%Y%m%d")
        except ValueError:
            pass
        return dt_str.replace("-", "").replace(":", "").replace("T", "")

    def create_event_from_params(
        self,
        calendar_path: str,
        summary: str,
        start: str,
        end: str,
        description: str = "",
        location: str = "",
    ) -> str | None:
        start_fmt = self._format_datetime(start)
        end_fmt = self._format_datetime(end)
        uid = f"{uuid.uuid4().hex}@nextcloud"
        dtstamp = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
        ical = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Nextcloud CLI//EN",
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp}",
            f"SUMMARY:{summary}",
            f"DTSTART:{start_fmt}",
            f"DTEND:{end_fmt}",
        ]
        if description:
            ical.append(f"DESCRIPTION:{description}")
        if location:
            ical.append(f"LOCATION:{location}")
        ical.extend(["END:VEVENT", "END:VCALENDAR"])
        return self.create_event(calendar_path, "\r\n".join(ical))

    def update_event_from_params(
            self,
            calendar_path: str,
            event_href: str,
            summary: str,
            start: str,
            end: str,
            description: str = "",
            location: str = "",
    ) -> bool:
        existing_content = self.get_event(calendar_path, event_href)
        uid = ""
        if existing_content:
            uid_match = re.search(r"UID:(.+)", existing_content)
            if uid_match:
                uid = uid_match.group(1).strip()
        start_fmt = self._format_datetime(start)
        end_fmt = self._format_datetime(end)
        if not uid:
            uid = f"{uuid.uuid4().hex}@nextcloud"
        dtstamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y%m%dT%H%M%SZ"
        )
        ical = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Nextcloud CLI//EN",
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp}",
            f"SUMMARY:{summary}",
            f"DTSTART:{start_fmt}",
            f"DTEND:{end_fmt}",
        ]
        if description:
            ical.append(f"DESCRIPTION:{description}")
        if location:
            ical.append(f"LOCATION:{location}")
        ical.extend(["END:VEVENT", "END:VCALENDAR"])
        return self.update_event(calendar_path, event_href, "\r\n".join(ical))


class NextcloudContactsClient(NextcloudClient):
    def _get_addressbook_path(self) -> str:
        return f"/remote.php/dav/addressbooks/users/{self.user}/contacts/"

    def list_cards(self) -> list[CardEntry]:
        addressbook_path = self._get_addressbook_path()
        response = self._request(
            "PROPFIND",
            addressbook_path,
            headers={"Depth": "1", "Content-Type": "application/xml"},
        )

        if response.status != 207:
            return []

        hrefs = self._parse_xml_data(response.read().decode())
        entries: list[CardEntry] = []

        for href in hrefs:
            if href.rstrip("/") == addressbook_path.rstrip("/"):
                continue
            if not href.endswith(".vcf"):
                continue
            entries.append(CardEntry(href=href))

        return entries

    def search_contacts(self, query: str) -> list[CardEntry]:
        addressbook_path = self._get_addressbook_path()
        response = self._request(
            "PROPFIND",
            addressbook_path,
            headers={"Depth": "1", "Content-Type": "application/xml"},
        )

        if response.status != 207:
            return []

        hrefs = self._parse_xml_data(response.read().decode())
        entries: list[CardEntry] = []

        for href in hrefs:
            if href.rstrip("/") == addressbook_path.rstrip("/"):
                continue
            if not href.endswith(".vcf"):
                continue
            entries.append(CardEntry(href=href))

        if query:
            entries = [e for e in entries if query.lower() in e.href.lower()]

        return entries

    def get_card(self, card_href: str) -> str | None:
        full_path = card_href.lstrip("/")
        if not full_path.startswith("/"):
            full_path = "/" + full_path
        response = self._request("GET", full_path)
        return response.read().decode() if response.status == 200 else None

    def create_card(self, card_href: str, vcard_content: str) -> str | None:
        full_path = card_href.lstrip("/")
        if not full_path.startswith("/"):
            full_path = "/" + full_path
        response = self._request(
            "PUT",
            full_path,
            vcard_content.encode("utf-8"),
            {"Content-Type": "text/vcard; charset=utf-8"},
        )
        self.raise_for_status(response)

        if response.url:
            base_url = self.url.rstrip("/")
            full_url = response.url.rstrip("/")
            return (
                full_url[len(base_url) :] if full_url.startswith(base_url) else full_url
            )
        return None

    def update_card(self, card_href: str, vcard_content: str) -> bool:
        full_path = card_href.lstrip("/")
        if not full_path.startswith("/"):
            full_path = "/" + full_path
        response = self._request(
            "PUT",
            full_path,
            vcard_content.encode("utf-8"),
            {"Content-Type": "text/vcard; charset=utf-8"},
        )
        self.raise_for_status(response)
        return response.status in (200, 204, 201)

    def delete_card(self, card_href: str) -> bool:
        full_path = card_href.lstrip("/")
        if not full_path.startswith("/"):
            full_path = "/" + full_path
        response = self._request("DELETE", full_path)
        return response.status in (200, 204)

    def create_card_from_params(
        self,
        card_href: str,
        first_name: str = "",
        last_name: str = "",
        email: str = "",
        phone: str = "",
        organization: str = "",
        note: str = "",
    ) -> str | None:
        uid = f"{uuid.uuid4().hex}@nextcloud"
        vcard = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"UID:{uid}",
            "PRODID:-//Nextcloud CLI//EN",
        ]

        if first_name:
            vcard.append(f"FN:{first_name}")
            vcard.append(f"N:{last_name};{first_name};;;")
        else:
            vcard.append("FN:")

        if last_name:
            vcard.append(f"NICKNAME:{last_name}")
        if email:
            vcard.append(f"EMAIL:{email}")
        if phone:
            vcard.append(f"TEL:{phone}")
        if organization:
            vcard.append(f"ORG:{organization}")
        if note:
            vcard.append(f"NOTE:{note}")

        vcard.append("END:VCARD")

        filename = f"{uid}.vcf"
        full_path = card_href.rstrip("/") + "/" + filename

        return self.create_card(full_path, "\r\n".join(vcard))

    def update_card_from_params(
            self,
            card_href: str,
            first_name: str = "",
            last_name: str = "",
            email: str = "",
            phone: str = "",
            organization: str = "",
            note: str = "",
    ) -> bool:
        existing_content = self.get_card(card_href)
        uid = ""
        if existing_content:
            uid_match = re.search(r"UID:(.+)", existing_content)
            if uid_match:
                uid = uid_match.group(1).strip()

        if not uid:
            uid = f"{uuid.uuid4().hex}@nextcloud"

        vcard = [
            "BEGIN:VCARD",
            "VERSION:3.0",
            f"UID:{uid}",
            "PRODID:-//Nextcloud CLI//EN",
        ]

        if first_name:
            vcard.append(f"FN:{first_name}")
            vcard.append(f"N:{last_name};{first_name};;;")
        else:
            vcard.append("FN:")

        if last_name:
            vcard.append(f"NICKNAME:{last_name}")
        if email:
            vcard.append(f"EMAIL:{email}")
        if phone:
            vcard.append(f"TEL:{phone}")
        if organization:
            vcard.append(f"ORG:{organization}")
        if note:
            vcard.append(f"NOTE:{note}")

        vcard.append("END:VCARD")

        return self.update_card(card_href, "\r\n".join(vcard))


def get_calendar_path(
    client: NextcloudCalendarClient, calendar_name_or_path: str
) -> str:
    if calendar_name_or_path.startswith("/"):
        return calendar_name_or_path

    calendars = client.list_calendars()
    for cal in calendars:
        if cal.name == calendar_name_or_path:
            return cal.href

    raise NextcloudError(f"Calendar '{calendar_name_or_path}' not found")


def print_file_list(files: list[FileEntry]) -> None:
    for f in files:
        print(f"  {f.name}{'/' if f.is_directory else ''}")


def print_calendar_list(calendars: list[CalendarEntry]) -> None:
    for cal in calendars:
        print(f"  {cal.name}: {cal.href}")


def print_event_list(events: list[EventEntry]) -> None:
    for event in events:
        print(f"  Event: {event.href}")


def print_card_list(cards: list[CardEntry]) -> None:
    for card in cards:
        print(f"  {card.href}")


def get_card_path(client: NextcloudContactsClient, card_name_or_path: str) -> str:
    if card_name_or_path.startswith("/"):
        return card_name_or_path

    cards = client.list_cards()
    for card in cards:
        href_name = (
            card.href.rstrip("/").split("/")[-1] if "/" in card.href else card.href
        )
        if href_name == card_name_or_path:
            return card.href

    raise NextcloudError(f"Contact card '{card_name_or_path}' not found")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Nextcloud CLI Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n\n"
            "python skill.py --url https://nextcloud.example.com --user admin --pass password file-list\n"
            "python skill.py --url https://nextcloud.example.com --user admin --pass password file-upload local.txt /remote.txt\n"
            "python skill.py --url https://nextcloud.example.com --user admin --pass password cal-list\n"
            "python skill.py --url https://nextcloud.example.com --user admin --pass password cal-create mycalendar\n"
            "python skill.py --url https://nextcloud.example.com --user admin --pass password cal-events mycalendar 2024-01-01 2024-12-31\n"
            "python skill.py --url https://nextcloud.example.com --user admin --pass password card-list\n"
            "python skill.py --url https://nextcloud.example.com --user admin --pass password card-search query\n"
            "python skill.py --url https://nextcloud.example.com --user admin --pass password card-get contact.vcf\n"
            "python skill.py --url https://nextcloud.example.com --user admin --pass password card-create --first-name John --last-name Doe --email john@example.com\n"
            "python skill.py --url https://nextcloud.example.com --user admin --pass password card-update contact.vcf --first-name Jane --last-name Doe\n"
            "python skill.py --url https://nextcloud.example.com --user admin --pass password card-delete contact.vcf\n"
        ),
    )
    parser.add_argument("--url")
    parser.add_argument("--user")
    parser.add_argument("--pass", dest="password")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--verbose", "-v", action="store_true")

    cmd_parser = parser.add_subparsers(dest="command")

    file_parser = cmd_parser.add_parser("file-list")
    file_parser.add_argument("path", nargs="?", default="/")
    file_parser.add_argument("--depth", default="1")

    file_upload = cmd_parser.add_parser("file-upload")
    file_upload.add_argument("local")
    file_upload.add_argument("remote")

    file_download = cmd_parser.add_parser("file-download")
    file_download.add_argument("remote")
    file_download.add_argument("local")

    file_delete = cmd_parser.add_parser("file-delete")
    file_delete.add_argument("path")

    file_mkdir = cmd_parser.add_parser("file-mkdir")
    file_mkdir.add_argument("path")

    cmd_parser.add_parser("cal-list")

    cal_events = cmd_parser.add_parser("cal-events")
    cal_events.add_argument("calendar")
    cal_events.add_argument("start")
    cal_events.add_argument("end")

    cal_create = cmd_parser.add_parser("cal-create")
    cal_create.add_argument("name")

    cal_delete = cmd_parser.add_parser("cal-delete")
    cal_delete.add_argument("name")

    cal_event_get = cmd_parser.add_parser("cal-event-get")
    cal_event_get.add_argument("calendar")
    cal_event_get.add_argument("event")

    cal_event_create = cmd_parser.add_parser("cal-event-create")
    cal_event_create.add_argument("calendar")
    cal_event_create.add_argument("summary")
    cal_event_create.add_argument("start")
    cal_event_create.add_argument("end")
    cal_event_create.add_argument("--description", "-d", default="")
    cal_event_create.add_argument("--location", "-l", default="")

    cal_event_update = cmd_parser.add_parser("cal-event-update")
    cal_event_update.add_argument("calendar")
    cal_event_update.add_argument("event")
    cal_event_update.add_argument("summary")
    cal_event_update.add_argument("start")
    cal_event_update.add_argument("end")
    cal_event_update.add_argument("--description", "-d", default="")
    cal_event_update.add_argument("--location", "-l", default="")

    cal_event_delete = cmd_parser.add_parser("cal-event-delete")
    cal_event_delete.add_argument("calendar")
    cal_event_delete.add_argument("event")

    cmd_parser.add_parser("card-list")

    card_search = cmd_parser.add_parser("card-search")
    card_search.add_argument("query")

    card_get = cmd_parser.add_parser("card-get")
    card_get.add_argument("card")

    card_create = cmd_parser.add_parser("card-create")
    card_create.add_argument("--first-name", "-f", default="")
    card_create.add_argument("--last-name", "-l", default="")
    card_create.add_argument("--email", "-e", default="")
    card_create.add_argument("--phone", "-p", default="")
    card_create.add_argument("--organization", "-o", default="")
    card_create.add_argument("--note", "-n", default="")

    card_update = cmd_parser.add_parser("card-update")
    card_update.add_argument("card")
    card_update.add_argument("--first-name", "-f", default="")
    card_update.add_argument("--last-name", "-l", default="")
    card_update.add_argument("--email", "-e", default="")
    card_update.add_argument("--phone", "-p", default="")
    card_update.add_argument("--organization", "-o", default="")
    card_update.add_argument("--note", "-n", default="")

    card_delete = cmd_parser.add_parser("card-delete")
    card_delete.add_argument("card")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if not args.command:
        parser.print_help()
        return

    url = args.url or os.environ.get("NEXTCLOUD_URL")
    user = args.user or os.environ.get("NEXTCLOUD_USER")
    password = args.password or os.environ.get("NEXTCLOUD_PASSWORD")

    if not url or not user or not password:
        logger.error("Missing required configuration.")
        sys.exit(1)

    try:
        base_client = NextcloudClient(
            url=url, user=user, password=password, timeout=args.timeout
        )
        files_client = NextcloudFilesClient(
            url=url, user=user, password=password, timeout=args.timeout
        )
        cal_client = NextcloudCalendarClient(
            url=url, user=user, password=password, timeout=args.timeout
        )
        card_client = NextcloudContactsClient(
            url=url, user=user, password=password, timeout=args.timeout
        )

        if args.command == "file-list":
            _execute_file_list(files_client, args.path, args.depth)
        elif args.command == "file-upload":
            _execute_file_upload(files_client, args.local, args.remote)
        elif args.command == "file-download":
            _execute_file_download(files_client, args.remote, args.local)
        elif args.command == "file-delete":
            _execute_file_delete(files_client, args.path)
        elif args.command == "file-mkdir":
            _execute_file_mkdir(files_client, args.path)
        elif args.command == "cal-list":
            _execute_cal_list(cal_client)
        elif args.command == "cal-events":
            _execute_cal_events(cal_client, args.calendar, args.start, args.end)
        elif args.command == "cal-create":
            _execute_cal_create(cal_client, args.name)
        elif args.command == "cal-delete":
            _execute_cal_delete(cal_client, args.name)
        elif args.command == "card-list":
            _execute_card_list(card_client)
        elif args.command == "card-search":
            _execute_card_search(card_client, args.query)
        elif args.command == "card-get":
            _execute_card_get(card_client, args.card)
        elif args.command == "card-create":
            _execute_card_create(card_client, args)
        elif args.command == "card-update":
            _execute_card_update(card_client, args)
        elif args.command == "card-delete":
            _execute_card_delete(card_client, args.card)
        elif args.command == "cal-event-get":
            _execute_cal_event_get(cal_client, args.calendar, args.event)
        elif args.command == "cal-event-create":
            _execute_cal_event_create(cal_client, args.calendar, args)
        elif args.command == "cal-event-update":
            _execute_cal_event_update(cal_client, args.calendar, args)
        elif args.command == "cal-event-delete":
            _execute_cal_event_delete(cal_client, args.calendar, args.event)
        else:
            parser.print_help()

    except HTTPRequestError as e:
        logger.error(f"HTTP error: {e.status}")
        sys.exit(1)
    except NextcloudError as e:
        logger.error(f"{e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"{e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"{e}")
        sys.exit(1)


def _execute_file_list(client: NextcloudFilesClient, path: str, depth: str) -> None:
    files = client.list_files(path, depth)
    print_file_list(files)


def _execute_file_upload(
    client: NextcloudFilesClient, local_path: str, remote_path: str
) -> None:
    if not client.upload_file(local_path, remote_path):
        print("File upload failed")
        sys.exit(1)


def _execute_file_download(
    client: NextcloudFilesClient, remote_path: str, local_path: str
) -> None:
    if not client.download_file(remote_path, local_path):
        print("File download failed")
        sys.exit(1)


def _execute_file_delete(client: NextcloudFilesClient, path: str) -> None:
    if not client.delete_file(path):
        print("Delete failed")
        sys.exit(1)


def _execute_file_mkdir(client: NextcloudFilesClient, path: str) -> None:
    if not client.mkdir(path):
        print("Directory creation failed")
        sys.exit(1)


def _execute_cal_list(client: NextcloudCalendarClient) -> None:
    print_calendar_list(client.list_calendars())


def _execute_cal_events(
    client: NextcloudCalendarClient,
    calendar_name_or_path: str,
    start_date: str,
    end_date: str,
) -> None:
    print_event_list(
        client.list_events(
            get_calendar_path(client, calendar_name_or_path), start_date, end_date
        )
    )


def _execute_cal_create(client: NextcloudCalendarClient, name: str) -> None:
    if not client.create_calendar(name):
        print("Calendar creation failed")
        sys.exit(1)


def _execute_cal_delete(client: NextcloudCalendarClient, name: str) -> None:
    if not client.delete_calendar(name):
        print("Calendar deletion failed")
        sys.exit(1)


def _execute_card_list(client: NextcloudContactsClient) -> None:
    print_card_list(client.list_cards())


def _execute_card_search(client: NextcloudContactsClient, query: str) -> None:
    print_card_list(client.search_contacts(query))


def _execute_card_get(client: NextcloudContactsClient, card_name_or_path: str) -> None:
    if not (card_content := client.get_card(get_card_path(client, card_name_or_path))):
        print("Contact not found")
        sys.exit(1)
    print(card_content)


def _execute_card_create(
    client: NextcloudContactsClient, args: argparse.Namespace
) -> None:
    if not (cards := client.list_cards()):
        print("No address book found")
        sys.exit(1)
    card_href = cards[0].href
    card_href = (
        card_href.rsplit("/", 1)[0] + "/" if "/" in card_href else card_href + "/"
    )
    if not (
        card_href := client.create_card_from_params(
            card_href,
            args.first_name,
            args.last_name,
            args.email,
            args.phone,
            args.organization,
            args.note,
        )
    ):
        print("Contact creation failed")
        sys.exit(1)
    print(f"Contact created: {card_href}")


def _execute_card_update(
    client: NextcloudContactsClient, args: argparse.Namespace
) -> None:
    if not client.update_card_from_params(
        get_card_path(client, args.card),
        args.first_name,
        args.last_name,
        args.email,
        args.phone,
        args.organization,
        args.note,
    ):
        print("Contact update failed")
        sys.exit(1)
    print(f"Contact updated: {args.card}")


def _execute_card_delete(
    client: NextcloudContactsClient, card_name_or_path: str
) -> None:
    if not client.delete_card(get_card_path(client, card_name_or_path)):
        print("Contact deletion failed")
        sys.exit(1)
    print(f"Contact deleted: {card_name_or_path}")


def _execute_cal_event_get(
    client: NextcloudCalendarClient, calendar_name_or_path: str, event_href: str
) -> None:
    if not (
        event_content := client.get_event(
            get_calendar_path(client, calendar_name_or_path), event_href
        )
    ):
        print("Event not found")
        sys.exit(1)
    print(event_content)


def _execute_cal_event_create(
    client: NextcloudCalendarClient,
    calendar_name_or_path: str,
    args: argparse.Namespace,
) -> None:
    if not (
        event_href := client.create_event_from_params(
            get_calendar_path(client, calendar_name_or_path),
            args.summary,
            args.start,
            args.end,
            args.description,
            args.location,
        )
    ):
        print("Event creation failed")
        sys.exit(1)
    print(f"Event created: {event_href}")


def _execute_cal_event_update(
    client: NextcloudCalendarClient,
    calendar_name_or_path: str,
    args: argparse.Namespace,
) -> None:
    if not client.update_event_from_params(
        get_calendar_path(client, calendar_name_or_path),
        args.event,
        args.summary,
        args.start,
        args.end,
        args.description,
        args.location,
    ):
        print("Event update failed")
        sys.exit(1)
    print(f"Event updated: {args.event}")


def _execute_cal_event_delete(
    client: NextcloudCalendarClient, calendar_name_or_path: str, event_href: str
) -> None:
    if not client.delete_event(
        get_calendar_path(client, calendar_name_or_path), event_href
    ):
        print("Event deletion failed")
        sys.exit(1)
    print(f"Event deleted: {event_href}")


if __name__ == "__main__":
    main()
