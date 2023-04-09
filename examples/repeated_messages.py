import poe
import logging
import sys
import time

#send messages in a loop

poe.logger.setLevel(logging.INFO)
token = sys.argv[1]
client = poe.Client(token)

message = "This is message number {num}."

counter = 1
while True:  
  for chunk in client.send_message("capybara", message.format(num=counter), with_chat_break=True):
    print(chunk["text_new"], end="", flush=True)
  print()
  counter += 1
  time.sleep(2)