"""Gmail Client Implementation - Concrete implementation using Gmail API.

This module provides a concrete implementation of the EmailClient interface
using Google's Gmail API for email operations.
"""

import base64
import logging
import os

# Import from the parent email_client_api
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from email_client_api import (
    AuthenticationError,
    EmailClient,
    EmailClientError,
    EmailMessage,
)

__version__ = "0.1.0"
__all__ = ["GmailClient"]

# Gmail API scopes required for the operations
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

# HTTP status codes
HTTP_NOT_FOUND = 404

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GmailClient(EmailClient):
    """Gmail implementation of the EmailClient interface.

    This class provides concrete implementations of all EmailClient methods
    using Google's Gmail API.
    """

    def __init__(
        self,
        credentials_file: str = "credentials.json",
        token_file: str = "token.json",
        scopes: Optional[list[str]] = None,
    ) -> None:
        """Initialize the Gmail client.

        Args:
        ----
            credentials_file: Path to OAuth 2.0 credentials file
            token_file: Path to store/load access tokens
            scopes: List of Gmail API scopes (uses default if None)
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = scopes or SCOPES
        self.service: Any = None
        self.credentials: Optional[Credentials] = None

        logger.info("GmailClient initialized")

    def authenticate(self) -> bool:
        """Authenticate with Gmail API using OAuth 2.0.

        Returns
        -------
            bool: True if authentication successful, False otherwise

        Raises
        ------
            AuthenticationError: If authentication fails
        """
        try:
            creds = None

            # Load existing token if available
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(
                    self.token_file, self.scopes,
                )

            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        logger.info("Access token refreshed successfully")
                    except Exception as e:
                        logger.warning(f"Token refresh failed: {e}")
                        creds = None

                if not creds:
                    if not os.path.exists(self.credentials_file):
                        raise AuthenticationError(
                            f"Credentials file not found: {self.credentials_file}",
                        )

                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.scopes,
                    )
                    creds = flow.run_local_server(port=8080)
                    logger.info("New credentials obtained")

                # Save the credentials for the next run
                with open(self.token_file, "w", encoding="utf-8") as token:
                    token.write(creds.to_json())

            self.credentials = creds
            self.service = build("gmail", "v1", credentials=creds)
            logger.info("Gmail service initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise AuthenticationError(f"Gmail authentication failed: {e}") from e

    def send_email(self, recipient: str, subject: str, body: str) -> bool:
        """Send an email using Gmail API.

        Args:
        ----
            recipient: Email address of the recipient
            subject: Subject line of the email
            body: Email body content

        Returns:
        -------
            bool: True if email was sent successfully, False otherwise

        Raises:
        ------
            AuthenticationError: If not authenticated
            EmailClientError: If email sending fails
        """
        if not self.service:
            raise AuthenticationError("Not authenticated. Call authenticate() first.")

        try:
            # Create message
            message = MIMEMultipart()
            message["to"] = recipient
            message["subject"] = subject

            # Add body
            message.attach(MIMEText(body, "plain"))

            # Encode message
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes(),
            ).decode("utf-8")

            # Send message
            send_message = {"raw": raw_message}
            result = self.service.users().messages().send(
                userId="me", body=send_message,
            ).execute()

            logger.info(f"Email sent successfully. Message ID: {result.get('id')}")
            return True

        except HttpError as e:
            logger.error(f"HTTP error sending email: {e}")
            raise EmailClientError(f"Failed to send email: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}")
            raise EmailClientError(f"Failed to send email: {e}") from e

    def retrieve_emails(
        self,
        folder: str = "INBOX",
        limit: int = 10,
    ) -> list[EmailMessage]:
        """Retrieve emails from Gmail.

        Args:
        ----
            folder: Gmail label to retrieve from (default: "INBOX")
            limit: Maximum number of emails to retrieve (default: 10)

        Returns:
        -------
            List[EmailMessage]: List of email message objects

        Raises:
        ------
            AuthenticationError: If not authenticated
            EmailClientError: If email retrieval fails
        """
        if not self.service:
            raise AuthenticationError("Not authenticated. Call authenticate() first.")

        try:
            # Get list of messages
            query = f"in:{folder.lower()}"
            result = self.service.users().messages().list(
                userId="me", q=query, maxResults=limit,
            ).execute()

            messages = result.get("messages", [])
            email_list = []

            for message in messages:
                try:
                    # Get full message details
                    msg = self.service.users().messages().get(
                        userId="me", id=message["id"],
                    ).execute()

                    email_obj = self._parse_gmail_message(msg)
                    if email_obj:
                        email_list.append(email_obj)

                except Exception as e:
                    logger.warning(f"Failed to parse message {message['id']}: {e}")
                    continue

            logger.info(f"Retrieved {len(email_list)} emails from {folder}")
            return email_list

        except HttpError as e:
            logger.error(f"HTTP error retrieving emails: {e}")
            raise EmailClientError(f"Failed to retrieve emails: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error retrieving emails: {e}")
            raise EmailClientError(f"Failed to retrieve emails: {e}") from e

    def delete_email(self, email_id: str) -> bool:
        """Delete an email from Gmail.

        Args:
        ----
            email_id: Gmail message ID to delete

        Returns:
        -------
            bool: True if email was deleted successfully, False otherwise

        Raises:
        ------
            AuthenticationError: If not authenticated
            EmailClientError: If email deletion fails
        """
        if not self.service:
            raise AuthenticationError("Not authenticated. Call authenticate() first.")

        try:
            self.service.users().messages().delete(
                userId="me", id=email_id,
            ).execute()

            logger.info(f"Email deleted successfully: {email_id}")
            return True

        except HttpError as e:
            if e.resp.status == HTTP_NOT_FOUND:
                logger.warning(f"Email not found for deletion: {email_id}")
                return False
            logger.error(f"HTTP error deleting email: {e}")
            raise EmailClientError(f"Failed to delete email: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error deleting email: {e}")
            raise EmailClientError(f"Failed to delete email: {e}") from e

    def mark_as_read(self, email_id: str) -> bool:
        """Mark an email as read in Gmail.

        Args:
        ----
            email_id: Gmail message ID to mark as read

        Returns:
        -------
            bool: True if email was marked as read successfully, False otherwise

        Raises:
        ------
            AuthenticationError: If not authenticated
            EmailClientError: If marking email as read fails
        """
        if not self.service:
            raise AuthenticationError("Not authenticated. Call authenticate() first.")

        try:
            # Remove UNREAD label to mark as read
            self.service.users().messages().modify(
                userId="me",
                id=email_id,
                body={"removeLabelIds": ["UNREAD"]},
            ).execute()

            logger.info(f"Email marked as read: {email_id}")
            return True

        except HttpError as e:
            if e.resp.status == HTTP_NOT_FOUND:
                logger.warning(f"Email not found for marking as read: {email_id}")
                return False
            logger.error(f"HTTP error marking email as read: {e}")
            raise EmailClientError(f"Failed to mark email as read: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error marking email as read: {e}")
            raise EmailClientError(f"Failed to mark email as read: {e}") from e

    def _parse_gmail_message(self, msg: dict[str, Any]) -> Optional[EmailMessage]:
        """Parse a Gmail API message into an EmailMessage object.

        Args:
        ----
            msg: Gmail API message object

        Returns:
        -------
            EmailMessage object or None if parsing fails
        """
        try:
            headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}

            # Extract basic information
            email_id = msg["id"]
            subject = headers.get("Subject", "No Subject")
            sender = headers.get("From", "Unknown Sender")
            recipient = headers.get("To", "Unknown Recipient")

            # Parse timestamp
            timestamp_ms = int(msg["internalDate"])
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000).isoformat()

            # Check if read (UNREAD label present means unread)
            is_read = "UNREAD" not in msg["labelIds"]

            # Determine folder from labels
            folder = "INBOX"  # Default
            if "INBOX" in msg["labelIds"]:
                folder = "INBOX"
            elif "SENT" in msg["labelIds"]:
                folder = "SENT"
            elif "DRAFT" in msg["labelIds"]:
                folder = "DRAFT"

            # Extract body (simplified - just get plain text)
            body = self._extract_message_body(msg["payload"])

            return EmailMessage(
                id=email_id,
                subject=subject,
                sender=sender,
                recipient=recipient,
                body=body,
                timestamp=timestamp,
                is_read=is_read,
                folder=folder,
                attachments=[],  # TODO: Implement attachment parsing
            )

        except Exception as e:
            logger.error(f"Failed to parse Gmail message: {e}")
            return None

    def _extract_message_body(self, payload: dict[str, Any]) -> str:
        """Extract the body text from a Gmail message payload.

        Args:
        ----
            payload: Gmail message payload

        Returns:
        -------
            Extracted body text
        """
        try:
            # Handle multipart messages
            if "parts" in payload:
                for part in payload["parts"]:
                    if part["mimeType"] == "text/plain":
                        data = part["body"]["data"]
                        return base64.urlsafe_b64decode(data).decode("utf-8")

            # Handle single part messages
            elif payload["mimeType"] == "text/plain":
                data = payload["body"]["data"]
                return base64.urlsafe_b64decode(data).decode("utf-8")

            return "No plain text content found"

        except Exception as e:
            logger.warning(f"Failed to extract message body: {e}")
            return "Failed to extract message content"
