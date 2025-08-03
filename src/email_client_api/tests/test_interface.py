"""Tests for the EmailClient interface.

This module contains tests to validate the abstract interface enforcement
and the EmailMessage data class functionality.
"""



import pytest

from email_client_api import (
    AuthenticationError,
    EmailClient,
    EmailClientError,
    EmailMessage,
)

# Constants
DEFAULT_INBOX_NAME = "INBOX"
DEFAULT_EMAIL_LIMIT = 10


class TestEmailMessage:
    """Test cases for the EmailMessage data class."""

    def test_email_message_initialization(self) -> None:
        """Test EmailMessage can be initialized with required fields."""
        email = EmailMessage(
            id="test-id-123",
            subject="Test Subject",
            sender="sender@example.com",
            recipient="recipient@example.com",
            body="Test email body content",
            timestamp="2023-01-01T12:00:00",
        )

        assert email.id == "test-id-123"
        assert email.subject == "Test Subject"
        assert email.sender == "sender@example.com"
        assert email.recipient == "recipient@example.com"
        assert email.body == "Test email body content"
        assert email.timestamp == "2023-01-01T12:00:00"
        assert email.is_read is False  # Default value
        assert email.folder == "INBOX"  # Default value
        assert email.attachments == []  # Default value

    def test_email_message_with_optional_fields(self) -> None:
        """Test EmailMessage with all optional fields set."""
        attachments = [{"name": "test.pdf", "size": 1024}]

        email = EmailMessage(
            id="test-id-456",
            subject="Test Subject 2",
            sender="sender2@example.com",
            recipient="recipient2@example.com",
            body="Test email body content 2",
            timestamp="2023-01-02T15:30:00",
            is_read=True,
            folder="SENT",
            attachments=attachments,
        )

        assert email.is_read is True
        assert email.folder == "SENT"
        assert email.attachments == attachments

    def test_email_message_to_dict(self) -> None:
        """Test EmailMessage.to_dict() returns correct dictionary format."""
        email = EmailMessage(
            id="dict-test-123",
            subject="Dict Test",
            sender="dict@example.com",
            recipient="test@example.com",
            body="Dictionary test content",
            timestamp="2023-01-03T09:15:00",
            is_read=True,
            folder="DRAFT",
        )

        result_dict = email.to_dict()

        expected_dict = {
            "id": "dict-test-123",
            "subject": "Dict Test",
            "sender": "dict@example.com",
            "recipient": "test@example.com",
            "body": "Dictionary test content",
            "timestamp": "2023-01-03T09:15:00",
            "is_read": True,
            "folder": "DRAFT",
            "attachments": [],
        }

        assert result_dict == expected_dict


