import requests
import json


# 查询战斗记录列表
def list_battles(user_id): 
  url = f"https://api-gateway.skymavis.com/x/origin/battle-history?type=pvp&limit=100&client_id={user_id}"
  headers = {
    'Accept': 'application/json',
    'X-API-Key': 'bca6LjK8Xx96tcu881OrT0TmhnvvngnA'
  }
  response = requests.request("GET", url, headers=headers)
  return response.json()['battles']

# 查询用户资产
def list_user_items(user_id, item_ids, images):
  url_prefix = f"https://api-gateway.skymavis.com/origins/v2/community/users/{user_id}/items?limit=100&"
  headers = {
    'Accept': 'application/json',
    'X-API-Key': 'bca6LjK8Xx96tcu881OrT0TmhnvvngnA'
  }
  url = url_prefix + '&'.join(f'itemIDs={item_id}' for item_id in item_ids)
  response = requests.request("GET", url, headers=headers).json()
  items = {}
  for item in response['_items']:
    item_id = item['itemId']
    quantity = item['quantity']
    if quantity > 0:
      item['image_url'] = images.get(item_id, '')
      items[item_id] = item
  return items

# 是否是先手
def is_first_player(battle, user_id):
  user_index = battle['client_ids'].index(user_id)
  return user_index == 0
def get_rune_image(rune_id):
  return f"https://axies.io/_next/image?url=https%3A%2F%2Fstorage.googleapis.com%2Forigin-production%2Fassets%2Fitem%2F{rune_id}.png&w=48&q=75"

# 查询用户数据
def extract_user_info(user_id, all_runes, all_charms):
  print('查询对战信息', end = "...", flush = True)
  battles = list_battles(user_id)
  data = {}
  latest_battle = battles[0]
  rewards = latest_battle['rewards']
  for reward in rewards:
    if (reward['user_id'] == user_id) :
      data['stars'] = reward['new_vstar']
  if is_first_player(latest_battle, user_id):
    data['fighters'] = latest_battle['first_client_fighters']
  else:
    data['fighters'] = latest_battle['second_client_fighters']
  for fighter in data['fighters']:
    if len(fighter['runes']) > 0:
      rune_id = fighter['runes'][0]
      fighter['rune_image'] = all_runes.get(rune_id, get_rune_image(rune_id))
    charm_images = {}
    for key,charm_id in fighter['charms'].items():
      charm_image_url = all_charms.get(charm_id, '')
      charm_images[key] = charm_image_url
    fighter['charm_images'] = charm_images

  total = len(battles)
  win_count = 0  
  lose_count = 0 
  first_count = 0 
  second_count = 0
  first_win_count = 0
  first_lose_count = 0
  second_win_count = 0
  second_lose_count = 0

  for battle in battles: 
    winner = battle['winner']
    if is_first_player(battle, user_id): # 先手
      first_count += 1
      if (winner == 0) :
          win_count += 1
          first_win_count += 1
      if (winner == 1):
          lose_count += 1
          first_lose_count += 1
    else : # 后手
      second_count += 1
      if (winner == 0) :
        lose_count += 1
        second_lose_count += 1
      if (winner == 1):
        win_count += 1
        second_win_count += 1

  data['battle'] = {
    'total': total,
    'win_count': win_count,
    'lose_count': lose_count,
    'first_count': first_count,
    'second_count': second_count,
    'first_win_count': first_win_count,
    'first_lose_count': first_lose_count,
    'second_win_count': second_win_count,
    'second_lose_count': second_lose_count,
  }
  print('查询资产', end = "", flush = True)
  general_item_ids = [
    "crafting_exp", "emaxs", "maxs", 'honor_medal', "moonshard", "moon_crystal",
    "slp", "selection_class_material_01"
  ]
  data['general_items'] = list_user_items(user_id, general_item_ids, {})
  print('', end = ".", flush = True)
  # runes
  with open('data_runes_per_rarity.json', 'r') as file:
    runes = json.load(file)
  for rarity, rune_ids  in runes.items():
    if rarity not in ['Rare', 'Epic', 'Mystic']:
      continue
    data['rune_items_' + rarity] = list_user_items(user_id, rune_ids, all_runes)
  print('', end = ".", flush = True)


  # charms
  with open('data_charms_per_rarity.json', 'r') as file:
    charms = json.load(file)
  for rarity, charm_ids  in charms.items():
    if rarity not in ['Rare', 'Epic', 'Mystic']:
      continue
    data['charm_items_' + rarity] = list_user_items(user_id, charm_ids, all_charms)
  print('', end = ".", flush = True)
  return data

datas = {}
# user_map
with open('data_user_map.json', 'r') as file:
  user_map = json.load(file)
for user_id, user_name in user_map.items():
  print(f"用户[{user_name}]开始处理", end = "...", flush = True)
  # 从文件中读取charms数据
  with open('data_charms.json', 'r') as json_file:
      all_charms = json.load(json_file)
  # 从文件中读取runes数据
  with open('data_runes.json', 'r') as json_file:
      all_runes = json.load(json_file)
  data = extract_user_info(user_id, all_runes, all_charms)
  data['user_name'] = user_name
  datas[user_id] = data
  print("处理完成")

with open('index_template.html', 'r') as template_file:
    template = template_file.read()

# Fill the template with data
filled_template = template.replace('[...]', str(datas))

# Save the filled template to an HTML file
with open('index.html', 'w') as output_file:
    output_file.write(filled_template)
print('数据写入index.html页面，打开页面查看数据')

