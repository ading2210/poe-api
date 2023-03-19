import poe
import logging
import sys

poe.logger.setLevel(logging.INFO)

token = sys.argv[1]
client = poe.Client(token)

message = "Summarize the GNU GPL v3"
for chunk in client.send_message("capybara", message, with_chat_break=True):
  print(chunk["text_new"], end="", flush=True)

print()
for chunk in client.send_message("capybara", "What is 9+10?", with_chat_break=True):
  print(chunk["text_new"], end="", flush=True)
print()