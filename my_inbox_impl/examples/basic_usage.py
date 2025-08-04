#!/usr/bin/env python3
"""Example script demonstrating basic usage of the my_inbox_impl package."""

import os
import sys
import argparse
from pathlib import Path

# Add parent directory to sys.path if running as a script
if __name__ == "__main__":
    parent_dir = str(Path(__file__).resolve().parent.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

from my_inbox_impl import get_client
from my_inbox_impl.mail_fetcher import MockFetcher


def list_folders(client):
    """List all available folders."""
    folders = client.get_folders()
    print("\nAvailable folders:")
    for folder in folders:
        print(f"  - {folder}")
    print()


def list_messages(client, folder="INBOX", limit=10):
    """List messages in the specified folder."""
    print(f"\nMessages in {folder}:")
    print("-" * 60)

    messages = list(client.get_messages(folder=folder, limit=limit))

    if not messages:
        print("No messages found.")
        return

    for idx, message in enumerate(messages, 1):
        read_status = "Read" if message.is_read else "Unread"
        attachment_count = len(message.attachments)
        attachment_info = (
            f" [{attachment_count} attachments]" if attachment_count > 0 else ""
        )

        print(f"{idx}. [{read_status}] From: {message.from_}")
        print(f"   Subject: {message.subject}{attachment_info}")
        print(f"   Date: {message.date}")
        print(f"   ID: {message.id}")
        print("-" * 60)


def view_message(client, message_id, folder="INBOX"):
    """View the content of a specific message.

    Args:
        client: Email client instance
        message_id: ID of the message to view
        folder: Folder containing the message (default: INBOX)
    """
    # Search for message by ID (optimize by using ID-based search)
    search_results = list(client.search_messages(message_id, folder))

    if not search_results:
        print(f"Message with ID {message_id} not found in {folder}")
        return

    # Get the first matching message
    message = search_results[0]

    # Mark as read
    message.mark_as_read()

    # Display message
    print("\n" + "=" * 60)
    print(f"From: {message.from_}")
    print(f"To: {message.to}")
    if message.cc:
        print(f"CC: {message.cc}")
    print(f"Date: {message.date}")
    print(f"Subject: {message.subject}")
    print("=" * 60)
    print(f"\n{message.body}\n")

    # Show attachments if any
    if message.attachments:
        print("\nAttachments:")
        for idx, attachment in enumerate(message.attachments, 1):
            print(
                f"  {idx}. {attachment.filename} ({attachment.content_type}, {attachment.size} bytes)"
            )

    print("\n" + "=" * 60)


def search_messages(client, query, folder="INBOX"):
    """Search for messages matching the query."""
    print(f"\nSearch results for '{query}' in {folder}:")
    print("-" * 60)

    results = list(client.search_messages(query, folder))

    if not results:
        print("No matching messages found.")
        return

    for idx, message in enumerate(results, 1):
        read_status = "Read" if message.is_read else "Unread"
        print(f"{idx}. [{read_status}] From: {message.from_}")
        print(f"   Subject: {message.subject}")
        print(f"   Date: {message.date}")
        print(f"   ID: {message.id}")
        print("-" * 60)


def populate_mock_data(client, count=20):
    """Add mock messages to the client for testing."""
    print(f"\nGenerating {count} mock messages...")

    # Create a mock fetcher
    fetcher = MockFetcher()
    fetcher.set_client(client)

    # Generate mock messages
    messages = fetcher.fetch_messages(count=count)

    print(f"Added {len(messages)} mock messages to INBOX")

    # Add some messages to other folders
    folders = ["Sent", "Drafts", "Archive"]
    for folder in folders:
        folder_count = count // 4  # Add fewer messages to other folders
        folder_messages = fetcher.fetch_messages(folder=folder, count=folder_count)
        print(f"Added {len(folder_messages)} mock messages to {folder}")


def main():
    """Demonstrate the email client functionality."""
    parser = argparse.ArgumentParser(description="Email Client Demo")
    parser.add_argument("--populate", type=int, help="Populate with N mock messages")
    parser.add_argument("--list", action="store_true", help="List messages")
    parser.add_argument("--folder", default="INBOX", help="Folder to use")
    parser.add_argument(
        "--limit", type=int, default=10, help="Limit number of messages"
    )
    parser.add_argument("--search", help="Search for messages")
    parser.add_argument("--view", help="View message by ID")

    args = parser.parse_args()

    # Get client instance
    client = get_client()

    # List folders
    list_folders(client)

    # Populate with mock data if requested
    if args.populate:
        populate_mock_data(client, args.populate)

    # List messages if requested
    if args.list:
        list_messages(client, args.folder, args.limit)

    # Search messages if requested
    if args.search:
        search_messages(client, args.search, args.folder)

    # View message if requested
    if args.view:
        view_message(client, args.view, args.folder)


if __name__ == "__main__":
    main()
