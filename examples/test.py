import poe
import logging

poe.logger.setLevel(logging.INFO)
client = poe.Client("5aYauG3gc-ZH99C4ITFoug%3D%3D")

import time

request = 600
wait_time = 600 / request
for i in range(request):
    start_time = time.time()
    input = [
        "How to make an apple pie?",
        "What's the relationship between luna and moon?",
        "How to make a cake?",
    ]
    for chunk in client.send_message(
        "a2", input[i % 3], with_chat_break=True, timeout=20, recv=(i % 3 == 0)
    ):
        pass
    print("Step", i + 1, ":", time.time() - start_time)
    time.sleep(wait_time)
