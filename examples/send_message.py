import poe
import logging
import sys

#send a message and stream the response

token = sys.argv[1]
poe.logger.setLevel(logging.INFO)
client = poe.Client(token)

message = "Summarize the GNU GPL v3"
for chunk in client.send_message("capybara", message, with_chat_break=True):
  print(chunk["text_new"], end="", flush=True)
print()