# Python Poe API

[![PyPi Version](https://img.shields.io/pypi/v/poe-api.svg)](https://pypi.org/project/poe-api/)

This is a reverse engineered API wrapper for Quora's Poe, which allows you free access to OpenAI's ChatGPT and GPT-4, as well as Antropic's Claude.

## Table of Contents:
- [Features](#features)
- [Installation](#installation)
- [Documentation](#documentation)
  * [Using the Client](#using-the-client)
    + [Downloading the Available Bots](#downloading-the-available-bots)
    + [Sending Messages](#sending-messages)
    + [Clearing the Conversation Context](#clearing-the-conversation-context)
    + [Downloading Conversation History](#downloading-conversation-history)
    + [Deleting Messages](#deleting-messages)
    + [Purging a Conversation](#purging-a-conversation)
  * [Misc](#misc)
    + [Changing the Logging Level](#changing-the-logging-level)
    + [Setting a Custom User-Agent](#setting-a-custom-user-agent)
- [Copyright](#copyright)

*Table of contents generated with [markdown-toc](http://ecotrust-canada.github.io/markdown-toc).*

## Features:
 - Log in with token
 - Download bot list
 - Send messages
 - Stream bot responses
 - Clear conversation context
 - Download conversation history
 - Delete messages
 - Purge an entire conversation

## Installation:
You can install this library by running the following command:
```
pip3 install poe-api
```

## Documentation:
Examples can be found in the `/examples` directory. To run these examples, pass in your token as a command-line argument.
```
python3 examples/temporary_message.py "TOKEN_HERE"
```

### Using the Client:
To use this library, simply import `poe` and create a `poe.Client` instance, passing in your token as the only argument. You can find your token in the `p-b` field in your browser's cookies. 

```python
import poe
client = poe.Client("TOKEN_HERE")
```

Note that the following examples assume `client` is the name of your `poe.Client` instance. If the token is invalid, a RuntimeError will be raised.

#### Downloading the Available Bots:
The client downloads all of the available bots upon initialization and stores them within `poe.Client.bots`. A dictionary that maps bot codenames to their display names can be found at `poe.Client.bot_names`. If you want to refresh these values, you can call `poe.Client.get_bots`.

```python
print(client.bot_names)
#{'capybara': 'Sage', 'beaver': 'GPT-4', 'a2_2': 'Claude+', 'a2': 'Claude', 'chinchilla': 'ChatGPT', 'nutria': 'Dragonfly'}
```

#### Sending Messages:
You can use the `poe.Client.send_message` function to send a message to a chatbot, which accepts the following arguments:
 - `chatbot` - The codename of the chatbot. (example: `capybara`)
 - `message` - The message to send to the chatbot.
 - `with_chat_break = False` - Whether the conversation context should be cleared.

The function is a generator which returns the most recent version of the generated message whenever it is updated.

Streamed Example:
```python
message = "Summarize the GNU GPL v3"
for chunk in client.send_message("capybara", message):
  print(chunk["text_new"], end="", flush=True)
```

Non-Streamed Example:
```python
message = "Summarize the GNU GPL v3"
for chunk in client.send_message("capybara", message):
  pass
print(chunk["text"])
```

You can also send multiple messages in parallel using `threading` and recieve their responses seperately, as demonstrated in `/examples/parallel_messages.py`.

#### Clearing the Conversation Context:
If you want to clear the the context of a conversation without sending a message, you can use `client.send_chat_break`. The only argument is the codename of the bot whose context will be cleared.

```python
client.send_chat_break("capybara")
```
The function returns the message which represents the chat break.

#### Downloading Conversation History:
To download past messages in a conversation, use the `client.get_message_history` function, which accepts the following arguments:
 - `chatbot` - The codename of the chatbot.
 - `count = 25` - The number of messages to download.
 - `cursor = None` - The message ID to start at instead of the latest one.

```python
message_history = client.get_message_history("capybara", count=10)
print(json.dumps(message_history, indent=2))
"""
[
  {
    "node": {
      "id": "TWVzc2FnZToxMDEwNzYyODU=",
      "messageId": 101076285,
      "creationTime": 1679298157718888,
      "text": "",
      "author": "chat_break",
      "linkifiedText": "",
      "state": "complete",
      "suggestedReplies": [],
      "vote": null,
      "voteReason": null,
      "__typename": "Message"
    },
    "cursor": "101076285",
    "id": "TWVzc2FnZUVkZ2U6MTAxMDc2Mjg1OjEwMTA3NjI4NQ=="
  },
  ...
]
"""
```

#### Deleting Messages:
To delete messages, use the `client.delete_message` function, which accepts a single argument. You can pass a single message ID into it to delete a single message, or you can pass a list of message IDs to delete multiple messages at once.

```python
#delete a single message
client.delete(96105719)

#delete multiple messages at once
client.delete([96105719, 96097108, 96097078, 96084421, 96084402])
```

#### Purging a Conversation:
To purge an entire conversation, or just the last few messages, you can use the `client.purge_conversation` function. This function accepts the following arguments:
 - `chatbot` - The codename of the chatbot.
 - `count = -1` - The number of messages to be deleted, starting from the latest one. The default behavior is to delete every single message.

```python
#purge just the last 10 messages
client.purge_conversation("capybara", count=10)

#purge the entire conversation
client.purge_conversation("capybara")
```

### Misc:
#### Changing the Logging Level:
If you want to show debug messages, simply call `poe.logger.setLevel`.

```python
import poe
import logging
poe.logger.setLevel(logging.INFO)
```

#### Setting a Custom User-Agent:
If you want to change the user-agent that is being spoofed, set `poe.user_agent`.

```python
import poe
poe.user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
```

## Copyright: 
This program is licensed under the [GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0.txt). All code, with the exception of the GraphQL queries, has been written by me, [ading2210](https://github.com/ading2210).

Most of the GraphQL queries are taken from [muharamdani/poe](https://github.com/muharamdani/poe), which is licenced under the ISC License. 