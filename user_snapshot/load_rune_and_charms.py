import requests
import json

season = 5
print(f"load charms of season {season}")
headers = {
    'Accept': 'application/json',
    'X-API-Key': 'bca6LjK8Xx96tcu881OrT0TmhnvvngnA'
  }
charms = {}
charms_per_rarity = {}
limit = 100
offset = 0
while True:
  url = f"https://api-gateway.skymavis.com/origins/v2/community/charms?limit={limit}&offset={offset}"
  response = requests.request("GET", url, headers=headers).json()
  items = response['_items']
  has_next = response['_metadata']['hasNext']
  offset += limit
  print('', end = ".", flush = True)
  for item in items:
    charm_id = item['item']['id']
    charms[charm_id] = item['item']['imageUrl']
    if item['season']['id'] == season + 1:
      rarity = item['item']['rarity']
      if not rarity in charms_per_rarity:
        charms_per_rarity[rarity] = []
      charms_per_rarity[rarity].append(charm_id)
  if not has_next:
    break;

# 将数据写入JSON文件
with open('data_charms.json', 'w') as file:
    json.dump(charms, file, indent=4)

with open('data_charms_per_rarity.json', 'w') as file:
    json.dump(charms_per_rarity, file, indent=4)

print('已将数据写入data_charms.json和data_charms_per_rarity.json')


print(f"load runes of season {season}")
headers = {
    'Accept': 'application/json',
    'X-API-Key': 'bca6LjK8Xx96tcu881OrT0TmhnvvngnA'
  }
runes = {}
runes_per_rarity = {}
limit = 100
offset = 0
while True:
  url = f"https://api-gateway.skymavis.com/origins/v2/community/runes?limit={limit}&offset={offset}"
  response = requests.request("GET", url, headers=headers).json()
  items = response['_items']
  has_next = response['_metadata']['hasNext']
  offset += limit
  print('', end = ".", flush = True)
  for item in items:
    charm_id = item['item']['id']
    runes[charm_id] = item['item']['imageUrl']
    if item['season']['id'] == season + 1:
      rarity = item['item']['rarity']
      if not rarity in runes_per_rarity:
        runes_per_rarity[rarity] = []
      runes_per_rarity[rarity].append(charm_id)
  if not has_next:
    break;

# 将数据写入JSON文件
with open('data_runes.json', 'w') as file:
    json.dump(runes, file, indent=4)

with open('data_runes_per_rarity.json', 'w') as file:
    json.dump(runes_per_rarity, file, indent=4)

print('已将数据写入data_runes.json和data_runes_per_rarity.json')