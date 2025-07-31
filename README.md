# Email Client OSPSD: Gmail Interface API

| Student Name: Krapa Karthik NET ID: kk5754

## Overview

Email Client OSPSD is a modular Python library providing a clean, standardized interface for email client operations. It implements a protocol-based approach for email handling with a Gmail implementation, developed as part of NYU's Open Source and Professional Software Development course.

## Project Structure

```
.
├── src/
│   ├── email_client_api/        # API protocol definitions
│   │   ├── tests/               # API tests
│   │   └── __init__.py          # Protocol interfaces
│   └── gmail_client_impl/       # Gmail implementation
│       ├── tests/               # Implementation tests
│       └── __init__.py          # Implementation classes
├── .circleci/                   # CI/CD configuration
├── .github/                     # GitHub templates
├── docs/                        # Documentation
├── tests/                       # Integration tests
├── pyproject.toml               # Project configuration
└── README.md                    # This file
```

## Features

- **Protocol-based design**: Clearly defined interfaces for messages, attachments, and client operations
- **Gmail integration**: Connect to Gmail via Google API
- **Folder management**: Access and manage email folders/labels
- **Message operations**: Retrieve, search, and manage message read/unread status
- **Attachment handling**: Access and manipulate email attachments
- **OAuth2 authentication**: Secure Gmail authentication
- **Local storage**: Messages cached locally for offline access

## Installation

1. **Prerequisites**:
   - Python 3.11 or higher
   - UV package manager

2. **Install UV** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install the package**:
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```

## Quick Start

### Basic Usage

```python
from email_client_api import get_client

# Get a client instance
client = get_client()

# List available folders
folders = client.get_folders()
print("Available folders:", folders)

# Get messages from inbox
for message in client.get_messages(folder="INBOX", limit=5):
    print(f"From: {message.from_}")
    print(f"Subject: {message.subject}")
    print(f"Read: {message.is_read}")
    print("-" * 50)

# Search for messages
results = client.search_messages("important", folder="INBOX")
for message in results:
    print(f"Found: {message.subject}")
```

### Gmail Setup

1. Create a Google Cloud Project and enable Gmail API
2. Download OAuth2 credentials JSON file
3. Set up authentication:

```python
from gmail_client_impl import GmailClient

# Initialize Gmail client
client = GmailClient(credentials_file="path/to/credentials.json")

# Authenticate (opens browser for first-time setup)
client.authenticate()

# Use the client
messages = list(client.get_messages(limit=10))
```

## API Reference

### Core Protocols

- **`Message`**: Email message with properties like `id`, `from_`, `subject`, `body`, `attachments`
- **`Attachment`**: File attachment with `filename`, `content_type`, `size`, and `get_content()`
- **`Client`**: Main interface with methods like `get_messages()`, `search_messages()`, `get_folders()`

### Key Methods

| Method | Parameters | Return Type | Description |
|--------|------------|-------------|-------------|
| `get_messages()` | `limit: int`, `folder: str` | `Iterator[Message]` | Fetch messages from folder |
| `search_messages()` | `query: str`, `folder: str` | `Iterator[Message]` | Search messages |
| `get_folders()` | None | `List[str]` | List available folders |

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run coverage run -m pytest
uv run coverage report
```

### Code Quality

```bash
# Linting
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .

# Type checking
uv run mypy src/
```

## CI/CD

This project uses CircleCI for continuous integration:

- **Linting**: Ruff code formatting and style checks
- **Type checking**: MyPy static type analysis  
- **Testing**: Pytest with coverage reporting (80% threshold)
- **Artifacts**: Test results and coverage reports

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Ensure all tests pass and coverage meets requirements
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Developed as part of NYU's Open Source and Professional Software Development course
- Thanks to all contributors and course instructors

