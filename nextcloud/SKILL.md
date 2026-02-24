---
name: nextcloud
description: Work with Nextcloud through WebDAV, CalDAV, and CardDAV protocols
version: 1.0.0
author: Oleg Yurchik <oleg@yurchik.space>
permissions: Requires network access to connect to Nextcloud server and file system access for local file operations
---

# Nextcloud CLI Client Skill

## Overview

This skill provides automation capabilities for managing files, calendars, and contacts on a Nextcloud server through the command line. It's designed to handle user requests that involve Nextcloud operations.

## When to use this skill

Use this skill when the user asks for:

| User Request | Command to use |
|--------------|----------------|
| "List files in folder X" | `python nextcloud/skill.py file-list /path/to/dir` |
| "Upload file X to server" | `python nextcloud/skill.py file-upload local.txt /remote.txt` |
| "Download file X from server" | `python nextcloud/skill.py file-download /remote.txt local.txt` |
| "Delete file X from server" | `python nextcloud/skill.py file-delete /path/to/file` |
| "Create folder X" | `python nextcloud/skill.py file-mkdir /path/to/dir` |
| "Show my calendars" | `python nextcloud/skill.py cal-list` |
| "Create calendar X" | `python nextcloud/skill.py cal-create mycalendar` |
| "Show events in calendar X" | `python nextcloud/skill.py cal-events mycalendar 2024-01-01 2024-12-31` |
| "Create event in calendar" | `python nextcloud/skill.py cal-event-create ...` |
| "Show my contacts" | `python nextcloud/skill.py card-list` |
| "Find contact X" | `python nextcloud/skill.py card-search query` |
| "Create contact" | `python nextcloud/skill.py card-create --first-name X --last-name Y` |

## Quick Start

To see all available commands and options, run:

```bash
python nextcloud/skill.py --help
```

For help on a specific command:

```bash
python nextcloud/skill.py file-list --help
python nextcloud/skill.py file-upload --help
python nextcloud/skill.py cal-list --help
python nextcloud/skill.py card-list --help
```

## Authentication

The skill supports two ways to pass credentials:

### Via command-line arguments
```bash
--url <URL>       # Nextcloud server URL (e.g., https://nextcloud.example.com)
--user <USERNAME> # Username
--pass <PASSWORD> # Password
--timeout <SEC>   # Request timeout (default: 30)
--verbose, -v     # Enable verbose output
```

### Via environment variables
```bash
NEXTCLOUD_URL      # Nextcloud server URL
NEXTCLOUD_USER     # Username
NEXTCLOUD_PASSWORD # Password
```

**Priority**: command-line arguments override environment variables.

## Core Commands

### File Management (WebDAV)
```bash
python nextcloud/skill.py file-list [OPTIONS] [PATH]
python nextcloud/skill.py file-upload [OPTIONS] LOCAL_PATH REMOTE_PATH
python nextcloud/skill.py file-download [OPTIONS] REMOTE_PATH LOCAL_PATH
python nextcloud/skill.py file-delete [OPTIONS] PATH
python nextcloud/skill.py file-mkdir [OPTIONS] PATH
```

### Calendar Management (CalDAV)
```bash
python nextcloud/skill.py cal-list [OPTIONS]
python nextcloud/skill.py cal-create [OPTIONS] NAME
python nextcloud/skill.py cal-events [OPTIONS] CALENDAR START_DATE [END_DATE]
python nextcloud/skill.py cal-event-get [OPTIONS] CALENDAR EVENT_HREF
python nextcloud/skill.py cal-event-create [OPTIONS] CALENDAR SUMMARY DTSTART DTEND
python nextcloud/skill.py cal-event-update [OPTIONS] CALENDAR EVENT_HREF
python nextcloud/skill.py cal-event-delete [OPTIONS] CALENDAR EVENT_HREF
```

### Contacts Management (CardDAV)
```bash
python nextcloud/skill.py card-list [OPTIONS]
python nextcloud/skill.py card-search [OPTIONS] QUERY
python nextcloud/skill.py card-get [OPTIONS] CARD_NAME_OR_PATH
python nextcloud/skill.py card-create [OPTIONS]
python nextcloud/skill.py card-update [OPTIONS] CARD_NAME_OR_PATH
python nextcloud/skill.py card-delete [OPTIONS] CARD_NAME_OR_PATH
```

## Examples

### List files in a directory
```bash
python nextcloud/skill.py file-list /path/to/dir
python nextcloud/skill.py file-list --depth infinity
```

### Upload a file
```bash
python nextcloud/skill.py file-upload local.txt /remote.txt
```

### List calendars
```bash
python nextcloud/skill.py cal-list
```

### Create an event
```bash
python nextcloud/skill.py cal-event-create mycalendar "Meeting Title" 2024-06-01T10:00:00+03:00 2024-06-01T11:00:00+03:00 --description "Team meeting" --location "Room 101"
```

### List contacts
```bash
python nextcloud/skill.py card-list
```

### Search contacts
```bash
python nextcloud/skill.py card-search query
```

## Dependencies

- Python 3.x (standard library only)
- Modules: `argparse`, `base64`, `datetime`, `logging`, `os`, `re`, `sys`, `uuid`, `urllib`, `xml.etree.ElementTree`

## Notes

- Calendar and contact names can be specified (auto-resolved) or full paths
- Events and contacts are identified by their href/UID
- Contact search performs client-side filtering (Nextcloud doesn't support CardDAV REPORT for search)
- **Datetime format**: All datetime parameters must include timezone information in ISO 8601 format (e.g., `2024-06-01T10:00:00+03:00` or `2024-06-01T10:00:00Z`). Date-only format (YYYY-MM-DD) is supported for all-day events.
