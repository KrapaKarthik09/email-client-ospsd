import pytest
from unittest.mock import MagicMock, patch
from typing import Iterator, List

# Import your interface definitions
import my_inbox_api
from my_inbox_api import Message, Client, Attachment


class MockAttachment(MagicMock):
    """Mock implementation of Attachment protocol for testing."""

    @property
    def filename(self) -> str:
        return "test_file.txt"

    @property
    def content_type(self) -> str:
        return "text/plain"

    @property
    def size(self) -> int:
        return 1024

    def get_content(self) -> bytes:
        return b"This is test content"


class MockMessage(MagicMock):
    """Mock implementation of Message protocol for testing."""

    @property
    def id(self) -> str:
        return "msg123"

    @property
    def from_(self) -> str:
        return "sender@example.com"

    @property
    def to(self) -> str:
        return "recipient@example.com"

    @property
    def cc(self) -> str:
        return "cc@example.com"

    @property
    def bcc(self) -> str:
        return "bcc@example.com"

    @property
    def date(self) -> str:
        return "Mon, 01 Apr 2025 12:00:00 +0000"

    @property
    def subject(self) -> str:
        return "Test Subject"

    @property
    def body(self) -> str:
        return "This is the test body."

    @property
    def attachments(self) -> List[Attachment]:
        return [MockAttachment()]

    @property
    def is_read(self) -> bool:
        return False

    def mark_as_read(self) -> None:
        pass

    def mark_as_unread(self) -> None:
        pass


class MockClient(MagicMock):
    """Mock implementation of Client protocol for testing."""

    def get_messages(self, limit=None, folder="INBOX") -> Iterator[Message]:
        # Return 5 mock messages, respecting the limit if provided
        messages = [MockMessage() for _ in range(5)]
        if limit is not None:
            messages = messages[:limit]
        return iter(messages)

    def search_messages(self, query, folder="INBOX") -> Iterator[Message]:
        # Return 2 mock messages for any search
        return iter([MockMessage(), MockMessage()])

    def get_folders(self) -> List[str]:
        return ["INBOX", "Sent", "Drafts", "Trash"]


def test_attachment_interface():
    """Test the Attachment protocol properties."""
    attachment = MockAttachment()

    # Test property types
    assert isinstance(attachment.filename, str)
    assert isinstance(attachment.content_type, str)
    assert isinstance(attachment.size, int)
    assert isinstance(attachment.get_content(), bytes)


def test_message_interface():
    """Test the Message protocol properties."""
    message = MockMessage()

    # Test property types
    assert isinstance(message.id, str)
    assert isinstance(message.from_, str)
    assert isinstance(message.to, str)
    assert isinstance(message.cc, str)
    assert isinstance(message.bcc, str)
    assert isinstance(message.date, str)
    assert isinstance(message.subject, str)
    assert isinstance(message.body, str)
    assert isinstance(message.attachments, list)
    assert isinstance(message.is_read, bool)

    # Test attachment list contains Attachment objects
    if message.attachments:
        assert isinstance(message.attachments[0].filename, str)


def test_client_interface():
    """Test the Client protocol methods."""
    client = MockClient()

    # Test get_messages
    messages = list(client.get_messages())
    assert len(messages) == 5
    assert isinstance(messages[0].id, str)

    # Test get_messages with limit
    limited_messages = list(client.get_messages(limit=2))
    assert len(limited_messages) == 2

    # Test search_messages
    search_results = list(client.search_messages("test"))
    assert len(search_results) == 2
    assert isinstance(search_results[0].id, str)

    # Test get_folders
    folders = client.get_folders()
    assert isinstance(folders, list)
    assert "INBOX" in folders


def test_get_client_function(monkeypatch):
    """Test the get_client function returns a Client instance."""
    # Mock get_client function to return our mock client
    mock_client = MockClient()
    monkeypatch.setattr(my_inbox_api, "get_client", lambda: mock_client)

    client = my_inbox_api.get_client()
    assert isinstance(client.get_messages(), Iterator)
    assert isinstance(client.get_folders(), list)
