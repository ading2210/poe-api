import tls_client as requests_tls
import poe
import re

if __name__ == "__main__":
  session = requests_tls.Session(client_identifier="chrome112")
  headers = {**poe.headers, **{
    "Cache-Control": "no-cache",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
  }}
  session.headers.update(headers)

  r = session.get("https://poe.com/login?redirect_url=%2F")
  scripts_regex = r'\"(https://psc2\.cf2\.poecdn\.net/[0-9a-f]{40}/_next/static/chunks.+?.js)"'
  script_urls = re.findall(scripts_regex, r.text)
  
  for url in script_urls:
    r2 = session.get(url)
    hashes_regex = r'params:{id:"([0-9a-f]{64})".+?name:"(\S+?)"'
    hashes_list = re.findall(hashes_regex, r2.text)

    for query_hash, query_name in hashes_list:
      if "_" in query_name:
        query_name = query_name.split("_")[1]
      print(query_hash, query_name)