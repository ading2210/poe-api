import poe
import logging
import sys

#fetch last 5 messages in Sage's convesation

token = sys.argv[1]
client = poe.Client(token)

message_history = client.get_message_history("capybara", count=10)
print("Last 10 messages:")
for message in message_history:
  node = message["node"]
  print(f'{node["author"]}: {node["text"]}')