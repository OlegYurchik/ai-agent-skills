# Python Skills Repository

Repository of skills for AI agents, written in Python without external dependencies.

## Features

- **Pure Python** — only standard Python libraries are used
- **Independent modules** — each skill is a self-contained module
- **CLI interface** — all skills are accessible via command line
- **Documented** — each skill has its own documentation

## Available Skills

### [`email/`](email/) — Email Management

Skill for interacting with email servers via IMAP and SMTP protocols.

**Capabilities:**
- Receive emails via IMAP
- Search messages by keywords
- Delete messages
- Send emails via SMTP

**File:** [`email/skill.py`](email/skill.py)

**Documentation:** [`email/SKILL.md`](email/SKILL.md)

---

### [`nextcloud/`](nextcloud/) — Nextcloud Management

Skill for interacting with Nextcloud via WebDAV, CalDAV, and CardDAV APIs.

**Capabilities:**
- File management (WebDAV): upload, download, delete, create directories
- Calendar management (CalDAV): create, edit, delete events
- Contact management (CardDAV): search, create, edit, delete contacts

**File:** [`nextcloud/skill.py`](nextcloud/skill.py)

**Documentation:** [`nextcloud/SKILL.md`](nextcloud/SKILL.md)

---

## Usage

Each skill is a separate Python file that can be run directly:

```bash
# Example for email skill
python3 email/skill.py --help

# Example for nextcloud skill
python3 nextcloud/skill.py --help
```

## Project Structure

```
ai-agent-skills/
├── email/              # Email skill
│   ├── skill.py        # Main module
│   ├── SKILL.md        # Documentation
│   └── .env.example    # Environment variables example
├── nextcloud/          # Nextcloud skill
│   ├── skill.py        # Main module
│   ├── SKILL.md        # Documentation
│   └── .env.example    # Environment variables example
└── README.md
```

## Requirements

- Python 3.11+

## License

MIT
