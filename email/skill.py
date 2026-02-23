#!/usr/bin/env python3
"""
Email skill module.

Supports:
- Receiving email via IMAP protocol
- Searching messages in email
- Deleting messages
- Sending messages via SMTP protocol
"""

import argparse
import email
import imaplib
import os
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header, make_header
from email.utils import parseaddr


def decode_mime_header(header_value):
    """Decode MIME header (e.g., email subject)."""
    if not header_value:
        return ""
    try:
        return str(make_header(decode_header(header_value)))
    except Exception:
        return header_value


def decode_email_body(payload, charset):
    """Decode email body."""
    if not payload:
        return ""
    try:
        if charset:
            return payload.decode(charset, errors="replace")
        return payload.decode("utf-8", errors="replace")
    except Exception:
        return payload.decode("utf-8", errors="replace")


def get_email_address(full_address):
    """Extract email address from string 'Name <email@example.com>'."""
    if not full_address:
        return ""
    try:
        return parseaddr(full_address)[1]
    except Exception:
        return full_address


class IMAPClient:
    """Client for working with IMAP server."""
    
    def __init__(self, host=None, port=None, username=None, password=None, use_ssl=False):
        """
        Initialize IMAPClient.
        
        Args:
            host: IMAP server (can be specified via IMAP_HOST environment variable)
            port: IMAP server port (default 993 for SSL, 143 for non-SSL)
            username: Username (email) (EMAIL_USER)
            password: Password (EMAIL_PASSWORD)
            use_ssl: Use SSL/TLS (default False, can be disabled via IMAP_USE_SSL)
        """
        self.host = host or os.environ.get("IMAP_HOST")
        self.port = port or os.environ.get("IMAP_PORT", 993 if use_ssl else 143)
        self.username = username or os.environ.get("EMAIL_USER")
        self.password = password or os.environ.get("EMAIL_PASSWORD")
        self.use_ssl = use_ssl or os.environ.get("IMAP_USE_SSL", False)
        
        # Check required parameters
        if not self.host:
            raise ValueError("IMAP host not specified. Specify via argument or IMAP_HOST environment variable")
        if not self.username:
            raise ValueError("Username not specified. Specify via argument or IMAP_USER environment variable")
        if not self.password:
            raise ValueError("Password not specified. Specify via argument or IMAP_PASSWORD environment variable")
        
        self.server = None
    
    def connect(self):
        """Connect to IMAP server."""
        try:
            if self.use_ssl:
                if self.port == 993:
                    self.server = imaplib.IMAP4_SSL(self.host, self.port)
                else:
                    self.server = imaplib.IMAP4(self.host, self.port)
                    self.server.starttls()
            else:
                self.server = imaplib.IMAP4(self.host, self.port)
            
            self.server.login(self.username, self.password)
            return self.server
        except Exception as e:
            raise ConnectionError(f"Error connecting to IMAP: {e}")
    
    def disconnect(self):
        """Disconnect from IMAP server."""
        if self.server:
            try:
                self.server.close()
                self.server.logout()
            except Exception:
                pass
            self.server = None
    
    def get_emails(self, folder="INBOX", search_criteria="ALL", limit=10):
        """
        Get list of messages from mailbox.
        
        Args:
            folder: Folder to read (default INBOX)
            search_criteria: Search criteria (default ALL - all emails)
            limit: Maximum number of emails to retrieve
        
        Returns:
            List of dictionaries with email data
        """
        if not self.server:
            self.connect()
        
        try:
            # Select folder
            status, _ = self.server.select(folder)
            if status != "OK":
                raise Exception(f"Failed to open folder {folder}")
            
            # Search messages
            status, data = self.server.search(None, search_criteria)
            if status != "OK":
                raise Exception("Error searching messages")
            
            # Get message IDs
            msg_ids = data[0].split()
            if not msg_ids:
                return []
            
            # Limit number of emails
            msg_ids = msg_ids[-limit:]
            
            emails = []
            for msg_id in msg_ids:
                status, msg_data = self.server.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue
                
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                
                # Extract headers
                subject = decode_mime_header(msg.get("Subject"))
                from_addr = decode_mime_header(msg.get("From"))
                to_addr = decode_mime_header(msg.get("To"))
                date = msg.get("Date", "")
                
                # Extract body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            charset = part.get_content_charset()
                            body = decode_email_body(part.get_payload(decode=True), charset)
                            break
                else:
                    charset = msg.get_content_charset()
                    body = decode_email_body(msg.get_payload(decode=True), charset)
                
                emails.append({
                    "id": msg_id.decode(),
                    "subject": subject,
                    "from": from_addr,
                    "from_email": get_email_address(from_addr),
                    "to": to_addr,
                    "date": date,
                    "body": body,
                    "raw": raw_email,
                })
            
            return emails
        finally:
            self.disconnect()
    
    def search_emails(self, search_term, folder="INBOX"):
        """
        Search messages by search query.
        
        Args:
            search_term: Search query
            folder: Folder to search in
        
        Returns:
            List of found emails
        """
        # Convert search query to IMAP-compatible format
        search_criteria = f'TEXT "{search_term}"'
        
        return self.get_emails(folder, search_criteria)
    
    def delete_email(self, msg_id, folder="INBOX"):
        """
        Delete message from mailbox.
        
        Args:
            msg_id: Message ID to delete
            folder: Folder containing the message
        
        Returns:
            True if deletion was successful
        """
        if not self.server:
            self.connect()
        
        try:
            # Select folder
            status, _ = self.server.select(folder)
            if status != "OK":
                raise Exception(f"Failed to open folder {folder}")
            
            # Mark message as deleted
            status, _ = self.server.store(msg_id, "+FLAGS", r"(\Deleted)")
            if status != "OK":
                raise Exception("Error marking message as deleted")
            
            # Physically delete marked messages
            status, _ = self.server.expunge()
            if status != "OK":
                raise Exception("Error physically deleting messages")
            
            return True
        finally:
            self.disconnect()


