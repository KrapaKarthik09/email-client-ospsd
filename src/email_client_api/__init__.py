"""Email Client API - Abstract interface for email client implementations.

This module defines the core interface that all email client implementations
must adhere to, promoting consistency and interchangeability between different
email service providers.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any, Optional, TypeVar

__version__ = "0.1.0"
__all__ = [
    "EmailClient",
    "EmailMessage",
    "AuthenticationError",
    "EmailClientError",
    "get_client",
]


class EmailClientError(Exception):
    """Base exception for email client operations."""


class AuthenticationError(EmailClientError):
    """Raised when authentication with email service fails."""


class Attachment:
    """Represents an email attachment."""

    def __init__(
        self: "Attachment",
        attachment_id: str,
        filename: str,
        content_type: str,
        size: int,
        content: Optional[bytes] = None,
    ) -> None:
        """Initialize an attachment.

        Args:
        ----
            attachment_id: Unique identifier for the attachment
            filename: Name of the attachment file
            content_type: MIME type of the attachment
            size: Size of the attachment in bytes
            content: The actual content of the attachment if loaded

        """
        self.attachment_id = attachment_id
        self.filename = filename
        self.content_type = content_type
        self.size = size
        self._content = content

    def get_content(self: "Attachment") -> bytes:
        """Get the attachment content.

        Returns
        -------
            Binary content of the attachment

        Raises
        ------
            EmailClientError: If content cannot be retrieved

        """
        if self._content:
            return self._content
        raise EmailClientError("Attachment content not loaded")


class EmailMessage:
    """Data class representing an email message."""

    def __init__(
        self: "EmailMessage",
        message_id: str,  # Renamed from 'id' to avoid shadowing builtin
        subject: str,
        sender: str,
        recipient: str,
        body: str,
        timestamp: str,
        *,  # Force keyword-only arguments to fix FBT001/FBT002
        is_read: bool = False,
        folder: str = "INBOX",
        attachments: Optional[list[dict[str, Any]]] = None,
    ) -> None:
        """Initialize an email message.

        Args:
        ----
            message_id: Unique email identifier
            subject: Email subject line
            sender: Sender email address
            recipient: Recipient email address
            body: Email body content
            timestamp: ISO format timestamp
            is_read: Whether the email has been read
            folder: Folder location of the email
            attachments: List of attachment metadata

        """
        self.id = message_id  # Keep 'id' as attribute name for backward compatibility
        self.subject = subject
        self.sender = sender
        self.recipient = recipient
        self.body = body
        self.timestamp = timestamp
        self.is_read = is_read
        self.folder = folder
        self.attachments = attachments or []

        # Add aliases to match README API
        self.from_ = sender

    def to_dict(self: "EmailMessage") -> dict[str, Any]:
        """Convert email message to dictionary format.

        Returns
        -------
            Dict containing email data

        """
        return {
            "id": self.id,
            "subject": self.subject,
            "sender": self.sender,
            "from_": self.sender,
            "recipient": self.recipient,
            "body": self.body,
            "timestamp": self.timestamp,
            "is_read": self.is_read,
            "folder": self.folder,
            "attachments": self.attachments,
        }


T = TypeVar("T", bound="EmailClient")


class EmailClient(ABC):
    """Abstract base class defining the email client interface.

    This interface defines the contract that all email client implementations
    must follow, ensuring consistency across different email service providers.
    """

    @abstractmethod
    def send_email(self: T, recipient: str, subject: str, body: str) -> bool:
        """Send an email to a recipient.

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
            AuthenticationError: If authentication with email service fails
            EmailClientError: If email sending fails for other reasons

        """

    @abstractmethod
    def retrieve_emails(
        self: T,
        folder: str = "INBOX",
        limit: int = 10,
    ) -> list[EmailMessage]:
        """Retrieve emails from a specified folder.

        Args:
        ----
            folder: Email folder to retrieve from (default: "INBOX")
            limit: Maximum number of emails to retrieve (default: 10)

        Returns:
        -------
            List[EmailMessage]: List of email message objects

        Raises:
        ------
            AuthenticationError: If authentication with email service fails
            EmailClientError: If email retrieval fails for other reasons

        """

    @abstractmethod
    def delete_email(self: T, email_id: str) -> bool:
        """Delete an email by its ID.

        Args:
        ----
            email_id: Unique identifier of the email to delete

        Returns:
        -------
            bool: True if email was deleted successfully, False otherwise

        Raises:
        ------
            AuthenticationError: If authentication with email service fails
            EmailClientError: If email deletion fails for other reasons

        """

    @abstractmethod
    def mark_as_read(self: T, email_id: str) -> bool:
        """Mark an email as read.

        Args:
        ----
            email_id: Unique identifier of the email to mark as read

        Returns:
        -------
            bool: True if email was marked as read successfully, False otherwise

        Raises:
        ------
            AuthenticationError: If authentication with email service fails
            EmailClientError: If marking email as read fails for other reasons

        """

    @abstractmethod
    def authenticate(self: T) -> bool:
        """Authenticate with the email service.

        Returns
        -------
            bool: True if authentication successful, False otherwise

        Raises
        ------
            AuthenticationError: If authentication fails

        """

    # Additional methods from README
    def get_messages(
        self: T, folder: str = "INBOX", limit: int = 10
    ) -> Iterator[EmailMessage]:
        """Get messages from a folder.

        Args:
        ----
            folder: Email folder to retrieve from (default: "INBOX")
            limit: Maximum number of emails to retrieve (default: 10)

        Returns:
        -------
            Iterator of EmailMessage objects

        Raises:
        ------
            AuthenticationError: If authentication with email service fails
            EmailClientError: If email retrieval fails

        """
        emails = self.retrieve_emails(folder=folder, limit=limit)
        yield from emails

    @abstractmethod
    def search_messages(
        self: T, query: str, folder: str = "INBOX"
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
            AuthenticationError: If authentication with email service fails
            EmailClientError: If search fails

        """

    @abstractmethod
    def get_folders(self: T) -> list[str]:
        """Get available folders/labels.

        Returns
        -------
            List of folder/label names

        Raises
        ------
            AuthenticationError: If authentication with email service fails
            EmailClientError: If folder retrieval fails

        """


def get_client(provider: str = "gmail", **kwargs: str) -> EmailClient:
    """Get an email client implementation.

    Args:
    ----
        provider: Email provider name (default: "gmail")
        **kwargs: Additional configuration parameters for the client

    Returns:
    -------
        An EmailClient implementation

    Raises:
    ------
        ValueError: If the provider is not supported

    """
    if provider.lower() == "gmail":
        # Import here to avoid circular imports
        from gmail_client_impl import GmailClient

        return GmailClient(**kwargs)
    raise ValueError(f"Email provider '{provider}' is not supported")
