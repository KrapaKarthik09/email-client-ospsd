"""Tests for the Gmail client implementation."""

import base64
import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest import mock
from unittest.mock import MagicMock, Mock, patch

from googleapiclient.errors import HttpError

# Add the src directory to path
parent_dir = Path(__file__).parent.parent.parent
sys.path.append(str(parent_dir))

from email_client_api import EmailMessage, AuthenticationError
from gmail_client_impl import GmailClient

# Constants used in tests
DEFAULT_EMAIL_LIMIT = 2
DEFAULT_SCOPES_COUNT = 3


class TestGmailClientInit:
    """Test Gmail client initialization."""

    def test_init_with_defaults(self: "TestGmailClientInit") -> None:
        """Test initialization with default parameters."""
        client = GmailClient()
        assert client.credentials_file == "credentials.json"
        assert client.token_file == "token.json"
        assert (
            len(client.scopes) == DEFAULT_SCOPES_COUNT
        )  # Use constant instead of magic number
        assert client.service is None

    def test_init_with_custom_params(self: "TestGmailClientInit") -> None:
        """Test initialization with custom parameters."""
        test_scopes = ["scope1", "scope2"]
        client = GmailClient(
            credentials_file="custom_creds.json",
            token_file="custom_token.json",
            scopes=test_scopes,
        )
        assert client.credentials_file == "custom_creds.json"
        assert client.token_file == "custom_token.json"
        assert client.scopes == test_scopes
        assert client.service is None


class TestGmailClientAuthenticate:
    """Test Gmail client authentication."""

    def setup_method(self: "TestGmailClientAuthenticate") -> None:
        """Set up test environment."""
        self.client = GmailClient(
            credentials_file="fake_creds.json",
            token_file="fake_token.json",
        )

    def test_authenticate_success_with_existing_token(
        self: "TestGmailClientAuthenticate",
    ) -> None:
        """Test successful authentication with existing token."""
        # Mock dependencies
        mock_build = Mock(return_value="mock_service")
        mock_credentials = Mock(valid=True)

        # Patch with context managers to scope correctly
        with patch("gmail_client_impl.build", mock_build), patch(
            "pathlib.Path.exists", return_value=True
        ), patch(
            "gmail_client_impl.Credentials.from_authorized_user_file",
            return_value=mock_credentials,
        ):

            # Call authenticate
            result = self.client.authenticate()

            # Assertions
            assert result is True
            mock_build.assert_called_once_with(
                "gmail", "v1", credentials=mock_credentials
            )
            assert self.client.service == "mock_service"

    def test_authenticate_with_expired_token(
        self: "TestGmailClientAuthenticate",
    ) -> None:
        """Test authentication with expired token that needs refresh."""
        # Set up mocks
        mock_build = Mock(return_value="mock_service")
        mock_credentials = Mock(
            valid=False, expired=True, refresh_token="fake_refresh_token"
        )
        mock_credentials.to_json.return_value = "{}"

        # Patch with context managers
        with patch("gmail_client_impl.build", mock_build), patch(
            "pathlib.Path.exists", return_value=True
        ), patch(
            "gmail_client_impl.Credentials.from_authorized_user_file",
            return_value=mock_credentials,
        ), patch(
            "pathlib.Path.open", mock.mock_open()
        ):

            # Call authenticate
            result = self.client.authenticate()

            # Assertions
            assert result is True
            mock_credentials.refresh.assert_called_once()
            mock_build.assert_called_once_with(
                "gmail", "v1", credentials=mock_credentials
            )
            assert self.client.service == "mock_service"

    def test_authenticate_oauth_flow(self: "TestGmailClientAuthenticate") -> None:
        """Test OAuth flow for authentication."""
        # This test directly tests the flow branch in authenticate method

        # Create a client with mocked internals for testing the flow
        client = GmailClient(
            credentials_file="test_creds.json",
            token_file="test_token.json",
        )

        # Create mocks for the OAuth flow
        mock_flow = Mock()
        mock_creds = Mock()
        mock_creds.to_json.return_value = "{}"
        mock_flow.run_local_server.return_value = mock_creds
        mock_service = Mock()

        # Setup patches for all components involved in the flow
        with patch("gmail_client_impl.Path.exists", side_effect=[False, True]), patch(
            "gmail_client_impl.InstalledAppFlow.from_client_secrets_file",
            return_value=mock_flow,
        ), patch("gmail_client_impl.Path.open", mock.mock_open()), patch(
            "gmail_client_impl.build", return_value=mock_service
        ):

            # Call authenticate
            result = client.authenticate()

            # Assertions
            assert result is True
            mock_flow.run_local_server.assert_called_once()
            assert client.service == mock_service

    def test_authenticate_credentials_file_not_found(
        self: "TestGmailClientAuthenticate",
    ) -> None:
        """Test authentication when credentials file is not found."""
        # Mock Path.exists to return False
        with patch("pathlib.Path.exists", return_value=False):
            # Call authenticate and expect exception
            with unittest.TestCase().assertRaises(Exception) as context:
                self.client.authenticate()

            # Verify error message
            assert "Credentials file not found" in str(context.exception)


