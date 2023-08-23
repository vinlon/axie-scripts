import requests
import json

# 查询用户信息
def get_profile(address):
  data = {
    'query': 'query getProfileWithAddress($address: String) {publicProfileWithRoninAddress(roninAddress: $address) {accountId name } }',
    'variables': {
        'address': address
    },
    'operationName': 'getProfileWithAddress'
  }
  endpoint = 'https://graphql-gateway.axieinfinity.com/graphql'
  response =  requests.post(endpoint, json = data)
  return response.json()['data']['publicProfileWithRoninAddress']


# 从文件中读取query内容
with open('user_snapshot_env', 'r') as file:
  addresses = json.load(file)

print(f"从user_snapshot_env文件中读取用户地址, 共{len(addresses)}个")
print(f"根据地址获取用户ID和用户名")
user_map = {}
for address in addresses:
  print('.' , end = '', flush = True)
  profile = get_profile(address)
  user_id = profile['accountId']
  name = profile['name']
  user_map[user_id] = name

# 将数据写入JSON文件
with open('data_user_map.json', 'w') as file:
    json.dump(user_map, file, indent=4)
print(f"已将用户数据写入文件data_user_map.json")

