#!/usr/bin/env python3
"""
Example usage of the Email Client OSPSD library.

This script demonstrates how to use the Email Client OSPSD library
to interact with Gmail.
"""

import os
import sys
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

# Import the client factory and types
from email_client_api import get_client, EmailMessage

# Load environment variables from .env file (if it exists)
load_dotenv()


def main():
    """Run the email client example."""
    # Optional: Get credentials file location from environment variable
    # Otherwise, defaults to 'credentials.json' in current directory
    credentials_file = os.environ.get("GMAIL_CREDENTIALS", "credentials.json")
    
    print("=== Email Client OSPSD Example ===")
    
    # Get a client instance with Gmail implementation
    client = get_client(provider="gmail", credentials_file=credentials_file)
    
    # Authenticate (will open browser for OAuth2 flow if needed)
    print("\nAuthenticating with Gmail...")
    try:
        client.authenticate()
        print("Authentication successful!")
    except Exception as e:
        print(f"Authentication failed: {e}")
        return
    
    # Display available folders/labels
    print("\nFetching available folders/labels...")
    try:
        folders = client.get_folders()
        print(f"Found {len(folders)} folders/labels:")
        for folder in folders[:10]:  # Show only first 10
            print(f"  - {folder}")
        if len(folders) > 10:
            print(f"  ... and {len(folders) - 10} more")
    except Exception as e:
        print(f"Error fetching folders: {e}")
    
    # Retrieve messages from inbox
    print("\nFetching messages from INBOX...")
    try:
        messages = list(client.get_messages(folder="INBOX", limit=5))
        print(f"Found {len(messages)} messages")
        
        # Display message details
        for i, message in enumerate(messages, 1):
            print(f"\nMessage {i}:")
            print(f"  From: {message.sender}")
            print(f"  Subject: {message.subject}")
            print(f"  Date: {message.timestamp}")
            print(f"  Read: {'Yes' if message.is_read else 'No'}")
            
            # Display truncated body
            body_preview = message.body[:100] + "..." if len(message.body) > 100 else message.body
            print(f"  Body preview: {body_preview}")
    except Exception as e:
        print(f"Error fetching messages: {e}")
    
    # Search for messages
    print("\nSearching for messages containing 'important'...")
    try:
        results = list(client.search_messages("important", folder="INBOX"))
        print(f"Found {len(results)} matching messages")
        
        for i, message in enumerate(results[:3], 1):  # Show only first 3
            print(f"  {i}. {message.subject}")
    except Exception as e:
        print(f"Error searching messages: {e}")
    
    print("\nExample completed.")


if __name__ == "__main__":
    main() 