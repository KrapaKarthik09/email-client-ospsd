#!/usr/bin/env python3
"""
Example usage of the Email Client OSPSD library.

This script demonstrates how to use the Email Client OSPSD library
to interact with Gmail.
"""

import logging
import os
import sys

from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

# Import the client factory and types
from email_client_api import EmailMessage, get_client

# Constants
MAX_FOLDERS_DISPLAY = 10
MAX_BODY_PREVIEW = 100
MAX_SEARCH_RESULTS_DISPLAY = 3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file (if it exists)
load_dotenv()


def main():
    """Run the email client example."""
    # Optional: Get credentials file location from environment variable
    # Otherwise, defaults to 'credentials.json' in current directory
    credentials_file = os.environ.get("GMAIL_CREDENTIALS", "credentials.json")

    logger.info("=== Email Client OSPSD Example ===")

    # Get a client instance with Gmail implementation
    client = get_client(provider="gmail", credentials_file=credentials_file)

    # Authenticate (will open browser for OAuth2 flow if needed)
    logger.info("Authenticating with Gmail...")
    try:
        client.authenticate()
        logger.info("Authentication successful!")
    except Exception as e:
        logger.error("Authentication failed: %s", e)
        return

    # Display available folders/labels
    logger.info("Fetching available folders/labels...")
    try:
        folders = client.get_folders()
        logger.info("Found %d folders/labels:", len(folders))
        for folder in folders[:MAX_FOLDERS_DISPLAY]:  # Show only first few
            logger.info("  - %s", folder)
        if len(folders) > MAX_FOLDERS_DISPLAY:
            logger.info("  ... and %d more", len(folders) - MAX_FOLDERS_DISPLAY)
    except Exception as e:
        logger.error("Error fetching folders: %s", e)

    # Retrieve messages from inbox
    logger.info("Fetching messages from INBOX...")
    try:
        messages = list(client.get_messages(folder="INBOX", limit=5))
        logger.info("Found %d messages", len(messages))

        # Display message details
        for i, message in enumerate(messages, 1):
            logger.info("Message %d:", i)
            logger.info("  From: %s", message.sender)
            logger.info("  Subject: %s", message.subject)
            logger.info("  Date: %s", message.timestamp)
            logger.info("  Read: %s", "Yes" if message.is_read else "No")

            # Display truncated body
            body_preview = (
                message.body[:MAX_BODY_PREVIEW] + "..."
                if len(message.body) > MAX_BODY_PREVIEW
                else message.body
            )
            logger.info("  Body preview: %s", body_preview)
    except Exception as e:
        logger.error("Error fetching messages: %s", e)

    # Search for messages
    logger.info("Searching for messages containing 'important'...")
    try:
        results = list(client.search_messages("important", folder="INBOX"))
        logger.info("Found %d matching messages", len(results))

        for i, message in enumerate(results[:MAX_SEARCH_RESULTS_DISPLAY], 1):
            logger.info("  %d. %s", i, message.subject)
    except Exception as e:
        logger.error("Error searching messages: %s", e)

    logger.info("Example completed.")


if __name__ == "__main__":
    main()
