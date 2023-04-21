import poe
import logging
import sys
import json

#create a bot and edit its model

poe.logger.setLevel(logging.INFO)
token = sys.argv[1]
client = poe.Client(token)

bot_name = input("bot name: ")
new_bot = client.create_bot(bot_name, "", base_model="chinchilla")
print("new bot created: "+bot_name)

handle = bot_name.lower()
bot_id = client.bots[handle]["defaultBotObject"]["botId"]
edit_result = client.edit_bot(bot_id, handle, base_model="a2") #switch model to claude
print("edit status: "+edit_result["status"])