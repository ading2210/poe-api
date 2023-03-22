import requests, re, json, random, logging
import websocket
from pathlib import Path

parent_path = Path(__file__).resolve().parent
queries_path = parent_path / "poe_graphql"
queries = {}

logging.basicConfig()
logger = logging.getLogger()

user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0"

def load_queries():
  for path in queries_path.iterdir():
    if path.suffix != ".graphql":
      continue
    with open(path) as f:
      queries[path.stem] = f.read()

def generate_payload(query_name, variables):
  return {
    "query": queries[query_name],
    "variables": variables
  }

def request_with_retries(method, *args, **kwargs):
  attempts = kwargs.get("attempts") or 10
  url = args[0]
  for i in range(attempts):
    r = method(*args, **kwargs)
    if r.status_code == 200:
      return r
    logger.warn(f"Server returned a status code of {r.status_code} while downloading {url}. Retrying ({i+1}/{attempts})...")
  
  raise RuntimeError(f"Failed to download {url} too many times.")

class Client:
  gql_url = "https://poe.com/api/gql_POST"
  gql_recv_url = "https://poe.com/api/receive_POST"
  home_url = "https://poe.com"
  settings_url = "https://poe.com/api/settings"

  formkey = ""
  next_data = {}
  bots = {}
  
  def __init__(self, token):
    self.session = requests.Session()

    self.session.cookies.set("p-b", token, domain="poe.com")
    self.headers = {
      "User-Agent": user_agent,
      "Referrer": "https://poe.com/",
      "Origin": "https://poe.com",
    }
    self.ws_domain = f"tch{random.randint(1, 1e6)}"

    self.session.headers.update(self.headers)
    self.next_data = self.get_next_data()
    self.channel = self.get_channel_data()
    self.bots = self.get_bots()
    self.bot_names = self.get_bot_names()

    self.gql_headers = {
      "poe-formkey": self.formkey,
      "poe-tchannel": self.channel["channel"],
    }
    self.gql_headers = {**self.gql_headers, **self.headers}

    self.subscribe()
    
  def get_next_data(self):
    logger.info("Downloading next_data...")
    
    r = request_with_retries(self.session.get, self.home_url)
    json_regex = r'<script id="__NEXT_DATA__" type="application\/json">(.+?)</script>'
    json_text = re.search(json_regex, r.text).group(1)
    next_data = json.loads(json_text)

    self.formkey = next_data["props"]["formkey"]
    self.viewer = next_data["props"]["pageProps"]["payload"]["viewer"]
    
    return next_data
  
  def get_bots(self):
    viewer = self.next_data["props"]["pageProps"]["payload"]["viewer"]
    if not "availableBots" in viewer:
      raise RuntimeError("Invalid token.")
    bot_list = viewer["availableBots"]

    bots = {}
    for bot in bot_list:
      url = f'https://poe.com/_next/data/{self.next_data["buildId"]}/{bot["displayName"].lower()}.json'
      logger.info("Downloading "+url)
      
      r = request_with_retries(self.session.get, url)

      chat_data = r.json()["pageProps"]["payload"]["chatOfBotDisplayName"]
      bots[chat_data["defaultBotObject"]["nickname"]] = chat_data
          
    return bots
  
  def get_bot_names(self):
    bot_names = {}
    for bot_nickname in self.bots:
      bot_obj = self.bots[bot_nickname]["defaultBotObject"]
      bot_names[bot_nickname] = bot_obj["displayName"]
    return bot_names
  
  def get_channel_data(self, channel=None):
    logger.info("Downloading channel data...")
    r = self.session.get(self.settings_url)
    data = r.json()

    self.formkey = data["formkey"]
    return data["tchannelData"]
  
  def get_websocket_url(self, channel=None):
    if channel is None:
      channel = self.channel
    query = f'?min_seq={channel["minSeq"]}&channel={channel["channel"]}&hash={channel["channelHash"]}'
    return f'wss://{self.ws_domain}.tch.{channel["baseHost"]}/up/{channel["boxName"]}/updates'+query

  def send_query(self, query_name, variables):
    payload = generate_payload(query_name, variables)
    r = self.session.post(self.gql_url, json=payload, headers=self.gql_headers)
    return r.json()
  
  def subscribe(self):
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
  
  def send_message(self, chatbot, message, with_chat_break=False):
    ws = websocket.WebSocket()
    ws.connect(self.get_websocket_url(), header={"User-Agent": user_agent})

    logger.info(f"Sending message to {chatbot}: {message}")
    message_data = self.send_query("AddHumanMessageMutation", {
      "bot": chatbot,
      "query": message,
      "chatId": self.bots[chatbot]["chatId"],
      "source": None,
      "withChatBreak": with_chat_break
    })

    last_text = ""
    message_id = None
    while True:
      data = json.loads(ws.recv())
      message = json.loads(data["messages"][0])["payload"]["data"]["messageAdded"]
      
      if message["state"] == "complete":
        if last_text and message["messageId"] == message_id:
          break
        else:
          continue

      message["text_new"] = message["text"][len(last_text):]
      last_text = message["text"]
      message_id = message["messageId"]

      yield message
    
    ws.close()
  
  def send_chat_break(self, chatbot):
    logger.info(f"Sending chat break to {chatbot}")
    result = self.send_query("AddMessageBreakMutation", {
      "chatId": self.bots[chatbot]["chatId"]
    })
    return result["data"]["messageBreakCreate"]["message"]

  def get_message_history(self, chatbot, count=25, cursor=None):
    logger.info(f"Downloading {count} messages from {chatbot}")
    result = self.send_query("ChatListPaginationQuery", {
      "count": count,
      "cursor": cursor,
      "id": self.bots[chatbot]["id"]
    })
    return result["data"]["node"]["messagesConnection"]["edges"]

  def delete_message(self, message_ids):
    logger.info(f"Deleting messages: {message_ids}")
    if not type(message_ids) is list:
      message_ids = [int(message_ids)]

    result = self.send_query("DeleteMessageMutation", {
      "messageIds": message_ids
    })
  
  def purge_conversation(self, chatbot, count=-1):
    logger.info(f"Purging messages from {chatbot}")
    last_messages = self.get_message_history(chatbot)[::-1]
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
      last_messages = self.get_message_history(chatbot)[::-1]
    logger.info(f"No more messages left to delete.")

load_queries()