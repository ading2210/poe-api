import re, json, random, logging, time, queue, threading, traceback, hashlib, string, random, os
import requests
import tls_client as requests_tls
import secrets
import websocket
import uuid
import random
from pathlib import Path
from urllib.parse import urlparse

parent_path = Path(__file__).resolve().parent
queries_path = parent_path / "poe_graphql"
queries = {}

logging.basicConfig()
logger = logging.getLogger()

user_agent = "This will be ignored! See the README for info on how to set custom headers."
headers = {
  "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
  "Accept-Encoding": "gzip, deflate, br",
  "Accept-Language": "en-US,en;q=0.9",
  "Sec-Ch-Ua": "\"Not.A/Brand\";v=\"8\", \"Chromium\";v=\"112\"",
  "Sec-Ch-Ua-Mobile": "?0",
  "Sec-Ch-Ua-Platform": "\"Linux\"",
  "Upgrade-Insecure-Requests": "1"
}
client_identifier = "chrome112"

def load_queries():
  for path in queries_path.iterdir():
    if path.suffix != ".graphql":
      continue
    with open(path) as f:
      queries[path.stem] = f.read()

def generate_payload(query_name, variables):
  if query_name == "recv":
    return generate_recv_payload(variables)
  return {
    "query": queries[query_name],
    "queryName": query_name,
    "variables": variables
  }

def generate_recv_payload(variables):
  payload = [
    {
      "category": "poe/bot_response_speed",
      "data": variables,
    }
  ]

  if random.random() > 0.9:
    payload.append({
      "category": "poe/statsd_event",
      "data": {
        "key": "poe.speed.web_vitals.INP",
        "value": random.randint(100, 125),
        "category": "time",
        "path": "/[handle]",
        "extra_data": {},
      },
    })

  return payload


def request_with_retries(method, *args, **kwargs):
  attempts = kwargs.get("attempts") or 10
  url = args[0]
  for i in range(attempts):
    r = method(*args, **kwargs)
    if r.status_code == 200:
      return r
    if r.status_code == 307:
      if r.headers.get("Location").startswith("/login"):
        raise RuntimeError("Invalid or missing token.")
    logger.warn(f"Server returned a status code of {r.status_code} while downloading {url}. Retrying ({i+1}/{attempts})...")

  raise RuntimeError(f"Failed to download {url} too many times.")

def generate_nonce(length:int=16):
  return "".join(secrets.choice(string.ascii_letters + string.digits) for i in range(length))

def get_config_path():
  if os.name == "nt":
    return Path.home() / "AppData" / "Roaming" / "poe-api"
  return Path.home() / ".config" / "poe-api"

def set_saved_device_id(user_id, device_id):
  device_id_path = get_config_path() / "device_id.json"
  device_ids = {}
  if device_id_path.exists():
    with open(device_id_path) as f:
      device_ids = json.loads(f.read())

  device_ids[user_id] = device_id
  device_id_path.parent.mkdir(parents=True, exist_ok=True)
  with open(device_id_path, "w") as f:
    f.write(json.dumps(device_ids, indent=2))

def get_saved_device_id(user_id):
  device_id_path = get_config_path() / "device_id.json"
  device_ids = {}
  if device_id_path.exists():
    with open(device_id_path) as f:
      device_ids = json.loads(f.read())

  if user_id in device_ids:
    return device_ids[user_id]

  device_id = str(uuid.uuid4())
  device_ids[user_id] = device_id
  device_id_path.parent.mkdir(parents=True, exist_ok=True)
  with open(device_id_path, "w") as f:
    f.write(json.dumps(device_ids, indent=2))

  return device_id

