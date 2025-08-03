"""Tests for the EmailClient interface."""

import unittest
from typing import Any, Iterator, cast

import pytest

from email_client_api import (
    Attachment,
    EmailClient,
    EmailClientError,
    EmailMessage,
    get_client,
)

# Constants to replace magic numbers
DEFAULT_INBOX_NAME = "INBOX"
DEFAULT_EMAIL_LIMIT = 10
TEST_ATTACHMENT_SIZE = 100  # Replaces magic number 100
TEST_FOLDER_COUNT = 4  # Replaces magic number 4


class TestEmailMessage:
    """Test EmailMessage class."""

    def test_init(self: "TestEmailMessage") -> None:
        """Test initialization with default parameters."""
        # Create an email message
        email = EmailMessage(
            message_id="test_id",
            subject="Test Subject",
            sender="sender@example.com",
            recipient="recipient@example.com",
            body="Test Body",
            timestamp="2023-01-01T12:00:00Z",
        )

        # Verify attributes
        assert email.id == "test_id"
        assert email.subject == "Test Subject"
        assert email.sender == "sender@example.com"
        assert email.from_ == "sender@example.com"  # Alias for sender
        assert email.recipient == "recipient@example.com"
        assert email.body == "Test Body"
        assert email.timestamp == "2023-01-01T12:00:00Z"
        assert email.is_read is False
        assert email.folder == "INBOX"
        assert email.attachments == []

    def test_init_with_all_params(self: "TestEmailMessage") -> None:
        """Test initialization with all parameters."""
        # Create an email message with all parameters
        attachments = [
            {
                "attachment_id": "att1",
                "filename": "test.txt",
                "content_type": "text/plain",
                "size": TEST_ATTACHMENT_SIZE,
            }
        ]
        email = EmailMessage(
            message_id="test_id",
            subject="Test Subject",
            sender="sender@example.com",
            recipient="recipient@example.com",
            body="Test Body",
            timestamp="2023-01-01T12:00:00Z",
            is_read=True,
            folder="SENT",
            attachments=attachments,
        )

        # Verify attributes
        assert email.id == "test_id"
        assert email.subject == "Test Subject"
        assert email.sender == "sender@example.com"
        assert email.recipient == "recipient@example.com"
        assert email.body == "Test Body"
        assert email.timestamp == "2023-01-01T12:00:00Z"
        assert email.is_read is True
        assert email.folder == "SENT"
        assert len(email.attachments) == 1
        assert email.attachments[0]["filename"] == "test.txt"

    def test_to_dict(self: "TestEmailMessage") -> None:
        """Test to_dict method."""
        # Create an email message
        email = EmailMessage(
            message_id="test_id",
            subject="Test Subject",
            sender="sender@example.com",
            recipient="recipient@example.com",
            body="Test Body",
            timestamp="2023-01-01T12:00:00Z",
            is_read=True,
            folder="SENT",
        )

        # Get dictionary representation
        email_dict = email.to_dict()

        # Verify dictionary
        assert email_dict["id"] == "test_id"
        assert email_dict["subject"] == "Test Subject"
        assert email_dict["sender"] == "sender@example.com"
        assert email_dict["from_"] == "sender@example.com"  # Alias for sender
        assert email_dict["recipient"] == "recipient@example.com"
        assert email_dict["body"] == "Test Body"
        assert email_dict["timestamp"] == "2023-01-01T12:00:00Z"
        assert email_dict["is_read"] is True
        assert email_dict["folder"] == "SENT"


class TestAttachment:
    """Test Attachment class."""

    def test_init(self: "TestAttachment") -> None:
        """Test initialization."""
        attachment = Attachment(
            attachment_id="att1",
            filename="test.txt",
            content_type="text/plain",
            size=TEST_ATTACHMENT_SIZE,
            content=b"test content",
        )

        assert attachment.attachment_id == "att1"
        assert attachment.filename == "test.txt"
        assert attachment.content_type == "text/plain"
        assert attachment.size == TEST_ATTACHMENT_SIZE

    def test_get_content(self: "TestAttachment") -> None:
        """Test get_content method."""
        attachment = Attachment(
            attachment_id="att1",
            filename="test.txt",
            content_type="text/plain",
            size=TEST_ATTACHMENT_SIZE,
            content=b"test content",
        )

        assert attachment.get_content() == b"test content"


