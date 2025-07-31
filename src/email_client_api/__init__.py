"""Email Client API - Abstract interface for email client implementations.

This module defines the core interface that all email client implementations
must adhere to, promoting consistency and interchangeability between different
email service providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

__version__ = "0.1.0"
__all__ = ["EmailClient", "EmailMessage", "AuthenticationError", "EmailClientError"]


class EmailClientError(Exception):
    """Base exception for email client operations."""
    
    pass


class AuthenticationError(EmailClientError):
    """Raised when authentication with email service fails."""
    
    pass


class EmailMessage:
    """Data class representing an email message."""
    
    def __init__(
        self,
        id: str,
        subject: str,
        sender: str,
        recipient: str,
        body: str,
        timestamp: str,
        is_read: bool = False,
        folder: str = "INBOX",
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Initialize an email message.
        
        Args:
            id: Unique email identifier
            subject: Email subject line
            sender: Sender email address
            recipient: Recipient email address
            body: Email body content
            timestamp: ISO format timestamp
            is_read: Whether the email has been read
            folder: Folder location of the email
            attachments: List of attachment metadata
        """
        self.id = id
        self.subject = subject
        self.sender = sender
        self.recipient = recipient
        self.body = body
        self.timestamp = timestamp
        self.is_read = is_read
        self.folder = folder
        self.attachments = attachments or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert email message to dictionary format.
        
        Returns:
            Dict containing email data
        """
        return {
            "id": self.id,
            "subject": self.subject,
            "sender": self.sender,
            "recipient": self.recipient,
            "body": self.body,
            "timestamp": self.timestamp,
            "is_read": self.is_read,
            "folder": self.folder,
            "attachments": self.attachments,
        }


class EmailClient(ABC):
    """Abstract base class defining the email client interface.
    
    This interface defines the contract that all email client implementations
    must follow, ensuring consistency across different email service providers.
    """
    
    @abstractmethod
    def send_email(self, recipient: str, subject: str, body: str) -> bool:
        """Send an email to a recipient.
        
        Args:
            recipient: Email address of the recipient
            subject: Subject line of the email
            body: Email body content
            
        Returns:
            bool: True if email was sent successfully, False otherwise
            
        Raises:
            AuthenticationError: If authentication with email service fails
            EmailClientError: If email sending fails for other reasons
        """
        pass
    
    @abstractmethod
    def retrieve_emails(
        self, 
        folder: str = "INBOX", 
        limit: int = 10
    ) -> List[EmailMessage]:
        """Retrieve emails from a specified folder.
        
        Args:
            folder: Email folder to retrieve from (default: "INBOX")
            limit: Maximum number of emails to retrieve (default: 10)
            
        Returns:
            List[EmailMessage]: List of email message objects
            
        Raises:
            AuthenticationError: If authentication with email service fails
            EmailClientError: If email retrieval fails for other reasons
        """
        pass
    
    @abstractmethod
    def delete_email(self, email_id: str) -> bool:
        """Delete an email by its ID.
        
        Args:
            email_id: Unique identifier of the email to delete
            
        Returns:
            bool: True if email was deleted successfully, False otherwise
            
        Raises:
            AuthenticationError: If authentication with email service fails
            EmailClientError: If email deletion fails for other reasons
        """
        pass
    
    @abstractmethod
    def mark_as_read(self, email_id: str) -> bool:
        """Mark an email as read.
        
        Args:
            email_id: Unique identifier of the email to mark as read
            
        Returns:
            bool: True if email was marked as read successfully, False otherwise
            
        Raises:
            AuthenticationError: If authentication with email service fails
            EmailClientError: If marking email as read fails for other reasons
        """
        pass
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the email service.
        
        Returns:
            bool: True if authentication successful, False otherwise
            
        Raises:
            AuthenticationError: If authentication fails
        """
        pass 