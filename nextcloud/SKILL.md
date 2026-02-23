---
name: nextcloud
description: Work with Nextcloud through WebDAV, CalDAV, and CardDAV protocols
version: 1.0.0
author: 
permissions: Requires network access to connect to Nextcloud server and file system access for local file operations
---

# Nextcloud CLI Client Skill

## Overview
This skill provides instructions for working with the Nextcloud CLI Client (`nextcloud/skill.py`) - a Python script for interacting with Nextcloud servers via WebDAV, CalDAV, and CardDAV APIs.

## File Location
- Main script: `nextcloud/skill.py`

## Core Functionality

### 1. File Management (WebDAV)
- `file-list` - List files and directories
- `file-upload` - Upload files to server
- `file-download` - Download files from server
- `file-delete` - Delete files or directories
- `file-mkdir` - Create directories

### 2. Calendar Management (CalDAV)
- `cal-list` - List all calendars
- `cal-create` - Create new calendar
- `cal-events` - List events in a date range
- `cal-event-get` - Get event content
- `cal-event-create` - Create event from parameters
- `cal-event-update` - Update existing event
- `cal-event-delete` - Delete event

### 3. Contacts Management (CardDAV)
- `card-list` - List all contacts
- `card-search` - Search contacts by query
- `card-get` - Get contact card content
- `card-create` - Create contact from parameters
- `card-update` - Update existing contact
- `card-delete` - Delete contact

## Authentication

### Command Line Arguments
```bash
--url <URL>       # Nextcloud server URL
--user <USERNAME> # Username
--pass <PASSWORD> # Password
--timeout <SEC>   # Request timeout (default: 30)
--verbose, -v     # Enable verbose output
```

### Environment Variables
```bash
NEXTCLOUD_URL      # Nextcloud server URL
NEXTCLOUD_USER     # Username
NEXTCLOUD_PASSWORD # Password
```

**Priority**: CLI arguments > Environment variables

## Usage Examples

### List Files
```bash
python skill.py --url https://nextcloud.example.com --user admin --pass password file-list
python skill.py --url https://nextcloud.example.com --user admin --pass password file-list /path/to/dir
python skill.py --url https://nextcloud.example.com --user admin --pass password file-list --depth infinity
```

### Upload/Download Files
```bash
python skill.py --url https://nextcloud.example.com --user admin --pass password file-upload local.txt /remote.txt
python skill.py --url https://nextcloud.example.com --user admin --pass password file-download /remote.txt local.txt
```

### Calendar Operations
```bash
# List calendars
python skill.py --url https://nextcloud.example.com --user admin --pass password cal-list

# Create calendar
python skill.py --url https://nextcloud.example.com --user admin --pass password cal-create mycalendar

# List events in date range
python skill.py --url https://nextcloud.example.com --user admin --pass password cal-events mycalendar 2024-01-01 2024-12-31

# Create event
python skill.py --url https://nextcloud.example.com --user admin --pass password cal-event-create mycalendar "Meeting Title" 2024-06-01T10:00:00 2024-06-01T11:00:00 --description "Team meeting" --location "Room 101"
```

### Contact Operations
```bash
# List contacts
python skill.py --url https://nextcloud.example.com --user admin --pass password card-list

# Search contacts
python skill.py --url https://nextcloud.example.com --user admin --pass password card-search query

# Create contact
python skill.py --url https://nextcloud.example.com --user admin --pass password card-create --first-name John --last-name Doe --email john@example.com --phone +1234567890

# Update contact
python skill.py --url https://nextcloud.example.com --user admin --pass password card-update contact.vcf --first-name Jane --last-name Doe
```

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

## Dependencies
- Python 3.x (standard library only - no external packages required)
- Uses: `argparse`, `base64`, `datetime`, `logging`, `os`, `re`, `sys`, `uuid`, `urllib`, `xml.etree.ElementTree`

## Notes
- Calendar and contact paths can be specified as names (auto-resolved) or full paths
- Events and contacts are identified by their href/UID
- Contact search performs client-side filtering (Nextcloud doesn't support CardDAV REPORT for search)
- All datetime parameters support both date-only (YYYY-MM-DD) and datetime (YYYY-MM-DDTHH:MM:SS) formats
