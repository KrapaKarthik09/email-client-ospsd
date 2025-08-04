# MyInbox: Email Interface API
this
## Overview

MyInbox is a modular Python library providing a clean, standardized interface for email client operations. It implements a protocol-based approach for email handling, allowing different backend implementations to share a common interface.

## Project Structure

```
.
├── my_inbox_api/            # API protocol definitions
│   ├── src/
│   │   └── my_inbox_api/    # Protocol interfaces
│   └── tests/               # API tests
├── my_inbox_impl/           # Reference implementation
│   ├── src/
│   │   └── my_inbox_impl/   # Implementation classes
│   ├── examples/            # Usage examples
│   └── tests/               # Implementation tests
├── .circleci/               # CI/CD configuration
├── .github/                 # GitHub templates
├── .gitignore               # Git ignore patterns
├── pyproject.toml           # Project configuration
└── README.md                # This file
```

## Features

- **Protocol-based design**: Clearly defined interfaces for messages, attachments, and client operations
- **Modular architecture**: Separates API from implementation for better maintainability
- **IMAP support**: Connect to email providers like Gmail via IMAP
- **Folder management**: Access and manage email folders/labels
- **Message operations**: Retrieve, search, and manage message read/unread status
- **Attachment handling**: Access and manipulate email attachments
- **Soft-delete**: Messages are moved to Trash instead of permanently deleted
- **Local storage**: Messages are stored locally for offline access

## Installation

1. **Prerequisites**:
   - Python 3.12 or higher
   - UV package manager

2. **Install UV** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install the package**:
   ```bash
   uv sync --all-packages
   ```

## API Protocols and Methods

### `Attachment` Protocol:

| Property       | Return Type | Description                           |
| :------------- | :---------- | :------------------------------------ |
| `filename`     | `str`       | The filename of the attachment        |
| `content_type` | `str`       | The content type of the attachment    |
| `size`         | `int`       | The size of the attachment in bytes   |
| `get_content()`| `bytes`     | Returns the content of the attachment |

### `Message` Protocol:

| Property/Method    | Return Type        | Description                                |
| :----------------- | :----------------- | :----------------------------------------- |
| `id`               | `str`              | The unique identifier of the message       |
| `from_`            | `str`              | The sender of the message                  |
| `to`               | `str`              | The recipient of the message               |
| `cc`               | `str | None`       | The CC recipients (if any)                 |
| `bcc`              | `str | None`       | The BCC recipients (if any)                |
| `date`             | `str`              | The date of the message                    |
| `subject`          | `str`              | The subject of the message                 |
| `body`             | `str`              | The body of the message                    |
| `attachments`      | `List[Attachment]` | A list of attachments                      |
| `is_read`          | `bool`             | Whether the message has been read          |
| `mark_as_read()`   | `None`             | Marks the message as read                  |
| `mark_as_unread()` | `None`             | Marks the message as unread                |

### `Client` Protocol:

| Method                             | Parameters                               | Return Type         | Description                                     |
| :--------------------------------- | :--------------------------------------- | :------------------ | :---------------------------------------------- |
| `get_messages(limit, folder)`      | `limit: int | None`, `folder: str`       | `Iterator[Message]` | Fetches messages from a specified folder        |
| `search_messages(query, folder)`   | `query: str`, `folder: str`              | `Iterator[Message]` | Searches for messages matching the query        |
| `get_folders()`                    | None                                     | `List[str]`         | Returns a list of available mail folders        |

### Helper Function:

| Function      | Return Type | Description                                    |
| :------------ | :---------- | :----------------------------------------------|
| `get_client()`| `Client`    | Returns an instance of a mail client implementation |

## Usage Examples

### Basic Usage

```python
import my_inbox_api

# Get a client instance
client = my_inbox_api.get_client()

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

### Gmail Integration

The library includes examples for connecting to Gmail using IMAP:

```python
from my_inbox_impl import get_client
from my_inbox_impl.mail_fetcher import IMAPFetcher

# Create client
client = get_client()

# Connect to Gmail
fetcher = IMAPFetcher(
    host="imap.gmail.com",
    port=993,
    username="your-email@gmail.com",
    password="your-app-password"  # Generate this in Gmail account settings
)

# Set client
fetcher.set_client(client)

# Fetch messages
fetched = fetcher.fetch_messages(folder="INBOX", limit=10)
print(f"Fetched {len(fetched)} messages")

# Display messages
for idx, message in enumerate(client.get_messages(limit=10), 1):
    print(f"{idx}. From: {message.from_}")
    print(f"   Subject: {message.subject}")
```

Check the `examples/` directory for more comprehensive examples.

## Development

### Running Tests

Use pytest to run the test suite:

```bash
uv run pytest
```

Run tests with coverage:

```bash
uv run coverage run -m pytest
uv run coverage report
```

### Code Quality

Run linting with Ruff:

```bash
uv run ruff check .
```

Apply auto-fixes where possible:

```bash
uv run ruff check --fix .
```

## CI/CD

This project uses CircleCI for continuous integration. The pipeline:

1. Installs dependencies
2. Runs linting with Ruff
3. Runs all tests with pytest
4. Generates code coverage reports

## Contributing

Contributions are welcome! Follow these steps:

1. Check the issue tracker for open issues or create a new one
2. Fork the repository
3. Create a new branch for your feature or bugfix
4. Write tests for your changes
5. Make your changes
6. Run the tests and linting to ensure everything passes
7. Submit a pull request

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- This project was developed as part of a collaborative effort at NYU OSSPD
- Thanks to all the contributors who have helped improve this codebase
