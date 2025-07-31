# Gmail Client Implementation

This component provides a concrete implementation of the EmailClient interface using Google's Gmail API. It demonstrates how to create a production-ready email client that adheres to the defined interface contract.

## Overview

The Gmail Client Implementation (`GmailClient`) is a concrete implementation of the abstract `EmailClient` interface. It provides full functionality for:

- OAuth 2.0 authentication with Gmail
- Sending emails through Gmail API
- Retrieving emails from Gmail folders/labels
- Deleting emails
- Marking emails as read/unread
- Proper error handling and logging

## Features

### Authentication
- **OAuth 2.0 Flow**: Secure authentication using Google's OAuth 2.0
- **Token Management**: Automatic token refresh and storage
- **Credentials Security**: Secure handling of sensitive authentication data

### Email Operations
- **Send Email**: Compose and send emails with proper MIME formatting
- **Retrieve Emails**: Fetch emails from any Gmail folder/label
- **Delete Emails**: Permanently delete emails from Gmail
- **Mark as Read**: Update email read status

### Error Handling
- **Robust Error Handling**: Comprehensive exception handling for API errors
- **Logging**: Detailed logging for debugging and monitoring
- **Graceful Degradation**: Proper fallback behavior for failed operations

## Setup Instructions

### 1. Gmail API Credentials

Follow these steps to set up Gmail API access:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Gmail API" and click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop application"
   - Download the credentials JSON file
5. Save the credentials file as `credentials.json` in your project root

### 2. Required Scopes

The implementation requires these Gmail API scopes:
- `https://www.googleapis.com/auth/gmail.readonly` - Read emails
- `https://www.googleapis.com/auth/gmail.send` - Send emails
- `https://www.googleapis.com/auth/gmail.modify` - Modify email labels

### 3. Environment Setup

Create a `.env` file with your configuration:

```bash
GMAIL_CLIENT_ID=your_client_id_here
GMAIL_CLIENT_SECRET=your_client_secret_here
GMAIL_PROJECT_ID=your_project_id_here
GMAIL_REDIRECT_URI=http://localhost:8080
```

## Usage Example

```python
from gmail_client_impl import GmailClient

# Initialize the Gmail client
client = GmailClient(
    credentials_file="credentials.json",
    token_file="token.json"
)

# Authenticate with Gmail
if client.authenticate():
    print("Authentication successful!")
    
    # Send an email
    success = client.send_email(
        recipient="friend@example.com",
        subject="Hello from Gmail API",
        body="This email was sent using the Gmail API implementation!"
    )
    
    if success:
        print("Email sent successfully!")
    
    # Retrieve recent emails
    emails = client.retrieve_emails(folder="INBOX", limit=5)
    
    for email in emails:
        print(f"From: {email.sender}")
        print(f"Subject: {email.subject}")
        print(f"Date: {email.timestamp}")
        print(f"Read: {email.is_read}")
        print("---")
        
        # Mark unread emails as read
        if not email.is_read:
            client.mark_as_read(email.id)
            print(f"Marked email {email.id} as read")

else:
    print("Authentication failed!")
```

## Advanced Usage

### Custom Scopes

```python
from gmail_client_impl import GmailClient

# Initialize with custom scopes
custom_scopes = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send"
]

client = GmailClient(
    credentials_file="my_credentials.json",
    token_file="my_token.json", 
    scopes=custom_scopes
)
```

### Error Handling

```python
from gmail_client_impl import GmailClient
from email_client_api import AuthenticationError, EmailClientError

client = GmailClient()

try:
    client.authenticate()
    emails = client.retrieve_emails()
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except EmailClientError as e:
    print(f"Email operation failed: {e}")
```

## Testing

Run the component tests:

```bash
# Run all tests
pytest src/gmail_client_impl/tests/

# Run with coverage
pytest --cov=gmail_client_impl src/gmail_client_impl/tests/

# Run specific test file
pytest src/gmail_client_impl/tests/test_gmail.py
```

## Architecture Notes

### Design Patterns
- **Strategy Pattern**: Implements the EmailClient interface
- **Factory Pattern**: Credential and service creation
- **Template Method**: Consistent error handling across methods

### Security Considerations
- OAuth 2.0 tokens are stored securely
- No passwords or sensitive data in logs
- Proper token refresh mechanisms
- Secure credential file handling

### Performance Considerations
- Efficient message parsing
- Batch operations where possible
- Proper resource cleanup
- Rate limiting compliance

## Gmail API Specifics

### Labels vs Folders
Gmail uses labels instead of traditional folders:
- `INBOX` - Inbox messages
- `SENT` - Sent messages  
- `DRAFT` - Draft messages
- `SPAM` - Spam messages
- `TRASH` - Deleted messages

### Message IDs
Gmail message IDs are unique strings that remain constant throughout the message lifecycle.

### Rate Limits
The implementation respects Gmail API rate limits:
- 1 billion quota units per day
- 250 quota units per user per second

## Troubleshooting

### Common Issues

1. **"Credentials file not found"**
   - Ensure `credentials.json` exists in the specified path
   - Check file permissions

2. **"Authentication failed"**
   - Verify OAuth 2.0 credentials are correct
   - Check if Gmail API is enabled in Google Cloud Console
   - Ensure redirect URI matches the one in credentials

3. **"Insufficient permissions"**
   - Verify required scopes are included
   - Re-authenticate to grant new permissions

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

client = GmailClient()
# Now all operations will show detailed logs
```

## Related Components

- **Email Client API**: Abstract interface implemented by this component
- **Email Analytics**: Can analyze emails retrieved by this component 