class TestGmailClientSendEmail:
    """Test sending emails with Gmail client."""

    def setup_method(self: "TestGmailClientSendEmail") -> None:
        """Set up test environment."""
        # Create client and mock service
        self.client = GmailClient()
        self.client.service = Mock()

        # Set up the mock chain
        self.mock_send = Mock()
        self.client.service.users.return_value.messages.return_value.send = (
            self.mock_send
        )
        self.mock_send.return_value.execute.return_value = {"id": "fake_id"}

    def test_send_email_success(self: "TestGmailClientSendEmail") -> None:
        """Test successful email sending."""
        # Call send_email
        result = self.client.send_email(
            recipient="test@example.com",
            subject="Test Subject",
            body="Test Body",
        )

        # Assertions
        assert result is True
        self.mock_send.assert_called_with(
            userId="me",
            body=mock.ANY,
        )

    def test_send_email_http_error(self: "TestGmailClientSendEmail") -> None:
        """Test send_email with HttpError."""
        # Set up mock to raise HttpError
        http_error = HttpError(resp=mock.Mock(status=400), content=b"Error content")
        self.mock_send.return_value.execute.side_effect = http_error

        # Call send_email and expect exception
        with unittest.TestCase().assertRaises(Exception) as context:
            self.client.send_email("test@example.com", "Test Subject", "Test Body")

        # Verify error message
        assert "Failed to send email" in str(context.exception)


class TestGmailClientRetrieveEmails:
    """Test retrieving emails with Gmail client."""

    def setup_method(self: "TestGmailClientRetrieveEmails") -> None:
        """Set up test environment."""
        # Create client and mock service
        self.client = GmailClient()
        self.client.service = Mock()

        # Set up mock responses
        self.message_list_response = {
            "messages": [
                {"id": "msg1"},
                {"id": "msg2"},
            ]
        }

        self.message1 = {
            "id": "msg1",
            "internalDate": "1600000000000",
            "labelIds": ["INBOX", "UNREAD"],
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender1@example.com"},
                    {"name": "Subject", "value": "Test Subject 1"},
                    {"name": "To", "value": "recipient@example.com"},
                ],
                "mimeType": "text/plain",
                "body": {"data": base64.b64encode(b"Test Body 1").decode("utf-8")},
            },
        }

        self.message2 = {
            "id": "msg2",
            "internalDate": "1600000000000",
            "labelIds": ["INBOX"],
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender2@example.com"},
                    {"name": "Subject", "value": "Test Subject 2"},
                    {"name": "To", "value": "recipient@example.com"},
                ],
                "mimeType": "text/plain",
                "body": {"data": base64.b64encode(b"Test Body 2").decode("utf-8")},
            },
        }

        # Set up the mock chain for list and get
        self.mock_list = Mock()
        self.mock_get = Mock()
        self.client.service.users.return_value.messages.return_value.list = (
            self.mock_list
        )
        self.client.service.users.return_value.messages.return_value.get = self.mock_get

        # Configure mock responses
        self.mock_list.return_value.execute.return_value = self.message_list_response
        self.mock_get.side_effect = lambda userId, id, **kwargs: Mock(
            execute=Mock(return_value=self.message1 if id == "msg1" else self.message2)
        )

    def test_retrieve_emails_success(self: "TestGmailClientRetrieveEmails") -> None:
        """Test successful email retrieval."""
        # Call retrieve_emails
        result = self.client.retrieve_emails(folder="INBOX", limit=DEFAULT_EMAIL_LIMIT)

        # Assertions
        assert len(result) == DEFAULT_EMAIL_LIMIT
        assert result[0].id == "msg1"
        assert result[0].subject == "Test Subject 1"
        assert result[0].is_read is False
        assert result[1].id == "msg2"
        assert result[1].subject == "Test Subject 2"
        assert result[1].is_read is True

        # Verify API calls
        self.mock_list.assert_called_with(
            userId="me", q="in:inbox", maxResults=DEFAULT_EMAIL_LIMIT
        )
        assert self.mock_get.call_count == DEFAULT_EMAIL_LIMIT

    def test_retrieve_emails_http_error(self: "TestGmailClientRetrieveEmails") -> None:
        """Test retrieve_emails with HttpError."""
        # Set up mock to raise HttpError
        http_error = HttpError(resp=mock.Mock(status=400), content=b"Error content")
        self.mock_list.return_value.execute.side_effect = http_error

        # Call retrieve_emails and expect exception
        with unittest.TestCase().assertRaises(Exception) as context:
            self.client.retrieve_emails()

        # Verify error message
        assert "Failed to retrieve emails" in str(context.exception)


