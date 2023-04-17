import poe
import logging
import sys
import threading
import time

#send multiple messages and get their responses

token = sys.argv[1]
poe.logger.setLevel(logging.INFO)
client = poe.Client(token)

thread_count = 0

def message_thread(prompt, counter):
  global thread_count
  for chunk in client.send_message("capybara", prompt, with_chat_break=True):
    pass
  print(prompt+"\n"+chunk["text"]+"\n"*3)
  thread_count -= 1

prompts = [
  "Write a paragraph about the impact of social media on mental health.",
  "Write a paragraph about the history and significance of the Olympic Games.",
  "Write a paragraph about the effects of climate change on the world's oceans.",
  "Write a paragraph about the benefits and drawbacks of remote work for employees and companies.",
  "Write a paragraph about the role of technology in modern education.",
  "Write a paragraph about the history and impact of the Civil Rights Movement in America.",
  "Write a paragraph about the impact of COVID-19 on global economies.",
  "Write a paragraph about the rise and fall of the Roman Empire.",
  "Write a paragraph about the benefits and drawbacks of genetically modified organisms (GMOs).",
  "Write a paragraph about the impact of globalization on cultural identity.",
  "Write a paragraph about the history and significance of the Mona Lisa painting.",
  "Write a paragraph about the benefits and drawbacks of renewable energy sources.",
  "Write a paragraph about the impact of social media on political discourse.",
  "Write a paragraph about the history and impact of the Industrial Revolution.",
  "Write a paragraph about the benefits and drawbacks of online shopping for consumers and businesses.",
  "Write a paragraph about the impact of artificial intelligence on the job market.",
  "Write a paragraph about the history and significance of the Great Wall of China.",
  "Write a paragraph about the benefits and drawbacks of standardized testing in schools.",
  "Write a paragraph about the impact of the feminist movement on women's rights.",
  "Write a paragraph about the history and impact of the American Revolution."
]

for i in range(len(prompts)):
  t = threading.Thread(target=message_thread, args=(prompts[i], i), daemon=True)
  t.start()
  thread_count += 1

while thread_count:
  time.sleep(0.1)

client.purge_conversation("capybara")