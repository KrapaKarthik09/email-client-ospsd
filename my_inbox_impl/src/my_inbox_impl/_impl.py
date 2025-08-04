from typing import Dict, Iterator, List
import my_inbox_api
import datetime
import uuid
import os
import json
from pathlib import Path


class AttachmentImpl:
    """Implementation of the Attachment protocol."""

    def __init__(self, filename: str, content_type: str, content: bytes) -> None:
        self._filename = filename
        self._content_type = content_type
        self._content = content

    @property
    def filename(self) -> str:
        return self._filename

    @property
    def content_type(self) -> str:
        return self._content_type

    @property
    def size(self) -> int:
        return len(self._content)

    def get_content(self) -> bytes:
        return self._content


class MessageImpl:
    """Implementation of the Message protocol."""

    def __init__(
        self,
        _id: str,
        _from: str,
        _to: str,
        _subject: str,
        _body: str,
        _date: str | None = None,
        _cc: str | None = None,
        _bcc: str | None = None,
        _attachments: List[AttachmentImpl] | None = None,
        _is_read: bool = False,
    ) -> None:
        """Initialize the message with the given parameters.

        Args:
            _id: Unique identifier for the message
            _from: Sender of the message
            _to: Recipient of the message
            _subject: Subject line of the message
            _body: Body content of the message
            _date: Date of the message (defaults to current date if None)
            _cc: CC recipients (if any)
            _bcc: BCC recipients (if any)
            _attachments: List of attachments (if any)
            _is_read: Whether the message has been read
        """
        self._id = _id
        self._from = _from
        self._to = _to
        self._subject = _subject
        self._body = _body
        self._date = _date
        self._cc = _cc
        self._bcc = _bcc
        self._attachments = _attachments if _attachments is not None else []
        self._is_read = _is_read

        # Initialize date if not provided
        if self._date is None:
            # Generate a date with proper timezone format
            self._date = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
            # If timezone formatting fails (empty %z), use alternative
            if self._date.endswith(" "):
                self._date = datetime.datetime.now().strftime(
                    "%a, %d %b %Y %H:%M:%S +0000"
                )

    @property
    def id(self) -> str:
        return self._id

    @property
    def from_(self) -> str:
        return self._from

    @property
    def to(self) -> str:
        return self._to

    @property
    def cc(self) -> str | None:
        return self._cc

    @property
    def bcc(self) -> str | None:
        return self._bcc

    @property
    def date(self) -> str:
        return self._date

    @property
    def subject(self) -> str:
        return self._subject

    @property
    def body(self) -> str:
        return self._body

    @property
    def attachments(self) -> List[my_inbox_api.Attachment]:
        return self._attachments

    @property
    def is_read(self) -> bool:
        return self._is_read

    def mark_as_read(self) -> None:
        self._is_read = True

    def mark_as_unread(self) -> None:
        self._is_read = False

    def to_dict(self) -> Dict:
        """Convert message to a dictionary for storage."""
        attachments = []
        for attachment in self._attachments:
            attachments.append(
                {
                    "filename": attachment.filename,
                    "content_type": attachment.content_type,
                    "content": attachment.get_content().hex(),  # Convert bytes to hex for storage
                }
            )

        return {
            "id": self._id,
            "from": self._from,
            "to": self._to,
            "cc": self._cc,
            "bcc": self._bcc,
            "date": self._date,
            "subject": self._subject,
            "body": self._body,
            "is_read": self._is_read,
            "attachments": attachments,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "MessageImpl":
        """Create a message instance from a dictionary representation.

        This method is used primarily for deserializing messages from storage.

        Args:
            data: A dictionary containing message data, typically loaded from JSON

        Returns:
            A new MessageImpl instance populated with the data from the dictionary
        """
        attachments = []
        for attachment_data in data.get("attachments", []):
            # Convert hex back to bytes
            content = bytes.fromhex(attachment_data["content"])
            attachment = AttachmentImpl(
                filename=attachment_data["filename"],
                content_type=attachment_data["content_type"],
                content=content,
            )
            attachments.append(attachment)

        return cls(
            _id=data["id"],
            _from=data["from"],
            _to=data["to"],
            _cc=data.get("cc"),
            _bcc=data.get("bcc"),
            _date=data["date"],
            _subject=data["subject"],
            _body=data["body"],
            _is_read=data["is_read"],
            _attachments=attachments,
        )


class ClientImpl:
    """Implementation of the Client protocol with local storage."""

    def __init__(self, data_dir: str | None = None) -> None:
        """Initialize the client with optional data directory.

        Args:
            data_dir: Directory to store email data. If None, uses './email_data'.
        """
        self._data_dir = data_dir or os.path.join(os.path.expanduser("~"), ".my_inbox")

        # Create data directory if it doesn't exist
        if not os.path.exists(self._data_dir):
            os.makedirs(self._data_dir)

        # Initialize default folders if they don't exist
        self._folders = ["INBOX", "Sent", "Drafts", "Trash", "Archive"]
        for folder in self._folders:
            folder_path = os.path.join(self._data_dir, folder)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

        # Load messages from disk or initialize empty dictionaries
        self._messages = self._load_messages()

    def _load_messages(self) -> Dict[str, List[MessageImpl]]:
        """Load messages from disk."""
        messages: Dict[str, List[MessageImpl]] = {}

        for folder in self._folders:
            messages[folder] = []
            folder_path = os.path.join(self._data_dir, folder)

            # Get all JSON files in the folder
            message_files = [
                f
                for f in os.listdir(folder_path)
                if f.endswith(".json") and os.path.isfile(os.path.join(folder_path, f))
            ]

            for filename in message_files:
                file_path = os.path.join(folder_path, filename)
                try:
                    with open(file_path, "r") as f:
                        message_data = json.load(f)
                        message = MessageImpl.from_dict(message_data)
                        messages[folder].append(message)
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error loading message from {file_path}: {e}")

        return messages

    def _save_message(self, message: MessageImpl, folder: str) -> None:
        """Save a message to disk."""
        folder_path = os.path.join(self._data_dir, folder)
        file_path = os.path.join(folder_path, f"{message.id}.json")

        with open(file_path, "w") as f:
            json.dump(message.to_dict(), f, indent=2)

    def get_messages(
        self, limit: int | None = None, folder: str = "INBOX"
    ) -> Iterator[my_inbox_api.Message]:
        """Return an iterator of messages from the specified folder."""
        # Make sure the folder exists
        if folder not in self._folders:
            raise ValueError(f"Folder '{folder}' does not exist")

        # Sort messages by date (newest first) with better error handling
        def safe_date_key(msg) -> datetime.datetime:
            """Parse message date to datetime for sorting, with timezone handling.

            Args:
                msg: The message containing a date string

            Returns:
                A datetime object for sorting purposes
            """
            try:
                # First try with timezone
                dt = datetime.datetime.strptime(msg.date, "%a, %d %b %Y %H:%M:%S %z")
                # Convert to UTC for consistent comparison
                return dt.astimezone(datetime.timezone.utc)
            except ValueError:
                try:
                    # Try common format with +0000 style timezone
                    dt = datetime.datetime.strptime(
                        msg.date, "%a, %d %b %Y %H:%M:%S +0000"
                    )
                    # Already UTC
                    return dt
                except ValueError:
                    try:
                        # Try without timezone
                        dt = datetime.datetime.strptime(
                            msg.date, "%a, %d %b %Y %H:%M:%S"
                        )
                        # Add UTC timezone to naive datetime
                        return dt.replace(tzinfo=datetime.timezone.utc)
                    except ValueError:
                        try:
                            # Try another common format
                            dt = datetime.datetime.strptime(
                                msg.date, "%d %b %Y %H:%M:%S %z"
                            )
                            return dt.astimezone(datetime.timezone.utc)
                        except ValueError:
                            # Fallback to today's date with UTC timezone
                            return datetime.datetime.now(datetime.timezone.utc)

        sorted_messages = sorted(
            self._messages.get(folder, []), key=safe_date_key, reverse=True
        )

        # Apply limit if specified
        if limit is not None:
            sorted_messages = sorted_messages[:limit]

        for message in sorted_messages:
            yield message

    def search_messages(
        self, query: str, folder: str = "INBOX"
    ) -> Iterator[my_inbox_api.Message]:
        """Search for messages that match the query in the specified folder."""
        # Make sure the folder exists
        if folder not in self._folders:
            raise ValueError(f"Folder '{folder}' does not exist")

        # Simple case-insensitive search in subject and body
        query = query.lower()
        for message in self._messages.get(folder, []):
            if (
                query in message.subject.lower()
                or query in message.body.lower()
                or query in message.from_.lower()
                or query in message.to.lower()
                or message.id.lower() == query.lower()
            ):  # Added direct ID matching
                yield message

    def get_folders(self) -> List[str]:
        """Return a list of available mail folders."""
        return self._folders

    def add_message(self, message: MessageImpl, folder: str = "INBOX") -> None:
        """Add a new message to the specified folder."""
        # Make sure the folder exists
        if folder not in self._folders:
            raise ValueError(f"Folder '{folder}' does not exist")

        # Add the message to the in-memory store
        if folder not in self._messages:
            self._messages[folder] = []
        self._messages[folder].append(message)

        # Save the message to disk
        self._save_message(message, folder)

    def create_folder(self, folder_name: str) -> None:
        """Create a new folder.

        Args:
            folder_name: Name of the folder to create

        Raises:
            ValueError: If the folder already exists
        """
        if folder_name in self._folders:
            raise ValueError(f"Folder '{folder_name}' already exists")

        # Create folder directory
        folder_path = os.path.join(self._data_dir, folder_name)
        os.makedirs(folder_path)

        # Add to list of folders
        self._folders.append(folder_name)
        self._messages[folder_name] = []

    def delete_message(self, message_id: str, folder: str) -> bool:
        """Delete a message from the specified folder.

        If the folder is not 'Trash', the message is moved to the Trash folder
        instead of being permanently deleted. Messages in the Trash folder are
        permanently deleted.

        Args:
            message_id: ID of the message to delete
            folder: Folder containing the message

        Returns:
            True if the message was deleted or moved, False if not found
        """
        # Make sure the folder exists
        if folder not in self._folders:
            raise ValueError(f"Folder '{folder}' does not exist")

        # If not in Trash folder, move to Trash instead of deleting
        if folder != "Trash":
            return self.move_message(message_id, folder, "Trash")

        # Find and remove the message
        for i, message in enumerate(self._messages.get(folder, [])):
            if message.id == message_id:
                # Remove from in-memory store
                del self._messages[folder][i]

                # Remove from disk
                file_path = os.path.join(self._data_dir, folder, f"{message_id}.json")
                if os.path.exists(file_path):
                    os.remove(file_path)

                return True

        return False

    def move_message(
        self, message_id: str, source_folder: str, target_folder: str
    ) -> bool:
        """Move a message from one folder to another.

        Args:
            message_id: ID of the message to move
            source_folder: Current folder of the message
            target_folder: Destination folder

        Returns:
            True if the message was moved, False if not found

        Raises:
            ValueError: If either source or target folder doesn't exist
        """
        # Make sure the folders exist
        if source_folder not in self._folders:
            raise ValueError(f"Source folder '{source_folder}' does not exist")
        if target_folder not in self._folders:
            raise ValueError(f"Target folder '{target_folder}' does not exist")

        # Find the message
        for i, message in enumerate(self._messages.get(source_folder, [])):
            if message.id == message_id:
                # Remove from source folder
                message = self._messages[source_folder].pop(i)

                # Add to target folder
                if target_folder not in self._messages:
                    self._messages[target_folder] = []
                self._messages[target_folder].append(message)

                # Update on disk
                source_path = os.path.join(
                    self._data_dir, source_folder, f"{message_id}.json"
                )
                target_path = os.path.join(
                    self._data_dir, target_folder, f"{message_id}.json"
                )

                if os.path.exists(source_path):
                    os.rename(source_path, target_path)
                else:
                    # If file doesn't exist, just save it to the target folder
                    self._save_message(message, target_folder)

                return True

        return False


# Factory function to create and return a client
def get_client() -> my_inbox_api.Client:
    """Return an instance of a Mail Client."""
    return ClientImpl()
