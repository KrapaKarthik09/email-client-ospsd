"""Utility module for fetching emails from various sources.

This module provides a mechanism to fetch emails from external sources
and add them to the local email client.
"""

import imaplib
import email
import email.message
import email.header
import email.utils
import uuid
import datetime
from typing import List, Dict, Any, Tuple, Optional
import os
import ssl
import json
import time

from ._impl import ClientImpl, MessageImpl, AttachmentImpl


class IMAPFetcher:
    """Class for fetching emails from an IMAP server."""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 993,
        use_ssl: bool = True,
    ) -> None:
        """Initialize the IMAP fetcher with server details."""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.client = None
        self._connect()

    def _connect(self) -> None:
        """Connect to the IMAP server."""
        if self.use_ssl:
            self.connection = imaplib.IMAP4_SSL(self.host, self.port)
        else:
            # Use type ignore to handle the type inconsistency
            self.connection = imaplib.IMAP4(self.host, self.port)  # type: ignore

        # Login
        self.connection.login(self.username, self.password)

    def set_client(self, client: ClientImpl) -> None:
        """Set the email client to use for storing fetched messages."""
        self.client = client

    def list_folders(self) -> List[str]:
        """List available folders on the server."""
        result, data = self.connection.list()
        if result != "OK":
            raise RuntimeError(f"Failed to list folders: {result}")

        folders = []
        for item in data:
            # Parse folder name from response
            parts = item.decode().split('"')
            if len(parts) >= 3:
                folders.append(parts[2].strip())

        return folders

    def fetch_messages(
        self, folder: str = "INBOX", limit: int = 10
    ) -> List[MessageImpl]:
        """Fetch messages from the specified folder."""
        if self.client is None:
            raise ValueError("No client has been set")

        # Select the folder
        result, _ = self.connection.select(folder)
        if result != "OK":
            raise RuntimeError(f"Failed to select folder '{folder}': {result}")

        # Search for all messages
        result, data = self.connection.search(None, "ALL")
        if result != "OK":
            raise RuntimeError(f"Failed to search messages: {result}")

        message_ids = data[0].split()
        # Take only the most recent 'limit' messages
        message_ids = message_ids[-limit:]

        fetched_messages = []

        for msg_id in message_ids:
            result, data = self.connection.fetch(msg_id, "(RFC822)")
            if result != "OK":
                print(f"Failed to fetch message {msg_id}: {result}")
                continue

            email_data = data[0][1]
            email_message = email.message_from_bytes(email_data)

            # Parse message
            message = self._parse_message(email_message)

            # Add to client
            try:
                self.client.add_message(message, folder)
                fetched_messages.append(message)
            except Exception as e:
                print(f"Error adding message to client: {e}")

        return fetched_messages

    def _parse_message(self, email_message) -> MessageImpl:
        """Parse an email.message.Message object into a MessageImpl."""
        # Extract header information
        message_id = email_message.get("Message-ID", str(uuid.uuid4()))
        if not message_id:
            message_id = str(uuid.uuid4())

        # Remove angle brackets if present
        message_id = message_id.strip("<>")

        # Get and decode subject
        subject = self._decode_header(email_message.get("Subject", "No Subject"))

        # Get sender
        from_header = email_message.get("From", "Unknown")
        from_ = self._decode_header(from_header)

        # Get recipients
        to_header = email_message.get("To", "")
        to = self._decode_header(to_header)

        cc_header = email_message.get("Cc", None)
        cc = self._decode_header(cc_header) if cc_header else None

        bcc_header = email_message.get("Bcc", None)
        bcc = self._decode_header(bcc_header) if bcc_header else None

        # Get date
        date_header = email_message.get("Date", None)
        date = date_header

        # Extract body and attachments
        body, attachments = self._extract_content(email_message)

        # Create and return a MessageImpl object
        # In _parse_message and other places where MessageImpl is created
        message = MessageImpl(
            _id=message_id,  # Changed from message_id
            _from=from_,  # Changed from from_
            _to=to,  # Changed from to
            _cc=cc,  # Changed from cc
            _bcc=bcc,  # Changed from bcc
            _date=date,  # Changed from date
            _subject=subject,  # Changed from subject
            _body=body,  # Changed from body
            _attachments=attachments,  # Changed from attachments
            _is_read=False,  # Changed from is_read
        )
        return message

    def _decode_header(self, header: str) -> str:
        """Decode email header string."""
        if not header:
            return ""

        decoded_header = ""
        for part, encoding in email.header.decode_header(header):
            if isinstance(part, bytes):
                if encoding:
                    # To:
                    try:
                        decoded_part = part.decode(encoding)
                    except (UnicodeDecodeError, LookupError):
                        decoded_part = part.decode("utf-8", errors="replace")
                else:
                    decoded_part = part.decode("utf-8", errors="replace")
            else:
                decoded_part = part

            decoded_header += decoded_part

        return decoded_header

    def _extract_content(self, email_message) -> Tuple[str, List[AttachmentImpl]]:
        """Extract body and attachments from an email message."""
        body = ""
        attachments = []

        # Handle multipart messages
        if email_message.is_multipart():
            for part in email_message.walk():
                # Skip container multipart parts
                if part.get_content_maintype() == "multipart":
                    continue

                content_type = part.get_content_type()
                content_disposition = part.get("Content-Disposition", "")

                # Handle attachments
                if "attachment" in content_disposition or content_type not in [
                    "text/plain",
                    "text/html",
                ]:
                    filename = part.get_filename()
                    if not filename:
                        filename = f"attachment_{len(attachments)}"

                    content = part.get_payload(decode=True)
                    attachment = AttachmentImpl(
                        filename=filename, content_type=content_type, content=content
                    )
                    attachments.append(attachment)

                # Handle body content
                elif content_type == "text/plain":
                    try:
                        charset = part.get_content_charset() or "utf-8"
                        payload = part.get_payload(decode=True)
                        decoded_text = payload.decode(charset, errors="replace")
                        body += decoded_text
                    except Exception as e:
                        print(f"Error decoding text/plain part: {e}")

                # Fallback to HTML if no plain text
                elif content_type == "text/html" and not body:
                    try:
                        charset = part.get_content_charset() or "utf-8"
                        payload = part.get_payload(decode=True)
                        decoded_text = payload.decode(charset, errors="replace")
                        body += f"[HTML Content]\n{decoded_text}"
                    except Exception as e:
                        print(f"Error decoding text/html part: {e}")

        # Handle non-multipart messages
        else:
            # Get content type and charset
            content_type = email_message.get_content_type()
            charset = email_message.get_content_charset() or "utf-8"

            # Get and decode payload
            try:
                payload = email_message.get_payload(decode=True)
                if payload:
                    body = payload.decode(charset, errors="replace")
            except Exception as e:
                print(f"Error decoding message body: {e}")
                body = "[Message body could not be decoded]"

        return body, attachments

    def close(self) -> None:
        """Close the connection to the IMAP server."""
        try:
            self.connection.close()
            self.connection.logout()
        except (imaplib.IMAP4.error, ConnectionError, OSError):
            pass


