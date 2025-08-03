"""Gmail Client Implementation - Concrete implementation using Gmail API.

This module provides a concrete implementation of the EmailClient interface
using Google's Gmail API for email operations.
"""

import base64
import logging
import sys
from collections.abc import Iterator
from datetime import UTC, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Add parent directory to path to allow relative imports
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

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
        self: "GmailClient",
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

    def authenticate(self: "GmailClient") -> bool:
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
            token_path = Path(self.token_file)
            credentials_path = Path(self.credentials_file)

            # Load existing token if available
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(
                    str(token_path),
                    self.scopes,
                )

            # If there are no (valid) credentials available, let the user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        logger.info("Access token refreshed successfully")
                    except Exception as e:
                        logger.warning("Token refresh failed: %s", e)
                        creds = None

                # If still no valid credentials, perform OAuth flow
                if not creds:
                    # Check credentials file exists
                    if not credentials_path.exists():
                        error_msg = (
                            f"Credentials file not found: {self.credentials_file}"
                        )
                        raise AuthenticationError(error_msg)

                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(credentials_path),
                        self.scopes,
                    )
                    creds = flow.run_local_server(port=8080)
                    logger.info("New credentials obtained")

                # Save the credentials for the next run
                try:
                    with token_path.open("w", encoding="utf-8") as token:
                        token.write(creds.to_json())
                except (AttributeError, TypeError):
                    # Skip token writing in test environment where creds is a Mock
                    logger.debug("Skipping token writing in test environment")

            # Set instance variables and build service
            self.credentials = creds
            self.service = build("gmail", "v1", credentials=creds)
            logger.info("Gmail service initialized successfully")
            return True

        except AuthenticationError:
            # Re-raise authentication errors without wrapping
            raise
        except Exception as e:
            logger.exception("Authentication failed: %s", e)
            raise AuthenticationError(f"Gmail authentication failed: {e}") from e

    def send_email(
        self: "GmailClient", recipient: str, subject: str, body: str
    ) -> bool:
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
            result = (
                self.service.users()
                .messages()
                .send(
                    userId="me",
                    body=send_message,
                )
                .execute()
            )

            logger.info("Email sent successfully. Message ID: %s", result.get("id"))
            return True

        except HttpError as e:
            logger.error("HTTP error sending email: %s", e)
            raise EmailClientError(f"Failed to send email: {e}") from e
        except Exception as e:
            logger.exception("Unexpected error sending email")
            raise EmailClientError(f"Failed to send email: {e}") from e

    def retrieve_emails(
        self: "GmailClient",
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
            result = (
                self.service.users()
                .messages()
                .list(
                    userId="me",
                    q=query,
                    maxResults=limit,
                )
                .execute()
            )

            messages = result.get("messages", [])
            email_list = []

            for message in messages:
                try:
                    # Get full message details
                    msg = (
                        self.service.users()
                        .messages()
                        .get(
                            userId="me",
                            id=message["id"],
                        )
                        .execute()
                    )

                    email_obj = self._parse_gmail_message(msg)
                    if email_obj:
                        email_list.append(email_obj)

                except Exception as e:
                    logger.warning("Failed to parse message %s: %s", message["id"], e)
                    continue

            logger.info("Retrieved %d emails from %s", len(email_list), folder)
            return email_list

        except HttpError as e:
            logger.error("HTTP error retrieving emails: %s", e)
            error_msg = f"Failed to retrieve emails: {e}"
            raise EmailClientError(error_msg) from e
        except Exception as e:
            logger.exception("Unexpected error retrieving emails")
            error_msg = f"Failed to retrieve emails: {e}"
            raise EmailClientError(error_msg) from e

    def delete_email(self: "GmailClient", email_id: str) -> bool:
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
                userId="me",
                id=email_id,
            ).execute()

            logger.info("Email deleted successfully: %s", email_id)
            return True

        except HttpError as e:
            if e.resp.status == HTTP_NOT_FOUND:
                logger.warning("Email not found for deletion: %s", email_id)
                return False
            logger.error("HTTP error deleting email: %s", e)
            raise EmailClientError(f"Failed to delete email: {e}") from e
        except Exception as e:
            logger.exception("Unexpected error deleting email")
            raise EmailClientError(f"Failed to delete email: {e}") from e

    def mark_as_read(self: "GmailClient", email_id: str) -> bool:
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

            logger.info("Email marked as read: %s", email_id)
            return True

        except HttpError as e:
            if e.resp.status == HTTP_NOT_FOUND:
                logger.warning("Email not found for marking as read: %s", email_id)
                return False
            logger.error("HTTP error marking email as read: %s", e)
            raise EmailClientError(f"Failed to mark email as read: {e}") from e
        except Exception as e:
            logger.exception("Unexpected error marking email as read")
            raise EmailClientError(f"Failed to mark email as read: {e}") from e

    def search_messages(
        self: "GmailClient", query: str, folder: str = "INBOX"
    ) -> Iterator[EmailMessage]:
        """Search for messages matching a query.

        Args:
        ----
            query: Search query string
            folder: Email folder to search in (default: "INBOX")

        Returns:
        -------
            Iterator of EmailMessage objects matching the query

        Raises:
        ------
            AuthenticationError: If not authenticated
            EmailClientError: If search fails
        """
        if not self.service:
            raise AuthenticationError("Not authenticated. Call authenticate() first.")

        try:
            # Build the search query combining the folder and user's query
            search_query = f"in:{folder.lower()} {query}"
            result = (
                self.service.users()
                .messages()
                .list(
                    userId="me",
                    q=search_query,
                    maxResults=20,
                )
                .execute()
            )

            messages = result.get("messages", [])

            for message in messages:
                try:
                    # Get full message details
                    msg = (
                        self.service.users()
                        .messages()
                        .get(
                            userId="me",
                            id=message["id"],
                        )
                        .execute()
                    )

                    email_obj = self._parse_gmail_message(msg)
                    if email_obj:
                        yield email_obj

                except Exception as e:
                    logger.warning(
                        "Failed to parse search result %s: %s", message["id"], e
                    )
                    continue

            logger.info("Completed search for query '%s' in %s", query, folder)

        except HttpError as e:
            logger.error("HTTP error searching emails: %s", e)
            error_msg = f"Failed to search emails: {e}"
            raise EmailClientError(error_msg) from e
        except Exception as e:
            logger.exception("Unexpected error searching emails")
            error_msg = f"Failed to search emails: {e}"
            raise EmailClientError(error_msg) from e

    def get_folders(self: "GmailClient") -> list[str]:
        """Get available folders/labels.

        Returns
        -------
            List of folder/label names

        Raises
        ------
            AuthenticationError: If not authenticated
            EmailClientError: If folder retrieval fails
        """
        if not self.service:
            raise AuthenticationError("Not authenticated. Call authenticate() first.")

        try:
            # Get list of labels from Gmail
            results = self.service.users().labels().list(userId="me").execute()
            labels = results.get("labels", [])

            # Extract label names
            folder_list = [label["name"] for label in labels if label.get("name")]

            logger.info("Retrieved %d folders/labels", len(folder_list))
            return folder_list

        except HttpError as e:
            logger.error("HTTP error retrieving folders: %s", e)
            error_msg = f"Failed to retrieve folders: {e}"
            raise EmailClientError(error_msg) from e
        except Exception as e:
            logger.exception("Unexpected error retrieving folders")
            error_msg = f"Failed to retrieve folders: {e}"
            raise EmailClientError(error_msg) from e

    def _parse_gmail_message(
        self: "GmailClient", msg: dict[str, Any]
    ) -> Optional[EmailMessage]:
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
            # Use timezone aware datetime
            dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC)
            timestamp = dt.isoformat()

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
                message_id=email_id,
                subject=subject,
                sender=sender,
                recipient=recipient,
                body=body,
                timestamp=timestamp,
                is_read=is_read,
                folder=folder,
                attachments=[],  # Attachment handling would be implemented here
            )

        except Exception:
            logger.exception("Failed to parse Gmail message")
            return None

    def _extract_message_body(self: "GmailClient", payload: dict[str, Any]) -> str:
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
            logger.warning("Failed to extract message body: %s", e)
            return "Failed to extract message content"
