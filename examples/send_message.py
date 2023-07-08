import poe
import logging
import sys
import time

#send a message and stream the response

token = sys.argv[1]
poe.logger.setLevel(logging.INFO)
client = poe.Client(token)

def callback(suggestion):
    print("Suggested reply:", suggestion)

message = "Summarize the GNU GPL v3"
for chunk in client.send_message("capybara", message, with_chat_break=True, suggest_callback=callback):
  print(chunk["text_new"], end="", flush=True)
print()

# Suggested replies usually come in a few seconds after the message is fully received
for i in range(5):
   time.sleep(1)