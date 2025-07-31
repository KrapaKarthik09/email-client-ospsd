# Email Client API

This component defines the abstract interface for email client implementations, promoting consistency and interchangeability between different email service providers.

## Overview

The Email Client API provides a standardized interface that all email client implementations must follow. This ensures that different email service providers (Gmail, Outlook, Yahoo, etc.) can be used interchangeably without changing the client code.

## Components

### EmailClient (Abstract Base Class)

The core interface defining the contract for email operations:

- `send_email(recipient, subject, body)`: Send an email
- `retrieve_emails(folder, limit)`: Retrieve emails from a folder
- `delete_email(email_id)`: Delete an email by ID
- `mark_as_read(email_id)`: Mark an email as read
- `authenticate()`: Authenticate with the email service

### EmailMessage (Data Class)

Represents an email message with the following attributes:

- `id`: Unique email identifier
- `subject`: Email subject line
- `sender`: Sender email address
- `recipient`: Recipient email address
- `body`: Email body content
- `timestamp`: ISO format timestamp
- `is_read`: Read status
- `folder`: Folder location
- `attachments`: List of attachment metadata

### Exception Classes

- `EmailClientError`: Base exception for email client operations
- `AuthenticationError`: Raised when authentication fails

## Usage Example

```python
from email_client_api import EmailClient, EmailMessage

# Any implementation of EmailClient can be used here
def process_emails(client: EmailClient) -> None:
    """Process emails using any email client implementation."""
    
    # Authenticate with the service
    if not client.authenticate():
        raise RuntimeError("Authentication failed")
    
    # Retrieve recent emails
    emails = client.retrieve_emails(folder="INBOX", limit=5)
    
    for email in emails:
        print(f"From: {email.sender}")
        print(f"Subject: {email.subject}")
        
        # Mark as read
        if not email.is_read:
            client.mark_as_read(email.id)
    
    # Send a response email
    client.send_email(
        recipient="user@example.com",
        subject="Re: Your inquiry",
        body="Thank you for your message."
    )
```

## Interface Contract

All implementations must:

1. **Return Types**: Follow the exact return types specified in the interface
2. **Error Handling**: Raise appropriate exceptions for error conditions
3. **Authentication**: Implement proper authentication before operations
4. **Data Format**: Use the EmailMessage class for consistent data representation

## Testing

The interface includes comprehensive tests to validate implementations:

```python
# Run tests for this component
pytest src/email_client_api/tests/
```

## Implementation Guidelines

When implementing this interface:

1. **Authentication**: Always verify authentication before performing operations
2. **Error Handling**: Use the provided exception classes consistently  
3. **Rate Limiting**: Implement appropriate rate limiting for API calls
4. **Logging**: Include proper logging for debugging and monitoring
5. **Security**: Never log sensitive information like passwords or tokens

## Related Components

- **Gmail Client Implementation**: Concrete implementation using Gmail API
- **Email Analytics**: Analytics component that operates on this interface 