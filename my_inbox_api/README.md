# My Inbox API

This module provides interface definitions for an email inbox client.

## Overview

The API defines protocols for:
- Email messages
- Message attachments
- Inbox client functionality

## Project Scope

### In Scope

- Basic email message retrieval
- Email folder/label support
- Message search functionality
- Attachment handling
- Message read/unread status management

### Out of Scope

- Message composition and sending
- Complex filtering rules
- Server-side folder management
- Account setup and configuration
- Security features beyond basic authentication

## Usage

The API provides protocols that must be implemented by concrete classes:

```python
import my_inbox_api

# Get a client instance (provided by an implementation)
client = my_inbox_api.get_client()

# List available folders
folders = client.get_folders()

# Get messages from inbox
for message in client.get_messages():
    print(f"From: {message.from_}")
    print(f"Subject: {message.subject}")
    print(f"Body: {message.body}")