class Client:
  gql_url = "https://poe.com/api/gql_POST"
  gql_recv_url = "https://poe.com/api/receive_POST"
  home_url = "https://poe.com"
  settings_url = "https://poe.com/api/settings"

  def __init__(self, token, proxy=None, headers=headers, device_id=None, client_identifier=client_identifier):
    self.ws_connecting = False
    self.ws_connected = False
    self.ws_error = False
    self.connect_count = 0
    self.setup_count = 0

    self.token = token
    self.device_id = device_id
    self.proxy = proxy
    self.client_identifier = client_identifier

    self.active_messages = {}
    self.message_queues = {}
    self.suggestion_callbacks = {}

    self.headers = {**headers, **{
      "Cache-Control": "no-cache",
      "Sec-Fetch-Dest": "document",
      "Sec-Fetch-Mode": "navigate",
      "Sec-Fetch-Site": "same-origin",
      "Sec-Fetch-User": "?1",
    }}

    self.connect_ws()

  def setup_session(self):
    logger.info("Setting up session...")
    if self.client_identifier:
      self.session = requests_tls.Session(client_identifier=self.client_identifier)
    else:
      self.session = requests.Session()

    if self.proxy:
      self.session.proxies = {
        "http": self.proxy,
        "https": self.proxy
      }
      logger.info(f"Proxy enabled: {self.proxy}")

    self.session.cookies.set("p-b", self.token, domain="poe.com")
    self.session.headers.update(self.headers)

  def setup_connection(self):
    if self.setup_count % 5 == 0:
      self.setup_session()

    self.setup_count += 1

    self.ws_domain = f"tch{random.randint(1, 1e6)}"
    self.next_data = self.get_next_data(overwrite_vars=True)
    self.channel = self.get_channel_data()

    if not hasattr(self, "bots"):
      self.bots = self.get_bots(download_next_data=False)
    if not hasattr(self, "bot_names"):
      self.bot_names = self.get_bot_names()

    if self.device_id is None:
      self.device_id = self.get_device_id()

    self.gql_headers = {
      "poe-formkey": self.formkey,
      "poe-tchannel": self.channel["channel"],
    }
    self.gql_headers = {**self.gql_headers, **self.headers}
    self.subscribe()

  def get_device_id(self):
    user_id = self.viewer["poeUser"]["id"]
    device_id = get_saved_device_id(user_id)
    return device_id

  def extract_formkey(self, html):
    script_regex = r'<script>(.+)function\(\){return .\.join\(""\)};</script>'
    script_text = re.search(script_regex, html).group(1)
    key_regex = r'var .="([0-9a-f]+)",'
    key_text = re.search(key_regex, script_text).group(1)
    cipher_regex = r'.\[(\d+)\]=.\[(\d+)\]'
    cipher_pairs = re.findall(cipher_regex, script_text)

    formkey_list = [""] * len(cipher_pairs)
    for pair in cipher_pairs:
      formkey_index, key_index = map(int, pair)
      formkey_list[formkey_index] = key_text[key_index]
    formkey = "".join(formkey_list)[:-1]

    return formkey

  def get_next_data(self, overwrite_vars=False):
    logger.info("Downloading next_data...")

    r = request_with_retries(self.session.get, self.home_url)
    json_regex = r'<script id="__NEXT_DATA__" type="application\/json">(.+?)</script>'
    json_text = re.search(json_regex, r.text).group(1)
    next_data = json.loads(json_text)

    if overwrite_vars:
      self.formkey = self.extract_formkey(r.text)
      if "payload" in next_data["props"]["pageProps"]:
        self.viewer = next_data["props"]["pageProps"]["payload"]["viewer"]
      else:
        self.viewer = next_data["props"]["pageProps"]["data"]["viewer"]
      self.user_id = self.viewer["poeUser"]["id"]
      self.next_data = next_data

    return next_data

  def get_bot(self, handle):
    url = f'https://poe.com/_next/data/{self.next_data["buildId"]}/{handle}.json'

    data = request_with_retries(self.session.get, url).json()
    chat_data = data["pageProps"]["data"]["chatOfBotHandle"]
    return chat_data

  def get_bots(self, download_next_data=True):
    logger.info("Downloading all bots...")
    if download_next_data:
      next_data = self.get_next_data(overwrite_vars=True)
    else:
      next_data = self.next_data

    if not "availableBotsConnection" in self.viewer:
      raise RuntimeError("Invalid token or no bots are available.")
    bot_list_url = f'https://poe.com/_next/data/{self.next_data["buildId"]}/index.json'
    bot_list = self.viewer["availableBotsConnection"]["edges"]

    threads = []
    bots = {}

    def get_bot_thread(bot):
      chat_data = self.get_bot(bot["node"]["handle"])
      bots[chat_data["defaultBotObject"]["nickname"]] = chat_data

    for bot in bot_list:
      thread = threading.Thread(target=get_bot_thread, args=(bot,), daemon=True)
      threads.append(thread)

    for thread in threads:
      thread.start()
    for thread in threads:
      thread.join()

    self.bots = bots
    self.bot_names = self.get_bot_names()
    return bots

  def get_bot_by_codename(self, bot_codename):
    if bot_codename in self.bots:
      return self.bots[bot_codename]

    #todo: cache this so it isn't re-downloaded every time
    return self.get_bot(bot_codename)

  def get_bot_names(self):
    bot_names = {}
    for bot_nickname in self.bots:
      bot_obj = self.bots[bot_nickname]["defaultBotObject"]
      bot_names[bot_nickname] = bot_obj["displayName"]
    return bot_names

  def explore_bots(self, end_cursor=None, count=25):
    if not end_cursor:
      url = f'https://poe.com/_next/data/{self.next_data["buildId"]}/explore_bots.json'
      r = request_with_retries(self.session.get, url).json()
      data = r["pageProps"].get("payload") or r["pageProps"]["data"]
      nodes = data["exploreBotsConnection"]["edges"]
      bots = [node["node"] for node in nodes]
      bots = bots[:count]
      return {
        "bots": bots,
        "end_cursor": data["exploreBotsConnection"]["pageInfo" ]["endCursor"],
      }

    else:
      # Use graphql to get the next page
      result = self.send_query("ExploreBotsListPaginationQuery", {
        "count": count,
        "cursor": end_cursor
      })
      result = result["data"]["exploreBotsConnection"]

      bots = [node["node"] for node in result["edges"]]
      return {
        "bots": bots,
        "end_cursor": result["pageInfo"]["endCursor"],
      }

  def get_remaining_messages(self, chatbot):
    chat_data = self.get_bot_by_codename(chatbot)
    return chat_data["defaultBotObject"]["messageLimit"]["numMessagesRemaining"]

  def get_channel_data(self, channel=None):
    logger.info("Downloading channel data...")
    r = request_with_retries(self.session.get, self.settings_url)
    data = r.json()

    return data["tchannelData"]

  def get_websocket_url(self, channel=None):
    if channel is None:
      channel = self.channel
    query = f'?min_seq={channel["minSeq"]}&channel={channel["channel"]}&hash={channel["channelHash"]}'
    return f'ws://{self.ws_domain}.tch.{channel["baseHost"]}/up/{channel["boxName"]}/updates'+query

  def send_query(self, query_name, variables, attempts=20):
    for i in range(attempts):
      json_data = generate_payload(query_name, variables)
      payload = json.dumps(json_data, separators=(",", ":"))

      base_string = payload + self.gql_headers["poe-formkey"] + "Jb1hi3fg1MxZpzYfy"

      headers = {
        "content-type": "application/json",
        "poe-tag-id": hashlib.md5(base_string.encode()).hexdigest()
      }
      headers = {**self.gql_headers, **headers}

      if query_name == "recv":
        r = request_with_retries(self.session.post, self.gql_recv_url, data=payload, headers=headers)
        return None

      r = request_with_retries(self.session.post, self.gql_url, data=payload, headers=headers)
      data = r.json()
      if data["data"] == None:
        logger.warn(f'{query_name} returned an error: {data["errors"][0]["message"]} | Retrying ({i+1}/20) | Response: {data}')
        time.sleep(2)
        continue

      return r.json()

    raise RuntimeError(f'{query_name} failed too many times.')

  def subscribe(self):
    logger.info("Subscribing to mutations")
    result = self.send_query("SubscriptionsMutation", {
      "subscriptions": [
        {
          "subscriptionName": "messageAdded",
          "query": queries["MessageAddedSubscription"]
        },
        {
          "subscriptionName": "viewerStateUpdated",
          "query": queries["ViewerStateUpdatedSubscription"]
        }
      ]
    })

  def ws_run_thread(self):
    kwargs = {}
    if self.proxy:
      proxy_parsed = urlparse(self.proxy)
      kwargs = {
        "proxy_type": proxy_parsed.scheme,
        "http_proxy_host": proxy_parsed.hostname,
        "http_proxy_port": proxy_parsed.port
      }

      # auth if exists
      if proxy_parsed.username and proxy_parsed.password:
        kwargs["http_proxy_auth"] = (proxy_parsed.username, proxy_parsed.password)

    self.ws.run_forever(**kwargs)

  def connect_ws(self, timeout=5):
    if self.ws_connected:
      return

    if self.ws_connecting:
      while not self.ws_connected:
        time.sleep(0.01)
      return

    self.ws_connecting = True
    self.ws_connected = False

    if self.connect_count % 5 == 0:
      self.setup_connection()

    self.connect_count += 1

    ws = websocket.WebSocketApp(
      self.get_websocket_url(),
      header={"User-Agent": user_agent},
      on_message=self.on_message,
      on_open=self.on_ws_connect,
      on_error=self.on_ws_error,
      on_close=self.on_ws_close
    )

    self.ws = ws

    t = threading.Thread(target=self.ws_run_thread, daemon=True)
    t.start()

    timer = 0
    while not self.ws_connected:
      time.sleep(0.01)
      timer += 0.01
      if timer > timeout:
        self.ws_connecting = False
        self.ws_connected = False
        self.ws_error = True
        ws.close()
        raise RuntimeError("Timed out waiting for websocket to connect.")

  def disconnect_ws(self):
    self.ws_connecting = False
    self.ws_connected = False
    if self.ws:
      self.ws.close()

  def on_ws_connect(self, ws):
    self.ws_connecting = False
    self.ws_connected = True

  def on_ws_close(self, ws, close_status_code, close_message):
    logger.warn(f"Websocket closed with status {close_status_code}: {close_message}")

    self.ws_connecting = False
    self.ws_connected = False
    if self.ws_error:
      self.ws_error = False
      self.connect_ws()

  def on_ws_error(self, ws, error):
    self.ws_connecting = False
    self.ws_connected = False
    self.ws_error = True

  def on_message(self, ws, msg):
    try:
      data = json.loads(msg)

      if not "messages" in data:
        return

      for message_str in data["messages"]:
        message_data = json.loads(message_str)
        if message_data["message_type"] != "subscriptionUpdate":
          continue
        message = message_data["payload"]["data"]["messageAdded"]

        #handle suggested replies
        if "suggestedReplies" in message and type(message["suggestedReplies"]) == list and len(message["suggestedReplies"]) > 0 and message["messageId"] in self.suggestion_callbacks:
          self.suggestion_callbacks[message["messageId"]](message["suggestedReplies"][-1])
          if len(message["suggestedReplies"]) >= 3:
            del self.suggestion_callbacks[message["messageId"]]

        copied_dict = self.active_messages.copy()
        for key, value in copied_dict.items():
          #add the message to the appropriate queue
          if value == message["messageId"] and key in self.message_queues:
            self.message_queues[key].put(message)
            return

          #indicate that the response id is tied to the human message id
          elif key != "pending" and value == None and message["state"] != "complete":
            self.active_messages[key] = message["messageId"]
            self.message_queues[key].put(message)
            return

    except Exception:
      logger.error(traceback.format_exc())
      self.disconnect_ws()
      self.connect_ws()

  def send_message(self, chatbot, message, with_chat_break=False, timeout=20, async_recv=True, suggest_callback=None):
    # if there is another active message, wait until it has finished sending
    timer = 0
    while None in self.active_messages.values():
      time.sleep(0.01)
      timer += 0.01
      if timer > timeout:
        raise RuntimeError("Timed out waiting for other messages to send.")

    # None indicates that a message is still in progress
    self.active_messages["pending"] = None

    # reconnect websocket
    while self.ws_error:
      time.sleep(0.01)

    self.connect_ws()

    logger.info(f"Sending message to {chatbot}: {message}")

    chat_id = self.get_bot_by_codename(chatbot)["chatId"]
    try:
      message_data = self.send_query("SendMessageMutation", {
        "bot": chatbot,
        "query": message,
        "chatId": chat_id,
        "source": None,
        "clientNonce": generate_nonce(),
        "sdid": self.device_id,
        "withChatBreak": with_chat_break,
      })
      del self.active_messages["pending"]
    except Exception as e:
      del self.active_messages["pending"]
      raise e

    if not message_data["data"]["messageEdgeCreate"]["message"]:
      raise RuntimeError(f"Daily limit reached for {chatbot}.")
    try:
      human_message = message_data["data"]["messageEdgeCreate"]["message"]
      human_message_id = human_message["node"]["messageId"]
    except TypeError:
      raise RuntimeError(f"An unknown error occurred. Raw response data: {message_data}")

    # indicate that the current message is waiting for a response
    self.active_messages[human_message_id] = None
    self.message_queues[human_message_id] = queue.Queue()

    last_text = ""
    message_id = None
    while True:
      try:
        message = self.message_queues[human_message_id].get(timeout=timeout)
      except queue.Empty:
        del self.active_messages[human_message_id]
        del self.message_queues[human_message_id]
        raise RuntimeError("Response timed out.")

      #only break when the message is marked as complete
      if message["state"] == "complete":
        if last_text and message["messageId"] == message_id:
          break
        else:
          continue

      #update info about response
      message["text_new"] = message["text"][len(last_text):]
      last_text = message["text"]
      message_id = message["messageId"]

      # set a suggestion callback on response
      if callable(suggest_callback) and not message_id in self.suggestion_callbacks:
        self.suggestion_callbacks[message_id] = suggest_callback

      yield message

    def recv_post_thread():
      bot_message_id = self.active_messages[human_message_id]

      # wait 2 seconds after sending the request
      time.sleep(2.5)

      # send recv_post after receiving the last message
      self.send_query("recv", {
        "bot": chatbot,
        "time_to_first_typing_indicator": 300, # randomly select
        "time_to_first_subscription_response": 600,
        "time_to_full_bot_response": 1100,
        "full_response_length": len(last_text) + 1,
        "full_response_word_count": len(last_text.split(" ")) + 1,
        "human_message_id": human_message_id,
        "bot_message_id": bot_message_id,
        "chat_id": chat_id,
        "bot_response_status": "success",
      })
      time.sleep(0.5)

    t = threading.Thread(target=recv_post_thread, daemon=True)
    t.start()
    if not async_recv:
      t.join()

    del self.active_messages[human_message_id]
    del self.message_queues[human_message_id]

  def send_chat_break(self, chatbot):
    logger.info(f"Sending chat break to {chatbot}")
    result = self.send_query("AddMessageBreakMutation", {
      "chatId": self.get_bot_by_codename(chatbot)["chatId"]}
    )
    return result["data"]["messageBreakEdgeCreate"]["message"]

  def get_message_history(self, chatbot, count=25, cursor=None):
    logger.info(f"Downloading {count} messages from {chatbot}")

    messages = []
    if cursor == None:
      if not chatbot in self.bots:
        chat_data = self.get_bot(chatbot)
      else:
        chat_data = self.get_bot(self.bot_names[chatbot])

      if not chat_data["messagesConnection"]["edges"]:
        return []
      messages = chat_data["messagesConnection"]["edges"][-count:]
      cursor = chat_data["messagesConnection"]["pageInfo"]["startCursor"]
      count -= len(messages)

    cursor = str(cursor)
    if count > 50:
      messages = self.get_message_history(chatbot, count=50, cursor=cursor) + messages
      while count > 0:
        count -= 50
        new_cursor = messages[0]["cursor"]
        new_messages = self.get_message_history(chatbot, min(50, count), cursor=new_cursor)
        messages = new_messages + messages
      return messages
    elif count <= 0:
      return messages

    result = self.send_query("ChatListPaginationQuery", {
      "count": count,
      "cursor": cursor,
      "id": self.get_bot_by_codename(chatbot)["id"]
    })
    query_messages = result["data"]["node"]["messagesConnection"]["edges"]
    messages = query_messages + messages
    return messages

  def delete_message(self, message_ids):
    logger.info(f"Deleting messages: {message_ids}")
    if not type(message_ids) is list:
      message_ids = [int(message_ids)]

    result = self.send_query("DeleteMessageMutation", {
      "messageIds": message_ids
    })

  def purge_conversation(self, chatbot, count=-1):
    logger.info(f"Purging messages from {chatbot}")
    last_messages = self.get_message_history(chatbot, count=50)[::-1]
    while last_messages:
      message_ids = []
      for message in last_messages:
        if count == 0:
          break
        count -= 1
        message_ids.append(message["node"]["messageId"])

      self.delete_message(message_ids)

      if count == 0:
        return
      last_messages = self.get_message_history(chatbot, count=50)[::-1]

    logger.info(f"No more messages left to delete.")

  def create_bot(self, handle, prompt, display_name=None, base_model="chinchilla", description="",
                  intro_message="", api_key=None, api_bot=False, api_url=None,
                  prompt_public=True, pfp_url=None, linkification=False,
                  markdown_rendering=True, suggested_replies=False, private=False,
                  temperature=None):
    result = self.send_query("PoeBotCreateMutation", {
      "model": base_model,
      "displayName": display_name,
      "handle": handle,
      "prompt": prompt,
      "isPromptPublic": prompt_public,
      "introduction": intro_message,
      "description": description,
      "profilePictureUrl": pfp_url,
      "apiUrl": api_url,
      "apiKey": api_key,
      "isApiBot": api_bot,
      "hasLinkification": linkification,
      "hasMarkdownRendering": markdown_rendering,
      "hasSuggestedReplies": suggested_replies,
      "isPrivateBot": private,
      "temperature": temperature
    })

    data = result["data"]["poeBotCreate"]
    if data["status"] != "success":
      raise RuntimeError(f"Poe returned an error while trying to create a bot: {data['status']}")
    self.get_bots()
    return data

  def edit_bot(self, bot_id, handle, prompt, display_name=None, base_model="chinchilla", description="",
                intro_message="", api_key=None, api_url=None, private=False,
                prompt_public=True, pfp_url=None, linkification=False,
                markdown_rendering=True, suggested_replies=False, temperature=None, new_handle=None):

    if bot_id is None and handle is not None:
      bot_id = self.get_bot(handle)["defaultBotObject"]["botId"]
    new_handle = new_handle or handle
    
    result = self.send_query("PoeBotEditMutation", {
      "baseBot": base_model,
      "botId": bot_id,
      "handle": new_handle,
      "displayName": display_name,
      "prompt": prompt,
      "isPromptPublic": prompt_public,
      "introduction": intro_message,
      "description": description,
      "profilePictureUrl": pfp_url,
      "apiUrl": api_url,
      "apiKey": api_key,
      "hasLinkification": linkification,
      "hasMarkdownRendering": markdown_rendering,
      "hasSuggestedReplies": suggested_replies,
      "isPrivateBot": private,
      "temperature": temperature
    })

    data = result["data"]["poeBotEdit"]
    if data["status"] != "success":
      raise RuntimeError(f"Poe returned an error while trying to edit a bot: {data['status']}")
    self.get_bots()
    return data

  def purge_all_conversations(self):
    logger.info("Purging all conversations")
    self.send_query("DeleteUserMessagesMutation", {})

load_queries()
