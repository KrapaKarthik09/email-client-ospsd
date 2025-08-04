#!/usr/bin/env python3
"""Example for using the IMAP fetcher with Gmail."""

import os
import sys
import time
import traceback
from pathlib import Path

# Add parent directory to sys.path if running as a script
if __name__ == "__main__":
    parent_dir = str(Path(__file__).resolve().parent.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

from my_inbox_impl import get_client
from my_inbox_impl.mail_fetcher import IMAPFetcher


def connect_to_gmail(username, password):
    """Connect to Gmail IMAP server.

    Args:
        username: Gmail username/email
        password: Gmail app password

    Returns:
        Tuple of (IMAPFetcher, ClientImpl)
    """
    # Gmail IMAP settings
    imap_host = "imap.gmail.com"
    imap_port = 993  # SSL port for IMAP

    print(f"\nConnecting to Gmail IMAP server ({imap_host}:{imap_port})...")

    # Create client
    client = get_client()

    # Create IMAP fetcher
    fetcher = IMAPFetcher(
        host=imap_host, port=imap_port, username=username, password=password
    )

    # Set client
    fetcher.set_client(client)

    return fetcher, client


def list_folders(fetcher):
    """List available folders on the Gmail server.

    Args:
        fetcher: IMAPFetcher instance

    Returns:
        List of folder names
    """
    print("\nFolders available on Gmail:")
    try:
        server_folders = fetcher.list_folders()
        if not server_folders:
            print("  No folders retrieved. This might be a connection issue.")
        else:
            for folder in server_folders:
                print(f"  - {folder}")
        return server_folders
    except Exception as e:
        print(f"  Error retrieving folders: {e}")
        # Default to standard INBOX
        return ["INBOX"]


def find_inbox_folder(server_folders):
    """Find a valid inbox folder from the list of server folders.

    Args:
        server_folders: List of folder names from the server

    Returns:
        Name of the inbox folder
    """
    # Find a valid inbox folder
    target_folder = "INBOX"
    valid_inbox_names = ["INBOX", "[Gmail]/INBOX", "Inbox", "inbox"]

    for folder_name in valid_inbox_names:
        if folder_name in server_folders:
            target_folder = folder_name
            break

    print(f"\nUsing folder: {target_folder}")
    return target_folder


def fetch_messages(fetcher, folder, limit):
    """Fetch messages from the specified folder.

    Args:
        fetcher: IMAPFetcher instance
        folder: Folder name to fetch from
        limit: Maximum number of messages to fetch

    Returns:
        List of fetched messages
    """
    print(f"\nFetching {limit} messages from {folder}...")
    start_time = time.time()
    fetched = fetcher.fetch_messages(folder=folder, limit=limit)
    end_time = time.time()

    print(f"Fetched {len(fetched)} messages in {end_time - start_time:.2f} seconds")
    return fetched


def display_messages(client, limit):
    """Display fetched messages from the client.

    Args:
        client: ClientImpl instance
        limit: Maximum number of messages to display

    Returns:
        List of messages
    """
    print("\nFetched messages:")
    fetched_messages = list(client.get_messages(folder="INBOX", limit=limit))

    if not fetched_messages:
        print("  No messages were successfully retrieved.")
        return []

    for idx, message in enumerate(fetched_messages, 1):
        print(f"{idx}. From: {message.from_}")
        print(f"   Subject: {message.subject}")
        print(f"   Date: {message.date}")
        print("-" * 50)

    return fetched_messages


def view_message_details(messages):
    """View details of a selected message.

    Args:
        messages: List of messages to choose from
    """
    if not messages:
        return

    msg_idx = input("\nEnter message number to view details (or press Enter to skip): ")
    if (
        not msg_idx
        or not msg_idx.isdigit()
        or int(msg_idx) < 1
        or int(msg_idx) > len(messages)
    ):
        return

    msg = messages[int(msg_idx) - 1]
    print("\n" + "=" * 60)
    print(f"ID: {msg.id}")
    print(f"From: {msg.from_}")
    print(f"To: {msg.to}")
    if msg.cc:
        print(f"CC: {msg.cc}")
    print(f"Date: {msg.date}")
    print(f"Subject: {msg.subject}")
    print("=" * 60)
    print("\nBody preview (first 200 chars):")
    print(f"{msg.body[:200]}...")

    if msg.attachments:
        print("\nAttachments:")
        for idx, attachment in enumerate(msg.attachments, 1):
            print(
                f"  {idx}. {attachment.filename} ({attachment.content_type}, {attachment.size} bytes)"
            )

    print("\n" + "=" * 60)


def main():
    """Execute the Gmail IMAP example."""
    # Gmail credentials
    username = os.environ.get("GMAIL_ADDRESS") or "prathamsaraf007@gmail.com"
    password = os.environ.get("GMAIL_APP_PASSWORD") or "twcf dzwz aqot dfnr"

    print(f"Using Gmail account: {username}")

    # Print initial client folders
    client = get_client()
    print("\nLocal client folders:")
    for folder in client.get_folders():
        print(f"  - {folder}")

    try:
        # Connect to Gmail
        fetcher, client = connect_to_gmail(username, password)

        # List folders and find inbox
        server_folders = list_folders(fetcher)
        target_folder = find_inbox_folder(server_folders)

        # Get number of messages to fetch
        limit = int(input("Number of messages to fetch (default: 5): ") or "5")

        try:
            # Fetch messages
            fetched = fetch_messages(fetcher, target_folder, limit)

            # Give system time to process
            print("Processing messages...")
            time.sleep(1)

            # Display messages and view details
            messages = display_messages(client, limit)
            view_message_details(messages)

        except Exception as e:
            print(f"Error fetching messages: {e}")
            traceback.print_exc()

        # Close the connection
        print("\nClosing connection...")
        fetcher.close()
        print("Done!")

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
