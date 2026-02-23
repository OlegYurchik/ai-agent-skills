---
name: email
description: Work with email through IMAP and SMTP protocols
version: 1.0.0
author: 
permissions: Requires network access to connect to IMAP/SMTP servers for sending and receiving emails
---

# Email CLI Client Skill

## Overview
This skill provides instructions for working with the Email CLI Client (`email/skill.py`) - a Python script for interacting with email servers via IMAP and SMTP protocols.

## File Location
- Main script: `email/skill.py`

## Core Functionality

### 1. Receiving Emails (IMAP)
- `get` - Get emails from mailbox
- `search` - Search emails by keyword

### 2. Deleting Emails (IMAP)
- `delete` - Delete email from mailbox

### 3. Sending Emails (SMTP)
- `send` - Send email to recipient

## Authentication

### Command Line Arguments
```bash
# IMAP/SMTP Server
--host <HOST>       # IMAP/SMTP server (e.g., imap.gmail.com, smtp.gmail.com)
--port <PORT>       # Server port (default: 993 for IMAP SSL, 465 for SMTP SSL)
--user <USERNAME>   # Email username
--password <PASS>   # Email password

# IMAP-specific
--folder <FOLDER>   # Mailbox folder (default: INBOX)
--search <CRITERIA> # IMAP search criteria (default: ALL)
--limit <N>         # Maximum number of emails (default: 10)
--no-ssl            # Disable SSL

# SMTP-specific
--to <ADDRESS>      # Recipient email address
--subject <SUBJECT> # Email subject
--body <BODY>       # Email body
--from <ADDRESS>    # Sender address (default: --user)
--no-tls            # Disable STARTTLS
--html              # Send as HTML
```

### Environment Variables
```bash
# IMAP
IMAP_HOST       # IMAP server
IMAP_PORT       # IMAP port (default: 993)
IMAP_USER       # Email username
IMAP_PASSWORD   # Email password
IMAP_USE_SSL    # Use SSL (default: True)

# SMTP
SMTP_HOST       # SMTP server
SMTP_PORT       # SMTP port (default: 465)
SMTP_USER       # Email username
SMTP_PASSWORD   # Email password
SMTP_USE_SSL    # Use SSL (default: True)
SMTP_USE_TLS    # Use STARTTLS (default: True)
```

**Priority**: CLI arguments > Environment variables

## Usage Examples

### Get Emails from Mailbox
```bash
# Get last 5 emails from INBOX
python email/skill.py get --host imap.gmail.com --user example@gmail.com --password pass

# Get emails with specific search criteria
python email/skill.py get --host imap.gmail.com --user example@gmail.com --password pass --search "UNSEEN"

# Get emails from specific folder
python email/skill.py get --host imap.gmail.com --user example@gmail.com --password pass --folder "Sent"
```

### Search Emails
```bash
# Search emails by keyword
python email/skill.py search --host imap.gmail.com --user example@gmail.com --password pass --term "important"

# Search in specific folder
python email/skill.py search --host imap.gmail.com --user example@gmail.com --password pass --term "meeting" --folder "INBOX"
```

### Delete Email
```bash
# Delete email by message ID
python email/skill.py delete --host imap.gmail.com --user example@gmail.com --password pass --id 123

# Delete from specific folder
python email/skill.py delete --host imap.gmail.com --user example@gmail.com --password pass --id 456 --folder "Trash"
```

### Send Email
```bash
# Send plain text email
python email/skill.py send --host smtp.gmail.com --user example@gmail.com --password pass --to dest@example.com --subject "Subject" --body "Text"

# Send HTML email
python email/skill.py send --host smtp.gmail.com --user example@gmail.com --password pass --to dest@example.com --subject "Subject" --body "<h1>HTML</h1>" --html

# Send from different sender address
python email/skill.py send --host smtp.gmail.com --user example@gmail.com --password pass --to dest@example.com --subject "Subject" --body "Text" --from admin@example.com
```

## IMAP Commands

### get
Retrieve emails from mailbox.

**Arguments:**
- `--host` - IMAP server
- `--port` - IMAP port (default: 993)
- `--user` - Email username
- `--password` - Email password
- `--folder` - Folder to read (default: INBOX)
- `--search` - IMAP search criteria (default: ALL)
- `--limit` - Maximum number of emails (default: 10)
- `--no-ssl` - Disable SSL

### search
Search emails by text query.

**Arguments:**
- `--host` - IMAP server
- `--port` - IMAP port (default: 993)
- `--user` - Email username
- `--password` - Email password
- `--term` - Search query (required)
- `--folder` - Folder to search in (default: INBOX)
- `--no-ssl` - Disable SSL

### delete
Delete email from mailbox.

**Arguments:**
- `--host` - IMAP server
- `--port` - IMAP port (default: 993)
- `--user` - Email username
- `--password` - Email password
- `--id` - Message ID to delete (required)
- `--folder` - Folder containing the message (default: INBOX)
- `--no-ssl` - Disable SSL

## SMTP Commands

### send
Send email to recipient.

**Arguments:**
- `--host` - SMTP server
- `--port` - SMTP port (default: 465)
- `--user` - Email username
- `--password` - Email password
- `--to` - Recipient address (required)
- `--subject` - Email subject (required)
- `--body` - Email body (required)
- `--from` - Sender address (default: --user)
- `--no-ssl` - Disable SSL
- `--no-tls` - Disable STARTTLS
- `--html` - Send as HTML

## Output Format

### Email Display
```
============================================================
Email #123 (#1)
============================================================
From: John Doe <john@example.com>
To: Jane Doe <jane@example.com>
Date: Mon, 1 Jan 2024 10:00:00 +0000
Subject: Test Email

Body:
----------------------------------------
This is the email body.
```

## IMAP Server Examples

| Provider | IMAP Host | Port | SSL |
|----------|-----------|------|-----|
| Gmail | imap.gmail.com | 993 | Yes |
| Outlook | outlook.office365.com | 993 | Yes |
| Yahoo | imap.mail.yahoo.com | 993 | Yes |
| Yandex | imap.yandex.com | 993 | Yes |

## SMTP Server Examples

| Provider | SMTP Host | Port | SSL/TLS |
|----------|-----------|------|---------|
| Gmail | smtp.gmail.com | 465 | SSL |
| Outlook | smtp.office365.com | 587 | TLS |
| Yahoo | smtp.mail.yahoo.com | 465 | SSL |
| Yandex | smtp.yandex.com | 465 | SSL |

## Data Fields

### Email Object
```python
{
    "id": "123",              # Message ID
    "subject": "Subject",     # Decoded subject
    "from": "Name <email>",   # Decoded From header
    "from_email": "email",    # Extracted email address
    "to": "Name <email>",     # Decoded To header
    "date": "Mon, 1 Jan 2024", # Date header
    "body": "Email body",     # Decoded body text
    "raw": b"..."             # Raw email bytes
}
```

## Error Handling

The script handles the following errors:
- `ValueError` - Missing required parameters
- `ConnectionError` - IMAP/SMTP connection errors
- `Exception` - IMAP/SMTP protocol errors

All errors result in exit code 1 with appropriate error messages logged to stdout/stderr.

## Dependencies
- Python 3.x (standard library only - no external packages required)
- Uses: `argparse`, `email`, `imaplib`, `os`, `smtplib`, `sys`

## Notes
- Email bodies are decoded using charset from headers or UTF-8 as fallback
- MIME multipart emails extract plain text parts
- IMAP search uses `TEXT` criterion for keyword search
- Deleted emails are marked with `\Deleted` flag and expunged
- SMTP sends emails with proper MIME headers (plain or HTML)
