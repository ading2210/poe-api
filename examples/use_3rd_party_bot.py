import poe
import sys
import logging

#download a list of third party bots and send a message to one of them

poe.logger.setLevel(logging.INFO)
token = sys.argv[1]
client = poe.Client(token)

bots = client.explore_bots()
bots = client.explore_bots(end_cursor=bots["end_cursor"])

bot = bots["bots"][-1]
bot_name = bot.get("displayName")
bot_id = bot.get("botId")

print(f"Bot name: {bot_name}")

message = "Summarize the GNU GPL v3"
for chunk in client.send_message(bots["bots"][-1].get("displayName"), message, with_chat_break=True):
  print(chunk["text_new"], end="", flush=True)
print()