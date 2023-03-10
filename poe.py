import requests, re, json

class Poe:
  gql_post = "https://poe.com/api/gql_POST"
  gql_post_recieve = "https://poe.com/api/gql_POST"
  home_url = "https://poe.com"

  formkey = ""
  next_data = {}
  bots = {}
  global_headers = {}
  
  def __init__(self, cookie):
    self.cookie = cookie
    self.global_headers["cookie"] = cookie
    self.session = requests.Session()
    self.get_next_data()

  def get_next_data(self):
    r = self.session.get(self.home_url, headers=self.global_headers)
    json_regex = r'<script id="__NEXT_DATA__" type="application\/json">(.+?)</script>'
    json_text = re.search(json_regex, r.text).group(1)
    self.next_data = json.loads(json_text)

    self.formkey = self.next_data["props"]["formkey"]
    self.bots = self.next_data["props"]["pageProps"]["payload"]["viewer"]["availableBots"]
    self.viewer = self.next_data["props"]["pageProps"]["payload"]["viewer"]
    
    return self.next_data
