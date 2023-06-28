import poe
import logging
import sys
import time

poe.logger.setLevel(logging.INFO)
token = sys.argv[1]
client = poe.Client(token)

request = 200
for i in range(request):
  start_time = time.time()
  input = [
    "How to make an apple pie?",
    "What's the relationship between luna and moon?",
    "How to make a cake?",
  ]
  for chunk in client.send_message("a2", input[i % 3], with_chat_break=True, timeout=20):
    pass
  print("Step", i + 1, ":", time.time() - start_time)