# Gmail Client Implementation

This module provides a concrete implementation of the Email Client API using Google's Gmail API.

## Features

- **OAuth2 Authentication**: Secure authentication with Gmail using OAuth2
- **Email Operations**: Send, retrieve, delete, and manage emails
- **Folder Management**: Access and list Gmail labels
- **Search Functionality**: Search emails with Gmail's powerful search syntax
- **Message Parsing**: Convert Gmail API messages to standardized EmailMessage objects

## Prerequisites

Before using this module, you need to:

1. Create a Google Cloud Project
2. Enable the Gmail API
3. Create OAuth 2.0 credentials
4. Download the credentials JSON file

## Setup

### 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Navigate to "APIs & Services" > "Library"
4. Search for "Gmail API" and enable it

### 2. Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Desktop app" as the application type
4. Enter a name for your credentials
5. Click "Create" and download the JSON file
6. Save the file as `credentials.json` in your project directory

## Usage

### Basic Usage

```python
from gmail_client_impl import GmailClient

# Initialize the client
client = GmailClient(
    credentials_file="path/to/credentials.json",
    token_file="path/to/token.json",
)

# Authenticate (opens browser for first-time authentication)
client.authenticate()

# Send an email
client.send_email(
    recipient="recipient@example.com",
    subject="Test Email",
    body="Hello from the Gmail Client!",
)

# Retrieve emails from inbox
emails = client.retrieve_emails(folder="INBOX", limit=10)
for email in emails:
    print(f"Subject: {email.subject}, From: {email.sender}")

# Search for emails
for email in client.search_messages("important", folder="INBOX"):
    print(f"Found: {email.subject}")

# Delete an email
client.delete_email(email_id="message_id_here")

# Mark an email as read
client.mark_as_read(email_id="message_id_here")

# List folders/labels
folders = client.get_folders()
print("Available folders:", folders)
```

### Using the Factory Function

Alternatively, you can use the factory function from the email_client_api module:

```python
from email_client_api import get_client

# Get a Gmail client
client = get_client(
    provider="gmail", 
    credentials_file="path/to/credentials.json",
)

# Use the client as before
client.authenticate()
```

## API Reference

### Constructor

```python
GmailClient(
    credentials_file: str = "credentials.json",
    token_file: str = "token.json",
    scopes: Optional[list[str]] = None,
)
```

- `credentials_file`: Path to the OAuth 2.0 credentials JSON file
- `token_file`: Path to store the access token
- `scopes`: List of Gmail API scopes (uses default scopes if None)

### Methods

#### `authenticate() -> bool`

Authenticates with the Gmail API. Opens a browser window for the first authentication.

#### `send_email(recipient: str, subject: str, body: str) -> bool`

Sends an email to the specified recipient.

#### `retrieve_emails(folder: str = "INBOX", limit: int = 10) -> list[EmailMessage]`

Retrieves emails from the specified folder.

#### `delete_email(email_id: str) -> bool`

Deletes an email by its ID.

#### `mark_as_read(email_id: str) -> bool`

Marks an email as read.

#### `search_messages(query: str, folder: str = "INBOX") -> Iterator[EmailMessage]`

Searches for messages matching the query in the specified folder.

#### `get_folders() -> list[str]`

Gets all available folders/labels.

## Error Handling

The module raises two main types of exceptions:

- `AuthenticationError`: When authentication fails
- `EmailClientError`: When email operations fail

Always wrap API calls in try-except blocks to handle these exceptions gracefully.

## Limitations

- Attachment handling is limited to metadata only
- HTML emails are converted to plain text
- OAuth2 authentication requires a web browser for the first authentication

## License

This module is part of the Email Client OSPSD project and is licensed under the MIT License.
