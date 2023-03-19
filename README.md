# Python Poe API
This is a reverse engineered API wrapper for Quora's Poe, which allows you free access to OpenAI's ChatGPT and GPT-4, as well as Antropic's Claude.

## Features:
 - Log in with token
 - Download bot list
 - Send messages
 - Stream bot responses

## Documentation:
An example can be be found in `/example.py`.

### Using the Client:
To use this library, simply import `poe` and create a `poe.Client` instance, passing in your token as the only argument. You can find your token in the `p-b` field in your browser's cookies. Note that the following examples assume `client` is the name of your `poe.Client` instance.
```python
import poe
client = poe.Poe("TOKEN_HERE")
```

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

### Misc:
#### Changing the Logging Level:
If you want to show debug messages, simply call `poe.logger.setLevel`.
```python
import poe
poe.logger.setLevel(logging.INFO)
```

#### Setting a Custom User-Agent:
If you want to change the user-agent that is being spoofed, set `poe.user_agent`.

```python
import poe
poe.user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
```

### Copyright: 
This program is licensed under the [GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0.txt). ALl code has been written by me, [ading2210](https://github.com/ading2210).

Most of the GraphQL queries are taken from [muharamdani/poe](https://github.com/muharamdani/poe), which is licenced under the ISC License. 