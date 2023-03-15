import requests, re, json, random, logging
import websocket
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

class Poe:
  gql_post = "https://poe.com/api/gql_POST"
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

    self.gql_headers = {
      "poe-formkey": self.formkey,
      "poe-tchannel": self.channel["channel"],
    }
    self.gql_headers = {**self.gql_headers, **self.headers}
    
  def get_next_data(self):
    logger.info("Downloading next_data...")
    r = self.session.get(self.home_url)
    json_regex = r'<script id="__NEXT_DATA__" type="application\/json">(.+?)</script>'
    json_text = re.search(json_regex, r.text).group(1)
    next_data = json.loads(json_text)

    self.formkey = next_data["props"]["formkey"]
    self.bots = next_data["props"]["pageProps"]["payload"]["viewer"]["availableBots"]
    self.viewer = next_data["props"]["pageProps"]["payload"]["viewer"]
    
    return next_data
  
  def get_channel_data(self):
    logger.info("Downloading channel data...")
    r = self.session.get(self.settings_url)
    return r.json()["tchannelData"]
  
  def get_websocket_url(self, channel=None):
    if channel is None:
      channel = self.channel
    query = f'?min_seq={channel["minSeq"]}&channel={channel["channel"]}&hash={channel["channelHash"]}'
    return f'wss://tch{random.randint(1, 1e6)}.tch.{channel["baseHost"]}/up/{channel["boxName"]}/updates'+query

load_queries()