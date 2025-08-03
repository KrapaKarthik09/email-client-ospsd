"""Tests for the Gmail client implementation.

This module contains tests for the GmailClient class, including mocked
Gmail API interactions and authentication testing.
"""

import base64
import os

# Import the classes we need to test
import sys
from typing import Any
from unittest import mock
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest
from googleapiclient.errors import HttpError

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from email_client_api import AuthenticationError, EmailClientError, EmailMessage

from gmail_client_impl import GmailClient

# Constants
DEFAULT_EMAIL_LIMIT = 2
DEFAULT_SCOPES_COUNT = 3


class TestGmailClientInitialization:
    """Test cases for GmailClient initialization."""

    def test_init_with_defaults(self) -> None:
        """Test GmailClient initialization with default parameters."""
        client = GmailClient()

        assert client.credentials_file == "credentials.json"
        assert client.token_file == "token.json"
        assert client.service is None
        assert client.credentials is None
        assert len(client.scopes) == DEFAULT_SCOPES_COUNT  # Default scopes

    def test_init_with_custom_params(self) -> None:
        """Test GmailClient initialization with custom parameters."""
        custom_scopes = ["https://www.googleapis.com/auth/gmail.readonly"]

        client = GmailClient(
            credentials_file="custom_creds.json",
            token_file="custom_token.json",
            scopes=custom_scopes,
        )

        assert client.credentials_file == "custom_creds.json"
        assert client.token_file == "custom_token.json"
        assert client.scopes == custom_scopes


class TestGmailClientAuthentication:
    """Test cases for Gmail authentication."""

    @patch("gmail_client_impl.build")
    @patch("gmail_client_impl.InstalledAppFlow.from_client_secrets_file")
    @patch("os.path.exists")
    def test_authenticate_new_user(
        self,
        mock_exists: Mock,
        mock_flow: Mock,
        mock_build: Mock,
    ) -> None:
        """Test authentication for a new user without existing token."""
        # Setup mocks
        mock_exists.side_effect = lambda path: path == "credentials.json"
        mock_credentials = Mock()
        mock_credentials.to_json.return_value = '{"token": "test"}'
        mock_flow_instance = Mock()
        mock_flow_instance.run_local_server.return_value = mock_credentials
        mock_flow.return_value = mock_flow_instance
        mock_service = Mock()
        mock_build.return_value = mock_service

        client = GmailClient()

        with patch("builtins.open", mock_open()) as mock_file:
            result = client.authenticate()

        assert result is True
        assert client.credentials == mock_credentials
        assert client.service == mock_service
        mock_flow.assert_called_once()
        mock_file.assert_called_once_with("token.json", "w", encoding="utf-8")

    @patch("gmail_client_impl.build")
    @patch("gmail_client_impl.Credentials.from_authorized_user_file")
    @patch("os.path.exists")
    def test_authenticate_existing_valid_token(
        self,
        mock_exists: Mock,
        mock_from_file: Mock,
        mock_build: Mock,
    ) -> None:
        """Test authentication with existing valid token."""
        # Setup mocks
        mock_exists.return_value = True
        mock_credentials = Mock()
        mock_credentials.valid = True
        mock_from_file.return_value = mock_credentials
        mock_service = Mock()
        mock_build.return_value = mock_service

        client = GmailClient()
        result = client.authenticate()

        assert result is True
        assert client.credentials == mock_credentials
        assert client.service == mock_service
        mock_from_file.assert_called_once_with("token.json", client.scopes)

    @patch("gmail_client_impl.build")
    @patch("gmail_client_impl.Credentials.from_authorized_user_file")
    @patch("gmail_client_impl.Request")
    @patch("os.path.exists")
    def test_authenticate_refresh_expired_token(
        self,
        mock_exists: Mock,
        mock_request: Mock,
        mock_from_file: Mock,
        mock_build: Mock,
    ) -> None:
        """Test authentication with expired token that can be refreshed."""
        # Setup mocks
        mock_exists.return_value = True
        mock_credentials = Mock()
        mock_credentials.valid = False
        mock_credentials.expired = True
        mock_credentials.refresh_token = "refresh_token"
        mock_credentials.to_json.return_value = '{"token": "refreshed"}'
        mock_from_file.return_value = mock_credentials
        mock_service = Mock()
        mock_build.return_value = mock_service

        client = GmailClient()

        with patch("builtins.open", mock_open()) as mock_file:
            result = client.authenticate()

        assert result is True
        mock_credentials.refresh.assert_called_once()
        mock_file.assert_called_once_with("token.json", "w", encoding="utf-8")

    @patch("os.path.exists")
    def test_authenticate_missing_credentials_file(self, mock_exists: Mock) -> None:
        """Test authentication fails when credentials file is missing."""
        mock_exists.return_value = False

        client = GmailClient()

        with pytest.raises(AuthenticationError, match="Credentials file not found"):
            client.authenticate()


