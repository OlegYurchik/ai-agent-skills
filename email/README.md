# Email Skill

Skill for working with email via IMAP and SMTP protocols.

## Features

- **Get emails** — retrieve emails from mailbox via IMAP
- **Search emails** — search messages by keyword
- **Delete emails** — delete messages from mailbox
- **Send emails** — send emails via SMTP

## Installation

No external dependencies required — uses only Python standard library.

## Usage

### Get Emails

```bash
python email/skill.py get --host imap.gmail.com --user example@gmail.com --password pass
```

### Search Emails

```bash
python email/skill.py search --host imap.gmail.com --user example@gmail.com --password pass --term "important"
```

### Delete Email

```bash
python email/skill.py delete --host imap.gmail.com --user example@gmail.com --password pass --id 123
```

### Send Email

```bash
python email/skill.py send --host smtp.gmail.com --user example@gmail.com --password pass --to dest@example.com --subject "Subject" --body "Text"
```

## Command Line Arguments

### Common Arguments

| Argument | Description |
|----------|-------------|
| `--host` | Server (IMAP/SMTP) |
| `--port` | Server port |
| `--user` | Username (email) |
| `--password` | Password |

### IMAP Arguments

| Argument | Description |
|----------|-------------|
| `--folder` | Folder to read (default: INBOX) |
| `--search` | IMAP search criteria (default: ALL) |
| `--limit` | Maximum number of emails (default: 10) |
| `--no-ssl` | Disable SSL |

### SMTP Arguments

| Argument | Description |
|----------|-------------|
| `--to` | Recipient address (required) |
| `--subject` | Email subject (required) |
| `--body` | Email body (required) |
| `--from` | Sender address (default: --user) |
| `--no-ssl` | Disable SSL |
| `--no-tls` | Disable STARTTLS |
| `--html` | Send as HTML |

## Environment Variables

### IMAP Variables

| Variable | Description |
|----------|-------------|
| `IMAP_HOST` | IMAP server |
| `IMAP_PORT` | IMAP port (default: 993) |
| `IMAP_USER` | Username |
| `IMAP_PASSWORD` | Password |
| `IMAP_USE_SSL` | Use SSL (default: True) |

### SMTP Variables

| Variable | Description |
|----------|-------------|
| `SMTP_HOST` | SMTP server |
| `SMTP_PORT` | SMTP port (default: 465) |
| `SMTP_USER` | Username |
| `SMTP_PASSWORD` | Password |
| `SMTP_USE_SSL` | Use SSL (default: True) |
| `SMTP_USE_TLS` | Use STARTTLS (default: True) |

**Priority**: CLI arguments > Environment variables

## Server Examples

### IMAP Servers

| Provider | Host | Port | SSL |
|----------|------|------|-----|
| Gmail | imap.gmail.com | 993 | Yes |
| Outlook | outlook.office365.com | 993 | Yes |
| Yahoo | imap.mail.yahoo.com | 993 | Yes |
| Yandex | imap.yandex.com | 993 | Yes |

### SMTP Servers

| Provider | Host | Port | SSL/TLS |
|----------|------|------|---------|
| Gmail | smtp.gmail.com | 465 | SSL |
| Outlook | smtp.office365.com | 587 | TLS |
| Yahoo | smtp.mail.yahoo.com | 465 | SSL |
| Yandex | smtp.yandex.com | 465 | SSL |

## Output Format

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

## Error Handling

- `ValueError` — missing required parameters
- `ConnectionError` — IMAP/SMTP connection errors
- `Exception` — IMAP/SMTP protocol errors

All errors result in exit code 1 with appropriate error messages.
