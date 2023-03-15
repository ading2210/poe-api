import requests, re, json, random, logging
from contextlib import closing
from websocket import create_connection
from pathlib import Path

parent_path = Path(__file__).resolve().parent
queries_path = parent_path / "graphql"
queries = {}

logging.basicConfig()
logger = logging.getLogger()

def load_queries():
  for path in queries_path.iterdir():
    with open(path) as f:
      queries[path.stem] = f.read()

def generate_payload(query_name, variables):
  return {
    "queryName": query_name,
    "query": queries[query_name],
    "variables": variables
  }

class Poe:
  gql_url = "https://poe.com/api/gql_POST"
  home_url = "https://poe.com"
  settings_url = "https://poe.com/api/settings"

  formkey = ""
  next_data = {}
  bots = {}
  
  def __init__(self, cookie):
    self.session = requests.Session()

    self.cookie = cookie
    self.headers = {
      "Cookie": cookie,
      "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0",
      "Referrer": "https://poe.com/",
      "Origin": "https://poe.com",
    }

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
    r = self.session.get(self.home_url)
    json_regex = r'<script id="__NEXT_DATA__" type="application\/json">(.+?)</script>'
    json_text = re.search(json_regex, r.text).group(1)
    next_data = json.loads(json_text)

    self.formkey = next_data["props"]["formkey"]
    self.viewer = next_data["props"]["pageProps"]["payload"]["viewer"]
    
    return next_data
  
  def get_bots(self):
    bot_list = self.next_data["props"]["pageProps"]["payload"]["viewer"]["availableBots"]
    bots = {}
    for bot in bot_list:
      url = f'https://poe.com/_next/data/{self.next_data["buildId"]}/{bot["displayName"].lower()}.json'
      logger.info("Downloading "+url)
      r = self.session.get(url)

      r.raise_for_status()
      chat_data = r.json()["pageProps"]["payload"]["chatOfBotDisplayName"]
      bots[chat_data["defaultBotObject"]["nickname"]] = chat_data
          
    return bots
  
  def get_bot_names(self):
    bot_names = {}
    for bot_nickname in self.bots:
      bot_obj = self.bots[bot_nickname]["defaultBotObject"]
      bot_names[bot_nickname] = bot_obj["displayName"]
    return bot_names
  
  def get_channel_data(self):
    logger.info("Downloading channel data...")
    r = self.session.get(self.settings_url)
    return r.json()["tchannelData"]
  
  def send_query(self, query_name, variables):
    payload = generate_payload(query_name, variables)
    r = self.session.post(self.gql_url, json=payload, headers=self.gql_headers)
    return r.json()
  
  def subscribe(self):
    result = self.send_query("AutoSubscriptionMutation", {
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
    result = self.send_query("AddHumanMessageMutation", {
      "bot": chatbot,
      "query": message,
      "chatId": self.bots[chatbot]["chatId"],
      "source": None,
      "withChatBreak": with_chat_break
    })
        
  def get_websocket_url(self, channel=None):
    if channel is None:
      channel = self.channel
    query = f'?min_seq={channel["minSeq"]}&channel={channel["channel"]}&hash={channel["channelHash"]}'
    return f'wss://tch{random.randint(1, 1e6)}.tch.{channel["baseHost"]}/up/{channel["boxName"]}/updates'+query

load_queries()