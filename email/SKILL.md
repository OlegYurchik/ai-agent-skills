---
name: email
description: Work with email through IMAP and SMTP protocols
version: 1.0.0
author: Oleg Yurchik <oleg@yurchik.space>
permissions: Requires network access to connect to IMAP/SMTP servers for sending and receiving emails
---

# Email CLI Client Skill

## Overview

This skill provides email automation capabilities through the command line. It's designed to handle user requests that involve email operations.

## When to use this skill

Use this skill when the user asks for:

| User Request | Command to use |
|--------------|----------------|
| "Find email from X" | `python email/skill.py search --term "X"` |
| "Show latest emails from inbox" | `python email/skill.py get` |
| "Check incoming emails" | `python email/skill.py get --search "UNSEEN"` |
| "Delete spam from inbox" | `python email/skill.py delete --id <ID>` |
| "Send email to X@example.com" | `python email/skill.py send --to X@example.com` |
| "Send report via email" | `python email/skill.py send --to admin@example.com --subject "Report"` |
| "Find emails with attachments" | `python email/skill.py search --term "has:attachment"` |
| "Check emails from Sent folder" | `python email/skill.py get --folder "Sent"` |

## Quick Start

To see all available commands and options, run:

```bash
python email/skill.py --help
```

For help on a specific command:

```bash
python email/skill.py get --help
python email/skill.py send --help
python email/skill.py search --help
python email/skill.py delete --help
```

## Authentication

The skill supports two ways to pass credentials:

### Via command-line arguments
```bash
--host <HOST>       # IMAP/SMTP server (e.g., imap.gmail.com)
--port <PORT>       # Server port
--user <USERNAME>   # Username
--password <PASS>   # Password
```

### Via environment variables
```bash
IMAP_HOST, IMAP_PORT, IMAP_USER, IMAP_PASSWORD
SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
```

**Priority**: command-line arguments override environment variables.

## Core Commands

### Get Emails
```bash
python email/skill.py get [OPTIONS]
```
Retrieves emails from the mailbox. Supports filtering by folder, IMAP criteria, and message limit.

### Search Emails
```bash
python email/skill.py search [OPTIONS] --term <QUERY>
```
Searches emails by keyword in headers and message body.

### Delete Emails
```bash
python email/skill.py delete [OPTIONS] --id <MESSAGE_ID>
```
Deletes an email by its identifier. Messages are marked as deleted and removed during expunge.

### Send Emails
```bash
python email/skill.py send [OPTIONS] --to <ADDRESS> --subject <SUBJECT> --body <BODY>
```
Sends email via SMTP. Supports HTML format.

## Examples

### Get last 5 unread emails
```bash
python email/skill.py get --search "UNSEEN" --limit 5
```

### Send error notification
```bash
python email/skill.py send \
  --to admin@example.com \
  --subject "Script Error" \
  --body "An error occurred during task execution"
```

### Search emails with attachments
```bash
python email/skill.py search --term "has:attachment"
```

## Supported IMAP Servers

| Provider | IMAP Host | Port | SSL |
|----------|-----------|------|-----|
| Gmail | imap.gmail.com | 993 | Yes |
| Outlook | outlook.office365.com | 993 | Yes |
| Yahoo | imap.mail.yahoo.com | 993 | Yes |
| Yandex | imap.yandex.com | 993 | Yes |

## Supported SMTP Servers

| Provider | SMTP Host | Port | SSL/TLS |
|----------|-----------|------|---------|
| Gmail | smtp.gmail.com | 465 | SSL |
| Outlook | smtp.office365.com | 587 | TLS |
| Yahoo | smtp.mail.yahoo.com | 465 | SSL |
| Yandex | smtp.yandex.com | 465 | SSL |

## Dependencies

- Python 3.x (standard library only)
- Modules: `argparse`, `email`, `imaplib`, `os`, `smtplib`, `sys`

## Notes

- Email bodies are decoded from headers or UTF-8 as fallback
- MIME multipart emails extract plain text parts
- IMAP search uses `TEXT` criterion for keyword search
- Deleted emails are marked with `\Deleted` flag and removed during expunge
- SMTP sends emails with proper MIME headers (plain or HTML)