class MockFetcher:
    """Class for generating mock emails for testing purposes."""

    def __init__(self) -> None:
        """Initialize the mock fetcher."""
        self.client = None

    def set_client(self, client: ClientImpl) -> None:
        """Set the email client to use for storing fetched messages."""
        self.client = client

    def fetch_messages(
        self, folder: str = "INBOX", count: int = 5
    ) -> List[MessageImpl]:
        """Generate mock messages and add them to the client."""
        if self.client is None:
            raise ValueError("No client has been set")

        # Create mock messages
        mock_messages = self._generate_mock_messages(count)

        # Add to client
        for message in mock_messages:
            try:
                self.client.add_message(message, folder)
            except Exception as e:
                print(f"Error adding message to client: {e}")

        return mock_messages

    def _generate_mock_messages(self, count: int) -> List[MessageImpl]:
        """Generate a list of mock messages."""
        messages = []

        for i in range(count):
            # Create a unique ID
            message_id = str(uuid.uuid4())

            # Set the date (recent messages, with some variation)
            date_offset = i * 3600  # hours in seconds
            date = datetime.datetime.now() - datetime.timedelta(seconds=date_offset)
            date_str = date.strftime("%a, %d %b %Y %H:%M:%S +0000")

            # Create message with varying content
            subject = f"Test Message {i+1}"
            from_ = "sender@example.com"
            to = "recipient@example.com"

            # Vary the message content
            if i % 3 == 0:
                body = f"This is test message {i+1} with some important content to test search functionality."
                subject = f"Important: {subject}"
            elif i % 3 == 1:
                body = f"Newsletter {i+1}: Updates and information about our latest developments."
                subject = f"Newsletter: {subject}"
            else:
                body = f"This is a regular message {i+1} with nothing particularly special about it."

            # Create attachments for some messages
            attachments = []
            if i % 2 == 0:
                # Create a simple text attachment
                text_content = f"This is the content of attachment {i+1}".encode(
                    "utf-8"
                )
                attachment = AttachmentImpl(
                    filename=f"attachment_{i+1}.txt",
                    content_type="text/plain",
                    content=text_content,
                )
                attachments.append(attachment)

            message = MessageImpl(
                _id=message_id,
                _from=from_,
                _to=to,
                _cc="cc@example.com" if i % 2 == 0 else None,
                _bcc="bcc@example.com" if i % 3 == 0 else None,
                _date=date_str,
                _subject=subject,
                _body=body,
                _attachments=attachments,
                _is_read=False,
            )

            messages.append(message)

        return messages


def import_emails_from_json(
    filename: str, client: ClientImpl, folder: str = "INBOX"
) -> List[MessageImpl]:
    """Import emails from a JSON file into the client."""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")

    imported_messages = []

    with open(filename, "r") as f:
        data = json.load(f)

        for message_data in data:
            try:
                attachments = []

                # Process attachments if any
                for att_data in message_data.get("attachments", []):
                    attachment = AttachmentImpl(
                        filename=att_data["filename"],
                        content_type=att_data["content_type"],
                        content=bytes.fromhex(att_data["content"])
                        if isinstance(att_data["content"], str)
                        else bytes(att_data["content"]),
                    )
                    attachments.append(attachment)

                # Create message
                message = MessageImpl(
                    _id=message_data.get("id", str(uuid.uuid4())),
                    _from=message_data["from"],
                    _to=message_data["to"],
                    _cc=message_data.get("cc"),
                    _bcc=message_data.get("bcc"),
                    _date=message_data.get(
                        "date",
                        datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000"),
                    ),
                    _subject=message_data["subject"],
                    _body=message_data["body"],
                    _attachments=attachments,
                    _is_read=message_data.get("is_read", False),
                )

                # Add to client
                client.add_message(message, folder)
                imported_messages.append(message)

            except Exception as e:
                print(f"Error importing message: {e}")

    return imported_messages