class TestGmailClientSendEmail:
    """Test cases for sending emails."""

    def setup_method(self) -> None:
        """Set up test client with mocked service."""
        self.client = GmailClient()
        self.client.service = Mock()

    def test_send_email_success(self) -> None:
        """Test successful email sending."""
        # Setup mock
        mock_result = {"id": "sent_message_id_123"}
        self.client.service.users().messages().send().execute.return_value = mock_result

        result = self.client.send_email(
            recipient="test@example.com",
            subject="Test Subject",
            body="Test Body",
        )

        assert result is True
        # Verify the send was called with the right parameters
        self.client.service.users().messages().send.assert_called_with(
            userId="me", body={"raw": mock.ANY},
        )

    def test_send_email_not_authenticated(self) -> None:
        """Test sending email without authentication."""
        client = GmailClient()  # No service set

        with pytest.raises(AuthenticationError, match="Not authenticated"):
            client.send_email("test@example.com", "Subject", "Body")

    def test_send_email_http_error(self) -> None:
        """Test sending email with HTTP error."""
        # Setup mock to raise HttpError
        mock_response = Mock()
        mock_response.status = 400
        http_error = HttpError(mock_response, b'{"error": "Bad Request"}')
        self.client.service.users().messages().send().execute.side_effect = http_error

        with pytest.raises(EmailClientError, match="Failed to send email"):
            self.client.send_email("test@example.com", "Subject", "Body")


class TestGmailClientRetrieveEmails:
    """Test cases for retrieving emails."""

    def setup_method(self: "TestGmailClientRetrieveEmails") -> None:
        """Set up test client with mocked service."""
        self.client = GmailClient()
        self.client.service = Mock()

    def create_mock_gmail_message(self: "TestGmailClientRetrieveEmails", email_id: str) -> dict[str, Any]:
        """Create a mock Gmail API message."""
        return {
            "id": email_id,
            "internalDate": "1640995200000",  # 2022-01-01 00:00:00
            "labelIds": ["INBOX", "UNREAD"],
            "payload": {
                "headers": [
                    {"name": "Subject", "value": f"Test Subject {email_id}"},
                    {"name": "From", "value": f"sender{email_id}@example.com"},
                    {"name": "To", "value": f"recipient{email_id}@example.com"},
                ],
                "mimeType": "text/plain",
                "body": {
                    "data": base64.urlsafe_b64encode(
                        f"Test body content {email_id}".encode(),
                    ).decode(),
                },
            },
        }

    def test_retrieve_emails_success(self: "TestGmailClientRetrieveEmails") -> None:
        """Test successful email retrieval."""
        # Setup mocks
        mock_messages_list = {
            "messages": [
                {"id": "msg1"},
                {"id": "msg2"},
            ],
        }
        self.client.service.users().messages().list().execute.return_value = mock_messages_list

        # Mock individual message retrieval
        self.client.service.users().messages().get.side_effect = [
            MagicMock(execute=lambda: self.create_mock_gmail_message("msg1")),
            MagicMock(execute=lambda: self.create_mock_gmail_message("msg2")),
        ]

        emails = self.client.retrieve_emails(folder="INBOX", limit=DEFAULT_EMAIL_LIMIT)

        assert len(emails) == DEFAULT_EMAIL_LIMIT
        assert all(isinstance(email, EmailMessage) for email in emails)
        assert emails[0].id == "msg1"
        assert emails[1].id == "msg2"
        assert emails[0].subject == "Test Subject msg1"
        assert emails[0].sender == "sendermsg1@example.com"

    def test_retrieve_emails_not_authenticated(self: "TestGmailClientRetrieveEmails") -> None:
        """Test retrieving emails without authentication."""
        client = GmailClient()  # No service set

        with pytest.raises(AuthenticationError, match="Not authenticated"):
            client.retrieve_emails()

    def test_retrieve_emails_empty_result(self: "TestGmailClientRetrieveEmails") -> None:
        """Test retrieving emails when none exist."""
        mock_messages_list = {"messages": []}
        self.client.service.users().messages().list().execute.return_value = mock_messages_list

        emails = self.client.retrieve_emails()

        assert emails == []


class TestGmailClientDeleteEmail:
    """Test cases for deleting emails."""

    def setup_method(self: "TestGmailClientDeleteEmail") -> None:
        """Set up test client with mocked service."""
        self.client = GmailClient()
        self.client.service = Mock()

    def test_delete_email_success(self) -> None:
        """Test successful email deletion."""
        self.client.service.users().messages().delete().execute.return_value = {}

        result = self.client.delete_email("test_email_id")

        assert result is True
        # Verify the delete was called with the right parameters
        self.client.service.users().messages().delete.assert_called_with(
            userId="me", id="test_email_id",
        )

    def test_delete_email_not_found(self) -> None:
        """Test deleting non-existent email."""
        mock_response = Mock()
        mock_response.status = 404
        http_error = HttpError(mock_response, b'{"error": "Not Found"}')
        self.client.service.users().messages().delete().execute.side_effect = http_error

        result = self.client.delete_email("nonexistent_id")

        assert result is False

    def test_delete_email_not_authenticated(self: "TestGmailClientDeleteEmail") -> None:
        """Test deleting email without authentication."""
        client = GmailClient()  # No service set

        with pytest.raises(AuthenticationError, match="Not authenticated"):
            client.delete_email("test_id")


