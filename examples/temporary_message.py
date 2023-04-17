import poe
import logging
import sys

#send a message and immediately delete it

token = sys.argv[1]
poe.logger.setLevel(logging.INFO)
client = poe.Client(token)

message = "Who are you?"
for chunk in client.send_message("capybara", message, with_chat_break=True):
  print(chunk["text_new"], end="", flush=True)

#delete the 3 latest messages, including the chat break
client.purge_conversation("capybara", count=3)