class SMTPClient:
    """Client for working with SMTP server."""
    
    def __init__(self, host=None, port=None, username=None, password=None, use_ssl=True, use_tls=True):
        """
        Initialize SMTPClient.
        
        Args:
            host: SMTP server (can be specified via SMTP_HOST environment variable)
            port: SMTP server port (default 465 for SSL, 587 for TLS)
            username: Username (email) (EMAIL_USER)
            password: Password (EMAIL_PASSWORD)
            use_ssl: Use SSL/TLS (default True, can be disabled via SMTP_USE_SSL)
            use_tls: Use STARTTLS (default True, can be disabled via SMTP_USE_TLS)
        """
        self.host = host or os.environ.get("SMTP_HOST")
        self.port = port or os.environ.get("SMTP_PORT", 465 if use_ssl else 587)
        self.username = username or os.environ.get("EMAIL_USER")
        self.password = password or os.environ.get("EMAIL_PASSWORD")
        self.use_ssl = use_ssl or os.environ.get("SMTP_USE_SSL")
        self.use_tls = use_tls or os.environ.get("SMTP_USE_TLS")
        
        if not self.host:
            raise ValueError("SMTP host not specified. Specify via argument or SMTP_HOST environment variable")
        if not self.username:
            raise ValueError("Username not specified. Specify via argument or SMTP_USER environment variable")
        if not self.password:
            raise ValueError("Password not specified. Specify via argument or SMTP_PASSWORD environment variable")
        
        self.server = None
    
    def connect(self):
        """Connect to SMTP server."""
        try:
            if self.use_ssl:
                self.server = smtplib.SMTP_SSL(self.host, self.port)
            else:
                self.server = smtplib.SMTP(self.host, self.port)
                if self.use_tls:
                    self.server.starttls()
            
            self.server.login(self.username, self.password)
            return self.server
        except Exception as e:
            raise ConnectionError(f"Error connecting to SMTP: {e}")
    
    def disconnect(self):
        """Disconnect from SMTP server."""
        if self.server:
            try:
                self.server.quit()
            except Exception:
                pass
            self.server = None
    
    def send_email(self, to_addr, subject, body, from_addr=None, html=False):
        """
        Send email.
        
        Args:
            to_addr: Recipient address
            subject: Email subject
            body: Email body
            from_addr: Sender address (default username)
            html: Send as HTML
        
        Returns:
            True if sending was successful
        """
        if not self.server:
            self.connect()
        
        if from_addr is None:
            from_addr = self.username
        
        try:
            # Create message
            if html:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = from_addr
                msg["To"] = to_addr
                
                part1 = MIMEText(body, "plain")
                part2 = MIMEText(body, "html")
                msg.attach(part1)
                msg.attach(part2)
            else:
                msg = MIMEText(body, "plain")
                msg["Subject"] = subject
                msg["From"] = from_addr
                msg["To"] = to_addr
            
            # Send email
            self.server.sendmail(from_addr, [to_addr], msg.as_string())
            return True
        finally:
            self.disconnect()


