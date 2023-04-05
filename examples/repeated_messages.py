import poe
import logging
import sys

#send messages in a loop

poe.logger.setLevel(logging.INFO)
token = sys.argv[1]
client = poe.Client(token)

message = "Who are you?"

while True:  
  for chunk in client.send_message("capybara", message, with_chat_break=True):
    print(chunk["text_new"], end="", flush=True)
  print()