class TestEmailClientInterface:
    """Test cases for the EmailClient abstract interface."""

    def test_cannot_instantiate_abstract_class(self) -> None:
        """Test that EmailClient cannot be instantiated directly."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            EmailClient()  # type: ignore

    def test_concrete_implementation_must_implement_all_methods(self) -> None:
        """Test that concrete implementations must implement all methods."""
        # Define an incomplete implementation
        class IncompleteEmailClient(EmailClient):
            """Incomplete implementation of EmailClient interface."""

            def send_email(self, recipient: str, subject: str, body: str) -> bool:
                """Implemented method."""
                return True
            # Missing other required methods

        # Attempting to instantiate should raise TypeError
        with pytest.raises(TypeError):  # type: ignore[unreachable]
            IncompleteEmailClient()  # type: ignore[abstract]

    def test_complete_implementation_can_be_instantiated(self) -> None:
        """Test that a complete implementation can be instantiated."""
        # Define a concrete implementation with all required methods
        class CompleteEmailClient(EmailClient):
            """Complete implementation of EmailClient interface."""

            def send_email(self, recipient: str, subject: str, body: str) -> bool:
                return True

            def retrieve_emails(
                self,
                folder: str = DEFAULT_INBOX_NAME,
                limit: int = DEFAULT_EMAIL_LIMIT,
            ) -> list[EmailMessage]:
                return []

            def delete_email(self, email_id: str) -> bool:
                return True

            def mark_as_read(self, email_id: str) -> bool:
                return True

            def authenticate(self) -> bool:
                return True

        # Should not raise any exception
        client = CompleteEmailClient()
        assert isinstance(client, EmailClient)

    def test_method_signatures_are_enforced(self) -> None:
        """Test that method signatures are enforced correctly."""
        # Define a concrete implementation with all required methods
        class TestEmailClient(EmailClient):
            """Test email client implementation."""

            def send_email(self, recipient: str, subject: str, body: str) -> bool:
                return True

            def retrieve_emails(
                self,
                folder: str = DEFAULT_INBOX_NAME,
                limit: int = DEFAULT_EMAIL_LIMIT,
            ) -> list[EmailMessage]:
                return []

            def delete_email(self, email_id: str) -> bool:
                return True

            def mark_as_read(self, email_id: str) -> bool:
                return True

            def authenticate(self) -> bool:
                return True

        client = TestEmailClient()

        # Test method exists and callable
        assert hasattr(client, "send_email")
        assert callable(client.send_email)
        assert hasattr(client, "retrieve_emails")
        assert callable(client.retrieve_emails)
        assert hasattr(client, "delete_email")
        assert callable(client.delete_email)
        assert hasattr(client, "mark_as_read")
        assert callable(client.mark_as_read)
        assert hasattr(client, "authenticate")
        assert callable(client.authenticate)


class TestExceptionClasses:
    """Test cases for exception classes."""

    def test_email_client_error_inheritance(self) -> None:
        """Test EmailClientError inherits from Exception."""
        error = EmailClientError("Test error message")
        assert isinstance(error, Exception)
        assert str(error) == "Test error message"

    def test_authentication_error_inheritance(self) -> None:
        """Test AuthenticationError inherits from EmailClientError."""
        error = AuthenticationError("Auth failed")
        assert isinstance(error, EmailClientError)
        assert isinstance(error, Exception)
        assert str(error) == "Auth failed"

    def test_exception_can_be_raised_and_caught(self) -> None:
        """Test exceptions can be properly raised and caught."""

        def raise_email_client_error() -> None:
            raise EmailClientError("Generic email error")

        def raise_authentication_error() -> None:
            raise AuthenticationError("Authentication failed")

        # Test EmailClientError
        with pytest.raises(EmailClientError, match="Generic email error"):
            raise_email_client_error()

        # Test AuthenticationError
        with pytest.raises(AuthenticationError, match="Authentication failed"):
            raise_authentication_error()

        # Test AuthenticationError can be caught as EmailClientError
        with pytest.raises(EmailClientError):
            raise_authentication_error()


class TestInterfaceContract:
    """Test cases for interface contract validation."""

    def test_interface_contract_documentation(self) -> None:
        """Test that interface methods have proper documentation."""
        # Check that abstract methods have docstrings
        assert EmailClient.send_email.__doc__ is not None
        assert "Send an email" in EmailClient.send_email.__doc__

        assert EmailClient.retrieve_emails.__doc__ is not None
        assert "Retrieve emails" in EmailClient.retrieve_emails.__doc__

        assert EmailClient.delete_email.__doc__ is not None
        assert "Delete an email" in EmailClient.delete_email.__doc__

        assert EmailClient.mark_as_read.__doc__ is not None
        assert "Mark an email as read" in EmailClient.mark_as_read.__doc__

        assert EmailClient.authenticate.__doc__ is not None
        assert "Authenticate" in EmailClient.authenticate.__doc__

    def test_method_parameter_types(self) -> None:
        """Test that method parameters have correct type hints."""
        import inspect

        # Test send_email method signature
        sig = inspect.signature(EmailClient.send_email)
        params = sig.parameters

        assert "recipient" in params
        assert "subject" in params
        assert "body" in params
        assert sig.return_annotation == bool

        # Test retrieve_emails method signature
        sig = inspect.signature(EmailClient.retrieve_emails)
        params = sig.parameters

        assert "folder" in params
        assert "limit" in params
        assert params["folder"].default == DEFAULT_INBOX_NAME
        assert params["limit"].default == DEFAULT_EMAIL_LIMIT
