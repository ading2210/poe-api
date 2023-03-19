import poe
import logging
import sys

poe.logger.setLevel(logging.INFO)

token = sys.argv[1]
chatbot = poe.Poe(token)

for chunk in chatbot.send_message("capybara", "Summarize the GNU GPL v3"):
  print(chunk["text_new"], end="", flush=True)