def print_emails(emails):
    """Pretty print list of emails."""
    if not emails:
        print("No emails found.")
        return
    
    for i, email_data in enumerate(emails, 1):
        print(f"\n{'=' * 60}")
        print(f"Email #{email_data['id']} (#{i})")
        print(f"{'=' * 60}")
        print(f"From: {email_data['from']}")
        print(f"To: {email_data['to']}")
        print(f"Date: {email_data['date']}")
        print(f"Subject: {email_data['subject']}")
        print(f"\nBody:")
        print("-" * 40)
        print(email_data['body'][:500] + "..." if len(email_data['body']) > 500 else email_data['body'])


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Email skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Usage examples:\n"
            "  # Get last 5 emails\n"
            "  python email/skill.py get --host imap.gmail.com --user example@gmail.com --password pass\n"
            "\n"
            "  # Search emails by keyword\n"
            "  python email/skill.py search --host imap.gmail.com --user example@gmail.com --password pass --term \"important\"\n"
            "\n"
            "  # Delete email\n"
            "  python email/skill.py delete --host imap.gmail.com --user example@gmail.com --password pass --id 123\n"
            "\n"
            "  # Send email\n"
            "  python email/skill.py send --host smtp.gmail.com --user example@gmail.com --password pass --to dest@example.com --subject \"Subject\" --body \"Text\"\n"
            "\n"
            "Environment variables:\n"
            "  IMAP_HOST, IMAP_PORT, IMAP_USER, IMAP_PASSWORD, IMAP_NO_SSL\n"
            "  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_NO_SSL, SMTP_NO_TLS"
        ),
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Command: get - get emails
    get_parser = subparsers.add_parser("get", help="Get emails from mailbox")
    get_parser.add_argument("--host", help="IMAP server (e.g., imap.gmail.com)")
    get_parser.add_argument("--port", type=int, default=None, help="IMAP server port (default 993)")
    get_parser.add_argument("--user", help="User email address")
    get_parser.add_argument("--password", help="Email password")
    get_parser.add_argument("--folder", default="INBOX", help="Folder to read (default INBOX)")
    get_parser.add_argument("--search", default="ALL", help="Search criteria (default ALL)")
    get_parser.add_argument("--limit", type=int, default=10, help="Maximum number of emails (default 10)")
    get_parser.add_argument("--no-ssl", action="store_true", help="Disable SSL")
    
    # Command: search - search emails
    search_parser = subparsers.add_parser("search", help="Search emails by query")
    search_parser.add_argument("--host", help="IMAP server")
    search_parser.add_argument("--port", type=int, default=None, help="IMAP server port")
    search_parser.add_argument("--user", help="User email address")
    search_parser.add_argument("--password", help="Email password")
    search_parser.add_argument("--term", required=True, help="Search query")
    search_parser.add_argument("--folder", default="INBOX", help="Folder to search in")
    search_parser.add_argument("--no-ssl", action="store_true", help="Disable SSL")
    
    # Command: delete - delete email
    delete_parser = subparsers.add_parser("delete", help="Delete email")
    delete_parser.add_argument("--host", help="IMAP server")
    delete_parser.add_argument("--port", type=int, default=None, help="IMAP server port")
    delete_parser.add_argument("--user", help="User email address")
    delete_parser.add_argument("--password", help="Email password")
    delete_parser.add_argument("--id", required=True, help="Message ID to delete")
    delete_parser.add_argument("--folder", default="INBOX", help="Folder containing the message")
    delete_parser.add_argument("--no-ssl", action="store_true", help="Disable SSL")
    
    # Command: send - send email
    send_parser = subparsers.add_parser("send", help="Send email")
    send_parser.add_argument("--host", help="SMTP server (e.g., smtp.gmail.com)")
    send_parser.add_argument("--port", type=int, default=None, help="SMTP server port (default 465)")
    send_parser.add_argument("--user", help="Sender email address")
    send_parser.add_argument("--password", help="Email password")
    send_parser.add_argument("--to", required=True, help="Recipient address")
    send_parser.add_argument("--subject", required=True, help="Email subject")
    send_parser.add_argument("--body", required=True, help="Email body")
    send_parser.add_argument("--from", dest="from_addr", help="Sender address (default --user)")
    send_parser.add_argument("--no-ssl", action="store_true", help="Disable SSL")
    send_parser.add_argument("--no-tls", action="store_true", help="Disable STARTTLS")
    send_parser.add_argument("--html", action="store_true", help="Send as HTML")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Handle SSL/TLS parameters
    use_ssl = True
    if hasattr(args, "no_ssl") and args.no_ssl:
        use_ssl = False
    
    use_tls = True
    if hasattr(args, "no_tls") and args.no_tls:
        use_tls = False
    
    if args.command in ("get", "search", "delete"):
        # Create IMAP client
        client = IMAPClient(
            host=args.host,
            port=args.port,
            username=args.user,
            password=args.password,
            use_ssl=use_ssl,
        )
        
        if args.command == "get":
            emails = client.get_emails(
                folder=args.folder,
                search_criteria=args.search,
                limit=args.limit,
            )
            print_emails(emails)
        
        elif args.command == "search":
            emails = client.search_emails(
                search_term=args.term,
                folder=args.folder,
            )
            print_emails(emails)
        
        elif args.command == "delete":
            success = client.delete_email(
                msg_id=args.id,
                folder=args.folder,
            )
            if success:
                print(f"Email #{args.id} successfully deleted.")
            else:
                print(f"Error deleting email #{args.id}.")
                sys.exit(1)
    
    elif args.command == "send":
        # Create SMTP client
        client = SMTPClient(
            host=args.host,
            port=args.port,
            username=args.user,
            password=args.password,
            use_ssl=use_ssl,
            use_tls=use_tls,
        )
        
        success = client.send_email(
            to_addr=args.to,
            subject=args.subject,
            body=args.body,
            from_addr=args.from_addr,
            html=args.html,
        )
        if success:
            print(f"Email successfully sent to {args.to}.")
        else:
            print("Error sending email.")
            sys.exit(1)
    

if __name__ == "__main__":
    main()