class TestGmailClientDeleteEmail:
    """Test deleting emails with Gmail client."""

    def setup_method(self: "TestGmailClientDeleteEmail") -> None:
        """Set up test environment."""
        # Create client and mock service
        self.client = GmailClient()
        self.client.service = Mock()

        # Set up the mock chain
        self.mock_delete = Mock()
        self.client.service.users.return_value.messages.return_value.delete = (
            self.mock_delete
        )
        self.mock_delete.return_value.execute.return_value = {}

    def test_delete_email_success(self: "TestGmailClientDeleteEmail") -> None:
        """Test successful email deletion."""
        # Call delete_email
        result = self.client.delete_email(email_id="msg1")

        # Assertions
        assert result is True
        self.mock_delete.assert_called_with(userId="me", id="msg1")

    def test_delete_email_not_found(self: "TestGmailClientDeleteEmail") -> None:
        """Test delete_email with not found error."""
        # Set up mock to raise HttpError with 404 status
        http_error = HttpError(resp=mock.Mock(status=404), content=b"Not found")
        self.mock_delete.return_value.execute.side_effect = http_error

        # Call delete_email
        result = self.client.delete_email(email_id="not_exists")

        # Assertions
        assert result is False
        self.mock_delete.assert_called_with(userId="me", id="not_exists")


class TestGmailClientMarkAsRead:
    """Test marking emails as read with Gmail client."""

    def setup_method(self: "TestGmailClientMarkAsRead") -> None:
        """Set up test environment."""
        # Create client and mock service
        self.client = GmailClient()
        self.client.service = Mock()

        # Set up the mock chain
        self.mock_modify = Mock()
        self.client.service.users.return_value.messages.return_value.modify = (
            self.mock_modify
        )
        self.mock_modify.return_value.execute.return_value = {}

    def test_mark_as_read_success(self: "TestGmailClientMarkAsRead") -> None:
        """Test successful marking email as read."""
        # Call mark_as_read
        result = self.client.mark_as_read(email_id="msg1")

        # Assertions
        assert result is True
        self.mock_modify.assert_called_with(
            userId="me",
            id="msg1",
            body={"removeLabelIds": ["UNREAD"]},
        )

    def test_mark_as_read_not_found(self: "TestGmailClientMarkAsRead") -> None:
        """Test mark_as_read with not found error."""
        # Set up mock to raise HttpError with 404 status
        http_error = HttpError(resp=mock.Mock(status=404), content=b"Not found")
        self.mock_modify.return_value.execute.side_effect = http_error

        # Call mark_as_read
        result = self.client.mark_as_read(email_id="not_exists")

        # Assertions
        assert result is False
        self.mock_modify.assert_called_with(
            userId="me",
            id="not_exists",
            body={"removeLabelIds": ["UNREAD"]},
        )


class TestGmailClientMessageParsing:
    """Test message parsing functionality."""

    def setup_method(self: "TestGmailClientMessageParsing") -> None:
        """Set up test environment."""
        self.client = GmailClient()

    # Public helper method to access the private method for testing
    def parse_message_for_testing(
        self: "TestGmailClientMessageParsing", msg: dict[str, Any]
    ) -> EmailMessage:
        """Helper to access the private parse method for testing."""
        result = self.client._parse_gmail_message(msg)
        assert result is not None
        return result

    def test_parse_gmail_message(self: "TestGmailClientMessageParsing") -> None:
        """Test parsing Gmail message to EmailMessage."""
        # Create test message data
        msg = {
            "id": "msg123",
            "internalDate": "1600000000000",
            "labelIds": ["INBOX", "UNREAD"],
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "To", "value": "recipient@example.com"},
                ],
                "mimeType": "text/plain",
                "body": {"data": base64.b64encode(b"Test Body").decode("utf-8")},
            },
        }

        # Parse message
        email = self.parse_message_for_testing(msg)

        # Assertions
        assert email.id == "msg123"
        assert email.subject == "Test Subject"
        assert email.sender == "sender@example.com"
        assert email.recipient == "recipient@example.com"
        assert "Test Body" in email.body
        assert email.is_read is False
        assert email.folder == "INBOX"

    def test_parse_multipart_message(self: "TestGmailClientMessageParsing") -> None:
        """Test parsing multipart Gmail message."""
        # Create test multipart message data
        msg = {
            "id": "msg123",
            "internalDate": "1600000000000",
            "labelIds": ["SENT"],
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"},
                    {"name": "Subject", "value": "Test Multipart"},
                    {"name": "To", "value": "recipient@example.com"},
                ],
                "mimeType": "multipart/alternative",
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {
                            "data": base64.b64encode(b"Plain text part").decode("utf-8")
                        },
                    },
                    {
                        "mimeType": "text/html",
                        "body": {
                            "data": base64.b64encode(b"<html>HTML part</html>").decode(
                                "utf-8"
                            )
                        },
                    },
                ],
            },
        }

        # Parse message
        email = self.parse_message_for_testing(msg)

        # Assertions
        assert email.id == "msg123"
        assert email.subject == "Test Multipart"
        assert "Plain text part" in email.body
        assert email.is_read is True  # No UNREAD label in SENT folder
        assert email.folder == "SENT"
