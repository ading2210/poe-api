import poe
import logging
import sys
import json

#get the account's bot list

token = sys.argv[1]
poe.logger.setLevel(logging.INFO)
client = poe.Client(token)

print(json.dumps(client.bot_names, indent=2))