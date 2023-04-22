# Python Poe API

[![PyPi Version](https://img.shields.io/pypi/v/poe-api.svg)](https://pypi.org/project/poe-api/)

This is a reverse engineered API wrapper for Quora's Poe, which allows you free access to OpenAI's ChatGPT and GPT-4, as well as Antropic's Claude.

## Table of Contents:
- [Features](#features)
- [Installation](#installation)
- [Documentation](#documentation)
  * [Finding Your Token](#finding-your-token)
  * [Using the Client](#using-the-client)
    + [Downloading the Available Bots](#downloading-the-available-bots)
    + [Creating New Bots](#creating-new-bots)
    + [Editing a Bot](#editing-a-bot)
    + [Sending Messages](#sending-messages)
    + [Clearing the Conversation Context](#clearing-the-conversation-context)
    + [Downloading Conversation History](#downloading-conversation-history)
    + [Deleting Messages](#deleting-messages)
    + [Purging a Conversation](#purging-a-conversation)
  * [Misc](#misc)
    + [Changing the Logging Level](#changing-the-logging-level)
    + [Setting a Custom User-Agent](#setting-a-custom-user-agent)
- [Copyright](#copyright)
  * [Copyright Notice](#copyright-notice)

*Table of contents generated with [markdown-toc](http://ecotrust-canada.github.io/markdown-toc).*

## Features:
 - Log in with token
 - Proxy requests + websocket
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

### Finding Your Token:
Log into [Poe](https://poe.com) on any web browser, then open your browser's developer tools (also known as "inspect") and look for the value of the `p-b` cookie in the following menus:
 - Chromium: Devtools > Application > Cookies > poe.com
 - Firefox: Devtools > Storage > Cookies
 - Safari: Devtools > Storage > Cookies

### Using the Client:
To use this library, simply import `poe` and create a `poe.Client` instance. The Client class accepts the following arguments:
 - `token` - The token to use. 
 - `proxy = None` - The proxy to use, in the format `protocol://host:port`. The socks5/socks4 protocol is reccommended.

Regular Example:
```python
import poe
client = poe.Client("TOKEN_HERE")
```

Proxied Example:
```python
import poe
client = poe.Client("TOKEN_HERE", proxy="socks5://178.62.100.151:59166")
```

Note that the following examples assume `client` is the name of your `poe.Client` instance. If the token is invalid, a RuntimeError will be raised.

#### Downloading the Available Bots:
The client downloads all of the available bots upon initialization and stores them within `client.bots`. A dictionary that maps bot codenames to their display names can be found at `client.bot_names`. If you want to refresh these values, you can call `client.get_bots`. This function takes the following arguments:
 - `download_next_data = True` - Whether or not to redownload the `__NEXT_DATA__`, which is required if the bot list has changed. 

```python
print(client.bot_names)
#{'capybara': 'Sage', 'beaver': 'GPT-4', 'a2_2': 'Claude+', 'a2': 'Claude', 'chinchilla': 'ChatGPT', 'nutria': 'Dragonfly'}
```

Note that, on free accounts, Claude+ (a2_2) has a limit of 3 messages per day and GPT-4 (beaver) has a limit of 1 message per day. For all the other chatbots, there seems to be a rate limit of 10 messages per minute.

#### Creating New Bots:
You can create a new bot using the `client.create_bot` function, which accepts the following arguments:
 - `handle` - The handle of the new bot.
 - `prompt = ""` - The prompt for the new bot.
 - `base_model = "chinchilla"` - The model that the new bot uses. This must be either `"chinchilla"` (ChatGPT)  or `"a2"` (Claude).
 - `description = ""` - The description for the new bot.
 - `intro_message = ""` - The intro message for the new bot. If this is an empty string then the bot will not have an intro message.
 - `prompt_public = True` - Whether or not the prompt should be publicly visible. 
 - `pfp_url = None` - The URL for the bot's profile picture. Currently, there is no way to actually upload a custom image using this library.
 - `linkification = False` - Whether or not the bot should turn some text in the response into clickable links.
 - `markdown_rendering = True` - Whether or not to enable markdown rendering for the bot's responses.
 - `suggested_replies = False` - Whether or not the bot should suggest possible replies after each response.
 - `private = False` - Whether or not the bot should be private.

Additionally, there are some arguments that seem to be for the upcoming bot developer API. You do not need to specify these, although they may become useful in the future. The description for these arguments are currently my best guesses for what they do:
 - `api_key = None` - The API key for the new bot. 
 - `api_bot = False` - Whether or not the bot has API functionally enabled.
 - `api_url = None` - The API URL for the new bot.

A full example of how to create and edit bots is located at `examples/create_bot.py`.
```python
new_bot = client.create_bot(bot_name, "prompt goes here", base_model="a2")
```

#### Editing a Bot:
You can edit a custom bot using the `client.edit_bot` function, which accepts the following arguments:
 - `bot_id` - The `botId` of the bot to edit.
 - `handle` - The handle of the bot to edit.
 - `prompt` - The prompt for the new bot.
 - `base_model = "chinchilla"` - The new model that the bot uses. This must be either `"chinchilla"` (ChatGPT)  or `"a2"` (Claude). Previously, it was possible to set this to `"beaver"` (GPT-4), which would bypass the free account restrictions, but this is now patched.
 - `description = ""` - The new description for the bot.
 - `intro_message = ""` - The new intro message for the bot. If this is an empty string then the bot will not have an intro message.
 - `prompt_public = True` - Whether or not the prompt should be publicly visible. 
 - `pfp_url = None` - The URL for the bot's profile picture. Currently, there is no way to actually upload a custom image using this library.
 - `linkification = False` - Whether or not the bot should turn some text in the response into clickable links.
 - `markdown_rendering = True` - Whether or not to enable markdown rendering for the bot's responses.
 - `suggested_replies = False` - Whether or not the bot should suggest possible replies after each response.
 - `private = False` - Whether or not the bot should be private.

Unreleased bot developer API arguments:
 - `api_key = None` - The new API key for the bot. 
 - `api_url = None` - The new API URL for the bot.

A full example of how to create and edit bots is located at `examples/create_bot.py`.
```python
edit_result = client.edit_bot(1086981, "bot_handle_here", base_model="beaver")
```

#### Sending Messages:
You can use the `client.send_message` function to send a message to a chatbot, which accepts the following arguments:
 - `chatbot` - The codename of the chatbot. (example: `capybara`)
 - `message` - The message to send to the chatbot.
 - `with_chat_break = False` - Whether the conversation context should be cleared.
 - `timeout = 20` - The max number of seconds in between recieved chunks until a `RuntimeError` is raised. 

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

You can also send multiple messages in parallel using `threading` and recieve their responses seperately, as demonstrated in `/examples/parallel_messages.py`. Note that if you send messages too fast, the server will give an error, but the request will eventually succeed.

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
 
Note that if you don't specify a cursor, the client will have to perform an extra request to determine what the latest cursor is.

The returned messages are ordered from oldest to newest. 

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
client.delete_message(96105719)

#delete multiple messages at once
client.delete_message([96105719, 96097108, 96097078, 96084421, 96084402])
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

#### Getting the Remaining Messages:
To get the number of messages remaining in the quota for a conversation, use the `client.get_remaining_messages` function. This function accepts the following arguments:
 - `chatbot` - The codename of the chatbot.

The function will return the number of messages remaining, or `None` if the bot does not have a quota.

### Misc:
#### Changing the Logging Level:
If you want to show debug messages, simply call `poe.logger.setLevel`.

```python
import poe
import logging
poe.logger.setLevel(logging.INFO)
```

#### Setting a Custom User-Agent:
If you want to change the headers that are spoofed, set `poe.headers` after importing the library. 

To use your browser's own headers, visit [this site](https://headers.uniqueostrich18.repl.co/), and copy-paste its contents.
```python
import poe
poe.headers = {
  "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0",
  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
  "Accept-Encoding": "gzip, deflate, br",
  "Accept-Language": "en-US,en;q=0.5",
  "Te": "trailers",
  "Upgrade-Insecure-Requests": "1"
}
```

The following headers will be ignored and overwritten:
```python
{
  "Referrer": "https://poe.com/",
  "Origin": "https://poe.com",
  "Host": "poe.com",
  "Sec-Fetch-Dest": "empty",
  "Sec-Fetch-Mode": "cors",
  "Sec-Fetch-Site": "same-origin"
}
```

Previously, this was done through `poe.user_agent`, but that variable is now completely ignored.

## Copyright: 
This program is licensed under the [GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0.txt). Most code, with the exception of the GraphQL queries, has been written by me, [ading2210](https://github.com/ading2210).

Reverse engineering the `poe-tag-id` header has been done by [xtekky](https://github.com/xtekky) in [PR #39](https://github.com/ading2210/poe-api/pull/39).

The `client.get_remaining_messages` function was written by [Snowad14](https://github.com/Snowad14) in [PR #46](https://github.com/ading2210/poe-api/pull/46).

Most of the GraphQL queries are taken from [muharamdani/poe](https://github.com/muharamdani/poe), which is licenced under the ISC License. 

### Copyright Notice:
```
ading2210/poe-api: a reverse engineered Python API wrapepr for Quora's Poe
Copyright (C) 2023 ading2210

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```