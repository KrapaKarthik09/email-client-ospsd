from my_inbox_impl import get_client
from my_inbox_impl.mail_fetcher import MockFetcher

# Get client instance
client = get_client()

# Create a mock fetcher and generate some test messages
fetcher = MockFetcher()
fetcher.set_client(client)
fetcher.fetch_messages(count=15)

# List folders
print("\nAvailable folders:")
for folder in client.get_folders():
    print(f"  - {folder}")

# List messages in inbox
print("\nMessages in INBOX:")
for idx, message in enumerate(client.get_messages(folder="INBOX", limit=5), 1):
    print(f"{idx}. From: {message.from_}")
    print(f"   Subject: {message.subject}")
    print(f"   Date: {message.date}")
    print(f"   Read: {message.is_read}")
    print("-" * 50)

# Search for messages
search_term = "important"
print(f"\nSearching for '{search_term}':")
for message in client.search_messages(search_term):
    print(f"  Match: {message.subject}")

# Test read/unread functionality
if list(client.get_messages()):
    message = next(client.get_messages())
    print(f"\nTesting read/unread status for message: {message.subject}")
    print(f"  Initially read: {message.is_read}")
    message.mark_as_read()
    print(f"  After marking read: {message.is_read}")
    message.mark_as_unread()
    print(f"  After marking unread: {message.is_read}")

# Test message with attachments
for message in client.get_messages():
    if message.attachments:
        print(f"\nMessage with attachments: {message.subject}")
        for idx, attachment in enumerate(message.attachments, 1):
            print(
                f"  Attachment {idx}: {attachment.filename} ({attachment.content_type})"
            )
            print(f"  Size: {attachment.size} bytes")
        break
