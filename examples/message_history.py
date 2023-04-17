import poe
import logging
import sys

#fetch the last 10 messages in Sage's conversation

token = sys.argv[1]
poe.logger.setLevel(logging.INFO)
client = poe.Client(token)

message_history = client.get_message_history("capybara", count=50)
print(f"Last {len(message_history)} messages:")
for message in message_history:
  node = message["node"]
  print(f'{node["author"]}: {node["text"]}')