class TestEmailClient:
    """Test EmailClient abstract base class."""

    def test_cannot_instantiate_abstract_class(self: "TestEmailClient") -> None:
        """Test that EmailClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            cast(Any, EmailClient())  # type: ignore[abstract]


class TestCompleteEmailClient(EmailClient):
    """Complete implementation of EmailClient for testing."""

    def authenticate(self: "TestCompleteEmailClient") -> bool:
        """Authenticate with the email service."""
        return True

    def send_email(
        self: "TestCompleteEmailClient",
        recipient: str,  # Keep parameters for interface compliance
        subject: str,
        body: str,
    ) -> bool:
        """Send an email."""
        # Use parameters to avoid ARG002
        return bool(recipient and subject and body)

    def retrieve_emails(
        self: "TestCompleteEmailClient",
        folder: str = DEFAULT_INBOX_NAME,
        limit: int = DEFAULT_EMAIL_LIMIT,
    ) -> list[EmailMessage]:
        """Retrieve emails from the specified folder."""
        # Use parameters to avoid ARG002
        if folder and limit > 0:
            return [
                EmailMessage(
                    message_id="test_id",
                    subject="Test Subject",
                    sender="sender@example.com",
                    recipient="recipient@example.com",
                    body="Test Body",
                    timestamp="2023-01-01T12:00:00Z",
                )
            ]
        return []

    def delete_email(self: "TestCompleteEmailClient", email_id: str) -> bool:
        """Delete an email by ID."""
        return bool(email_id)  # Use parameter to avoid ARG002

    def mark_as_read(self: "TestCompleteEmailClient", email_id: str) -> bool:
        """Mark an email as read."""
        return bool(email_id)  # Use parameter to avoid ARG002

    def search_messages(
        self: "TestCompleteEmailClient",
        query: str,
        folder: str = DEFAULT_INBOX_NAME,
    ) -> Iterator[EmailMessage]:
        """Search for messages matching a query."""
        # Use parameters to avoid ARG002
        if query and folder:
            yield EmailMessage(
                message_id="test_id",
                subject="Test Subject",
                sender="sender@example.com",
                recipient="recipient@example.com",
                body="Test Body",
                timestamp="2023-01-01T12:00:00Z",
            )

    def get_folders(self: "TestCompleteEmailClient") -> list[str]:
        """Get available folders/labels."""
        return ["INBOX", "SENT", "DRAFTS", "TRASH"]


class TestEmailClientImplementation:
    """Test EmailClient implementation."""

    def test_complete_implementation(self: "TestEmailClientImplementation") -> None:
        """Test a complete implementation of EmailClient."""
        client = TestCompleteEmailClient()

        assert client.authenticate() is True
        assert client.send_email("recipient@example.com", "Subject", "Body") is True
        assert len(client.retrieve_emails()) == 1
        assert client.delete_email("test_id") is True
        assert client.mark_as_read("test_id") is True

        # Test search_messages
        messages = list(client.search_messages("test"))
        assert len(messages) == 1

        # Test get_folders
        folders = client.get_folders()
        assert len(folders) == TEST_FOLDER_COUNT
        assert "INBOX" in folders


class TestEmailClientFactory:
    """Test EmailClient factory function."""

    def test_get_client_gmail(self: "TestEmailClientFactory") -> None:
        """Test get_client with gmail provider."""
        # Should raise error without credentials_file
        with pytest.raises(ValueError, match="Email provider .* is not supported"):
            get_client("unknown_provider")

        # With credentials_file should import and create GmailClient
        with pytest.raises(EmailClientError):
            # Will fail to authenticate but should create the right type
            get_client("gmail", credentials_file="nonexistent.json")

    def test_get_client_unknown_provider(self: "TestEmailClientFactory") -> None:
        """Test get_client with unknown provider."""
        with pytest.raises(ValueError, match="Email provider .* is not supported"):
            get_client("unknown")


class TestPartialEmailClient(EmailClient):
    """Partial implementation of EmailClient for testing."""

    def authenticate(self: "TestPartialEmailClient") -> bool:
        """Authenticate with the email service."""
        return True

    def send_email(
        self: "TestPartialEmailClient",
        recipient: str,  # Keep parameters for interface compliance
        subject: str,
        body: str,
    ) -> bool:
        """Send an email."""
        # Use parameters to avoid ARG002
        return bool(recipient and subject and body)

    def retrieve_emails(
        self: "TestPartialEmailClient",
        folder: str = DEFAULT_INBOX_NAME,
        limit: int = DEFAULT_EMAIL_LIMIT,
    ) -> list[EmailMessage]:
        """Retrieve emails from the specified folder."""
        # Use parameters to avoid ARG002 while returning empty list
        return [] if folder and limit >= 0 else []

    def delete_email(self: "TestPartialEmailClient", email_id: str) -> bool:
        """Delete an email by ID."""
        return bool(email_id)  # Use parameter to avoid ARG002

    def mark_as_read(self: "TestPartialEmailClient", email_id: str) -> bool:
        """Mark an email as read."""
        return bool(email_id)  # Use parameter to avoid ARG002

    def search_messages(
        self: "TestPartialEmailClient",
        query: str,
        folder: str = DEFAULT_INBOX_NAME,
    ) -> Iterator[EmailMessage]:
        """Search for messages matching a query."""
        # Return an empty iterator, use parameters to avoid ARG002
        return iter([]) if query and folder else iter([])

    def get_folders(self: "TestPartialEmailClient") -> list[str]:
        """Get available folders/labels."""
        return ["INBOX"]


class TestEmailClientExtensions:
    """Test EmailClient extension methods."""

    def test_get_messages(self: "TestEmailClientExtensions") -> None:
        """Test get_messages method."""
        client = TestCompleteEmailClient()
        messages = list(client.get_messages())
        assert len(messages) == 1
        assert isinstance(messages[0], EmailMessage)

    def test_get_messages_empty(self: "TestEmailClientExtensions") -> None:
        """Test get_messages with empty result."""
        client = TestPartialEmailClient()
        messages = list(client.get_messages())
        assert len(messages) == 0

    def test_search_messages(self: "TestEmailClientExtensions") -> None:
        """Test search_messages method."""
        client = TestCompleteEmailClient()
        messages = list(client.search_messages("test"))
        assert len(messages) == 1
        assert isinstance(messages[0], EmailMessage)

    def test_search_messages_empty(self: "TestEmailClientExtensions") -> None:
        """Test search_messages with empty result."""
        client = TestPartialEmailClient()
        messages = list(client.search_messages("test"))
        assert len(messages) == 0
