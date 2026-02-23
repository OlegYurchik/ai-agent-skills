# Nextcloud Skill

Skill for working with Nextcloud servers via WebDAV, CalDAV, and CardDAV protocols.

## Features

- **File Management** — list, upload, download, delete files and directories
- **Calendar Management** — list calendars, create events, update/delete events
- **Contacts Management** — list, search, create, update, delete contacts

## Installation

No external dependencies required — uses only Python standard library.

## Usage

### File Operations

#### List Files

```bash
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password file-list
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password file-list /path/to/dir
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password file-list --depth infinity
```

#### Upload File

```bash
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password file-upload local.txt /remote.txt
```

#### Download File

```bash
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password file-download /remote.txt local.txt
```

#### Delete File

```bash
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password file-delete /path/to/file
```

#### Create Directory

```bash
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password file-mkdir /path/to/dir
```

### Calendar Operations

#### List Calendars

```bash
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password cal-list
```

#### Create Calendar

```bash
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password cal-create mycalendar
```

#### Delete Calendar

```bash
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password cal-delete mycalendar
```

#### List Events in Date Range

```bash
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password cal-events mycalendar 2024-01-01 2024-12-31
```

#### Get Event

```bash
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password cal-event-get mycalendar event.ics
```

#### Create Event

```bash
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password cal-event-create mycalendar "Meeting Title" 2024-06-01T10:00:00 2024-06-01T11:00:00 --description "Team meeting" --location "Room 101"
```

#### Update Event

```bash
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password cal-event-update mycalendar event.ics "Updated Title" 2024-06-01T10:00:00 2024-06-01T11:00:00 --description "Updated description"
```

#### Delete Event

```bash
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password cal-event-delete mycalendar event.ics
```

### Contact Operations

#### List Contacts

```bash
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password card-list
```

#### Search Contacts

```bash
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password card-search query
```

#### Get Contact

```bash
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password card-get contact.vcf
```

#### Create Contact

```bash
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password card-create --first-name John --last-name Doe --email john@example.com --phone +1234567890 --organization "Company" --note "Notes"
```

#### Update Contact

```bash
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password card-update contact.vcf --first-name Jane --last-name Doe --email jane@example.com
```

#### Delete Contact

```bash
python nextcloud/skill.py --url https://nextcloud.example.com --user admin --pass password card-delete contact.vcf
```

## Command Line Arguments

### Common Arguments

| Argument | Description |
|----------|-------------|
| `--url` | Nextcloud server URL (required) |
| `--user` | Username (required) |
| `--pass` | Password (required) |
| `--timeout` | Request timeout in seconds (default: 30) |
| `--verbose`, `-v` | Enable verbose output |

### File Arguments

| Argument | Description |
|----------|-------------|
| `path` | Path to file or directory |
| `local` | Local file path |
| `remote` | Remote file path |
| `--depth` | Depth for listing (default: 1, use "infinity" for recursive) |

### Calendar Arguments

| Argument | Description |
|----------|-------------|
| `calendar` | Calendar name or full path |
| `start` | Start date (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS) |
| `end` | End date (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS) |
| `event` | Event href/ID |
| `summary` | Event title |
| `start` | Event start datetime |
| `end` | Event end datetime |
| `--description`, `-d` | Event description |
| `--location`, `-l` | Event location |

### Contact Arguments

| Argument | Description |
|----------|-------------|
| `card` | Contact card href/name |
| `--first-name`, `-f` | First name |
| `--last-name`, `-l` | Last name |
| `--email`, `-e` | Email address |
| `--phone`, `-p` | Phone number |
| `--organization`, `-o` | Organization name |
| `--note`, `-n` | Notes |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `NEXTCLOUD_URL` | Nextcloud server URL |
| `NEXTCLOUD_USER` | Username |
| `NEXTCLOUD_PASSWORD` | Password |

**Priority**: CLI arguments > Environment variables

## API Endpoints Used

### Files (WebDAV)

- `PROPFIND /remote.php/dav/files/{user}/` - List files
- `PUT /remote.php/dav/files/{user}/` - Upload file
- `GET /remote.php/dav/files/{user}/` - Download file
- `DELETE /remote.php/dav/files/{user}/` - Delete file
- `MKCOL /remote.php/dav/files/{user}/` - Create directory

### Calendars (CalDAV)

- `PROPFIND /remote.php/dav/calendars/{user}/` - List calendars
- `REPORT /remote.php/dav/calendars/{user}/{calendar}/` - Query events
- `MKCOL /remote.php/dav/calendars/{user}/{name}/` - Create calendar
- `PUT /remote.php/dav/calendars/{user}/{calendar}/{event}.ics` - Create/update event
- `GET /remote.php/dav/calendars/{user}/{calendar}/{event}.ics` - Get event
- `DELETE /remote.php/dav/calendars/{user}/{calendar}/{event}.ics` - Delete event

### Contacts (CardDAV)

- `PROPFIND /remote.php/dav/addressbooks/users/{user}/contacts/` - List address books
- `GET /remote.php/dav/addressbooks/users/{user}/contacts/{card}.vcf` - Get contact
- `PUT /remote.php/dav/addressbooks/users/{user}/contacts/{card}.vcf` - Create/update contact
- `DELETE /remote.php/dav/addressbooks/users/{user}/contacts/{card}.vcf` - Delete contact

## Data Formats

### Event (iCalendar/VCALENDAR)

```
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Nextcloud CLI//EN
BEGIN:VEVENT
UID:{uuid}@nextcloud
DTSTAMP:{timestamp}
SUMMARY:{title}
DTSTART:{datetime}
DTEND:{datetime}
DESCRIPTION:{description}
LOCATION:{location}
END:VEVENT
END:VCALENDAR
```

### Contact (vCard/VCARD)

```
BEGIN:VCARD
VERSION:3.0
UID:{uuid}@nextcloud
PRODID:-//Nextcloud CLI//EN
FN:{full_name}
N:{last_name};{first_name};;;
NICKNAME:{nickname}
EMAIL:{email}
TEL:{phone}
ORG:{organization}
NOTE:{note}
END:VCARD
```

## Error Handling

The script handles the following errors:

- `HTTPRequestError` - HTTP errors (4xx, 5xx responses)
- `HTTPRequestStatusException` - Incorrect response status
- `NextcloudAuthError` - Authentication errors
- `NextcloudError` - General Nextcloud errors
- `FileNotFoundError` - Local file not found
- `ValueError` - Input validation errors

All errors result in exit code 1 with appropriate error messages logged to stderr.

## Notes

- Calendar and contact paths can be specified as names (auto-resolved) or full paths
- Events and contacts are identified by their href/UID
- Contact search performs client-side filtering (Nextcloud doesn't support CardDAV REPORT for search)
- All datetime parameters support both date-only (YYYY-MM-DD) and datetime (YYYY-MM-DDTHH:MM:SS) formats
