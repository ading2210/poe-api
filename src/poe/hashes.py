import tls_client as requests_tls
import poe
import re
import json
import pathlib

#running this file will export the gql query ids to poe_graphql/queries.json

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
  manifest_regex = r'https://psc2\.cf2\.poecdn\.net/[0-9a-f]{40}/_next/static/\S{21}/_buildManifest\.js'
  base_regex = r'https://psc2\.cf2\.poecdn\.net/[0-9a-f]{40}/_next/'
  manifest_url = re.findall(manifest_regex, r.text)[0]
  base_url = re.findall(base_regex, r.text)[0]

  r2 = session.get(manifest_url)
  resources_regex = r'"(static/.+?)"'
  resources_list = re.findall(resources_regex, r2.text)

  queries = {}
  for resource in resources_list:
    if not resource.endswith(".js"):
      continue
    url = base_url + resource

    r3 = session.get(url)
    hashes_regex = r'params:{id:"([0-9a-f]{64})".+?name:"(\S+?)"'
    hashes_list = re.findall(hashes_regex, r3.text)

    for query_hash, query_name in hashes_list:
      if "_" in query_name:
        query_name = query_name.split("_")[1]
      query_name = query_name[0].upper()+query_name[1:]
      queries[query_name] = query_hash

  out_path = poe.queries_path / "queries.json"
  json_text = json.dumps(queries, indent=2, sort_keys=True)
  out_path.write_text(json_text)