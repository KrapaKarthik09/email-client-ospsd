import pytest
import tempfile
import os
import shutil
from pathlib import Path

from my_inbox_impl import get_client, ClientImpl, MessageImpl, AttachmentImpl
from my_inbox_impl.mail_fetcher import MockFetcher


@pytest.fixture
def test_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after test
    shutil.rmtree(temp_dir)


@pytest.fixture
def client(test_dir):
    """Set up test client with temporary directory."""
    return ClientImpl(data_dir=test_dir)


def test_get_client():
    """Test that get_client returns a valid Client instance."""
    client = get_client()
    assert client is not None

    # Check that it has the required methods
    assert hasattr(client, "get_messages")
    assert hasattr(client, "search_messages")
    assert hasattr(client, "get_folders")


def test_attachment_implementation():
    """Test the AttachmentImpl class."""
    test_content = b"Test content for the attachment"
    attachment = AttachmentImpl(
        filename="test.txt", content_type="text/plain", content=test_content
    )

    # Check properties
    assert attachment.filename == "test.txt"
    assert attachment.content_type == "text/plain"
    assert attachment.size == len(test_content)
    assert attachment.get_content() == test_content


def test_message_implementation():
    """Test the MessageImpl class."""
    # Create a test message
    message = MessageImpl(
        _id="test123",
        _from="sender@example.com",
        _to="recipient@example.com",
        _subject="Test Subject",
        _body="Test body content",
        _cc="cc@example.com",
        _bcc="bcc@example.com",
        _date="Mon, 01 Apr 2025 12:00:00 +0000",
        _is_read=False,
    )

    # Check properties
    assert message.id == "test123"
    assert message.from_ == "sender@example.com"
    assert message.to == "recipient@example.com"
    assert message.cc == "cc@example.com"
    assert message.bcc == "bcc@example.com"
    assert message.date == "Mon, 01 Apr 2025 12:00:00 +0000"
    assert message.subject == "Test Subject"
    assert message.body == "Test body content"
    assert message.is_read is False
    assert len(message.attachments) == 0

    # Test mark_as_read and mark_as_unread
    message.mark_as_read()
    assert message.is_read is True

    message.mark_as_unread()
    assert message.is_read is False

    # Test message with attachments
    test_attachment = AttachmentImpl(
        filename="test.txt", content_type="text/plain", content=b"Test content"
    )

    message_with_attachment = MessageImpl(
        _id="test456",
        _from="sender@example.com",
        _to="recipient@example.com",
        _subject="Test with Attachment",
        _body="Message with attachment",
        _attachments=[test_attachment],
    )

    assert len(message_with_attachment.attachments) == 1
    assert message_with_attachment.attachments[0].filename == "test.txt"


def test_client_implementation(client, test_dir):
    """Test the ClientImpl class."""
    # Check default folders
    folders = client.get_folders()
    assert "INBOX" in folders
    assert "Sent" in folders

    # Verify folder directories were created
    for folder in folders:
        folder_path = os.path.join(test_dir, folder)
        assert os.path.exists(folder_path)

    # Test adding a message
    message = MessageImpl(
        _id="test123",
        _from="sender@example.com",
        _to="recipient@example.com",
        _subject="Test Subject",
        _body="Test body content",
    )

    client.add_message(message, "INBOX")

    # Verify message was added
    messages = list(client.get_messages(folder="INBOX"))
    assert len(messages) == 1
    assert messages[0].subject == "Test Subject"

    # Check message was saved to disk
    message_path = os.path.join(test_dir, "INBOX", f"{message.id}.json")
    assert os.path.exists(message_path)

    # Test search functionality
    search_results = list(client.search_messages("Test", "INBOX"))
    assert len(search_results) == 1

    # Test with no matching messages
    search_results = list(client.search_messages("NotFound", "INBOX"))
    assert len(search_results) == 0

    # Test creating a new folder
    client.create_folder("TestFolder")
    folders = client.get_folders()
    assert "TestFolder" in folders

    # Test moving a message between folders
    client.move_message(message.id, "INBOX", "TestFolder")

    # Verify message was moved
    inbox_messages = list(client.get_messages(folder="INBOX"))
    assert len(inbox_messages) == 0

    test_folder_messages = list(client.get_messages(folder="TestFolder"))
    assert len(test_folder_messages) == 1

    # Test deleting a message
    client.delete_message(message.id, "TestFolder")
    test_folder_messages = list(client.get_messages(folder="TestFolder"))
    assert len(test_folder_messages) == 0


def test_mock_fetcher(client):
    """Test the MockFetcher class."""
    # Create a mock fetcher
    fetcher = MockFetcher()
    fetcher.set_client(client)

    # Generate mock messages
    mock_messages = fetcher.fetch_messages(count=10)
    assert len(mock_messages) == 10

    # Verify messages were added to the client
    client_messages = list(client.get_messages(folder="INBOX"))
    assert len(client_messages) == 10

    # Test search with mock messages
    search_results = list(client.search_messages("Important", "INBOX"))
    assert len(search_results) >= 1

    # Check that some messages have attachments
    messages_with_attachments = [m for m in client_messages if m.attachments]
    assert len(messages_with_attachments) >= 1