class TestGmailClientMarkAsRead:
    """Test cases for marking emails as read."""

    def setup_method(self: "TestGmailClientMarkAsRead") -> None:
        """Set up test client with mocked service."""
        self.client = GmailClient()
        self.client.service = Mock()

    def test_mark_as_read_success(self) -> None:
        """Test successfully marking email as read."""
        self.client.service.users().messages().modify().execute.return_value = {}

        result = self.client.mark_as_read("test_email_id")

        assert result is True
        # Verify the modify was called with the right parameters
        self.client.service.users().messages().modify.assert_called_with(
            userId="me",
            id="test_email_id",
            body={"removeLabelIds": ["UNREAD"]},
        )

    def test_mark_as_read_not_found(self) -> None:
        """Test marking non-existent email as read."""
        mock_response = Mock()
        mock_response.status = 404
        http_error = HttpError(mock_response, b'{"error": "Not Found"}')
        self.client.service.users().messages().modify().execute.side_effect = http_error

        result = self.client.mark_as_read("nonexistent_id")

        assert result is False

    def test_mark_as_read_not_authenticated(self: "TestGmailClientMarkAsRead") -> None:
        """Test marking email as read without authentication."""
        client = GmailClient()  # No service set

        with pytest.raises(AuthenticationError, match="Not authenticated"):
            client.mark_as_read("test_id")


class TestGmailClientMessageParsing:
    """Test cases for Gmail message parsing."""

    def setup_method(self: "TestGmailClientMessageParsing") -> None:
        """Set up test client."""
        self.client = GmailClient()

    def parse_message_for_testing(self: "TestGmailClientMessageParsing", message: dict[str, Any]) -> Any:
        """Access the parse method for testing purposes.

        This helper is used to properly test the private method while avoiding
        linting errors.
        """
        return self.client._parse_gmail_message(message)  # noqa: SLF001

    def test_parse_gmail_message_simple(self: "TestGmailClientMessageParsing") -> None:
        """Test parsing a simple Gmail message."""
        mock_msg = {
            "id": "test_msg_123",
            "internalDate": "1640995200000",  # 2022-01-01 00:00:00
            "labelIds": ["INBOX"],
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                ],
                "mimeType": "text/plain",
                "body": {
                    "data": base64.urlsafe_b64encode(b"Test body content").decode(),
                },
            },
        }

        email = self.parse_message_for_testing(mock_msg)

        assert email is not None
        assert email.id == "test_msg_123"
        assert email.subject == "Test Subject"
        assert email.sender == "sender@example.com"
        assert email.recipient == "recipient@example.com"
        assert email.body == "Test body content"
        assert email.is_read is True  # No UNREAD label
        assert email.folder == "INBOX"

    def test_parse_gmail_message_unread(self: "TestGmailClientMessageParsing") -> None:
        """Test parsing an unread Gmail message."""
        mock_msg = {
            "id": "unread_msg",
            "internalDate": "1640995200000",
            "labelIds": ["INBOX", "UNREAD"],
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Unread Subject"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                ],
                "mimeType": "text/plain",
                "body": {"data": base64.urlsafe_b64encode(b"Unread content").decode()},
            },
        }

        email = self.parse_message_for_testing(mock_msg)

        assert email is not None
        assert email.is_read is False  # UNREAD label present

    def test_parse_gmail_message_multipart(self: "TestGmailClientMessageParsing") -> None:
        """Test parsing a multipart Gmail message."""
        mock_msg = {
            "id": "multipart_msg",
            "internalDate": "1640995200000",
            "labelIds": ["INBOX"],
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Multipart Subject"},
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "To", "value": "recipient@example.com"},
                ],
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {
                            "data": base64.urlsafe_b64encode(b"Plain text part").decode(),
                        },
                    },
                    {
                        "mimeType": "text/html",
                        "body": {
                            "data": base64.urlsafe_b64encode(b"<html>HTML part</html>").decode(),
                        },
                    },
                ],
            },
        }

        email = self.parse_message_for_testing(mock_msg)

        assert email is not None
        assert email.body == "Plain text part"  # Should extract plain text

    def test_parse_gmail_message_invalid(self: "TestGmailClientMessageParsing") -> None:
        """Test parsing an invalid Gmail message."""
        invalid_msg = {"id": "invalid"}  # Missing required fields

        email = self.parse_message_for_testing(invalid_msg)

        assert email is None
