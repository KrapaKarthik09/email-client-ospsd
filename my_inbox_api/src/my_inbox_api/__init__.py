from typing import Iterator, Protocol, List


class Attachment(Protocol):
    """An email attachment."""

    @property
    def filename(self) -> str:
        """Return the filename of the attachment."""
        raise NotImplementedError()

    @property
    def content_type(self) -> str:
        """Return the content type of the attachment."""
        raise NotImplementedError()

    @property
    def size(self) -> int:
        """Return the size of the attachment in bytes."""
        raise NotImplementedError()

    def get_content(self) -> bytes:
        """Return the content of the attachment."""
        raise NotImplementedError()


class Message(Protocol):
    """An Email Message."""

    @property
    def id(self) -> str:
        """Return the unique identifier of the message."""
        raise NotImplementedError()

    @property
    def from_(self) -> str:
        """Return the sender of the message."""
        raise NotImplementedError()

    @property
    def to(self) -> str:
        """Return the recipient of the message."""
        raise NotImplementedError()

    @property
    def cc(self) -> str | None:
        """Return the CC recipients of the message, if any."""
        raise NotImplementedError()

    @property
    def bcc(self) -> str | None:
        """Return the BCC recipients of the message, if any."""
        raise NotImplementedError()

    @property
    def date(self) -> str:
        """Return the date of the message."""
        raise NotImplementedError()

    @property
    def subject(self) -> str:
        """Return the subject of the message."""
        raise NotImplementedError()

    @property
    def body(self) -> str:
        """Return the body of the message."""
        raise NotImplementedError()

    @property
    def attachments(self) -> List[Attachment]:
        """Return a list of attachments."""
        raise NotImplementedError()

    @property
    def is_read(self) -> bool:
        """Return whether the message has been read."""
        raise NotImplementedError()

    def mark_as_read(self) -> None:
        """Mark the message as read."""
        raise NotImplementedError()

    def mark_as_unread(self) -> None:
        """Mark the message as unread."""
        raise NotImplementedError()


class Client(Protocol):
    """A Mail Client used to fetch and manage messages."""

    def get_messages(
        self, limit: int | None = None, folder: str = "INBOX"
    ) -> Iterator[Message]:
        """Return an iterator of messages.

        Args:
            limit: Maximum number of messages to retrieve. If None, retrieves all available messages.
            folder: The folder to fetch messages from. Defaults to "INBOX".

        Returns:
            An iterator of Message objects.
        """
        raise NotImplementedError()

    def search_messages(self, query: str, folder: str = "INBOX") -> Iterator[Message]:
        """Search for messages that match the query.

        Args:
            query: The search query string.
            folder: The folder to search in. Defaults to "INBOX".

        Returns:
            An iterator of Message objects that match the query.
        """
        raise NotImplementedError()

    def get_folders(self) -> List[str]:
        """Return a list of available mail folders.

        Returns:
            A list of folder names.
        """
        raise NotImplementedError()


def get_client() -> Client:
    """Return an instance of a Mail Client.

    This function will be overridden by the implementation module.

    Returns:
        An instance of a Client implementation.
    """
    raise NotImplementedError()
