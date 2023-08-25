import requests
import json
import os
import sys
import time
from eth_account.messages import encode_defunct
from eth_account.messages import encode_structured_data
from web3 import Web3


### ============方法定义 start ============
# 根据市场链接查询axie列表
def fetch_axie(mp_url, size):
  # 从文件中读取query内容
  with open('get_brief_list.graphql', 'r') as file:
    query = file.read()

  criteria = parse_criteria(mp_url)
  aution_type = 'Sale'
  sort = 'PriceAsc'
  if 'auctionTypes' in criteria: 
    aution_types = criteria.get('auctionTypes')
    if (len(aution_types) == 2) :
      aution_type = 'All'
    else : 
      aution_type = aution_types[0]
    del criteria['auctionTypes']
  if 'sort' in criteria:
    sort = criteria.get('sort')[0]
    del criteria['sort']
  data = {
    'query': query,
    'variables': {
        'from': 0,
        'size': size,
        'autionType': aution_type,
        'sort': sort,
        'criteria': criteria
    },
    'operationName': 'GetAxieBriefList'
  }
  endpoint = 'https://graphql-gateway.axieinfinity.com/graphql'
  response =  requests.post(endpoint, json = data)
  return response.json()['data']['axies']

def send_offer(signer, access_token, axie, offer_price):
  with open('sign_message_template.json', 'r') as file:
    message = json.load(file)
  order = axie['order']
  asset = order['assets'][0]
  axie_id = axie['id']
  # 注意: 签名时的数据结构和graphql请求时的不太一样
  message['message'] = {
    'maker': order['maker'],
    'kind': 0,
    'assets': [{
      'erc': 1,
      'addr': asset['address'],
      'id': int(axie_id),
      'quantity': int(asset['quantity'])
    }],
    'expiredAt': int(order['expiredAt']),
    'paymentToken': order['paymentToken'],
    'startedAt': int(order['startedAt']),
    'basePrice': int(offer_price),
    'endedAt': int(order['endedAt']),
    'endedPrice': int(order['endedPrice']),
    'expectedState': 0,
    'nonce': int(order['nonce']),
    'marketFeePercentage': int(order['marketFeePercentage'])
  }
  sign_result = signer.sign_message(encode_structured_data(message))
  print(sign_result.signature.hex())
  with open('create_order.graphql', 'r') as file:
    query = file.read()
  data = {
    'query': query,
    'variables': {
        # 注意: 签名时的数据结构和graphql请求时的不太一样
        'order': {
          'assets': [{
            'erc': asset['erc'],
            'address': asset['address'],
            'id': axie_id,
            'quantity': asset['quantity']
          }],
          'basePrice': str(offer_price),
          'endedAt': order['endedAt'],
          'endedPrice': str(order['endedPrice']),
          'expectedState': '61162214077330396652601178591922430472979244393074746123949999818242734682784',
          'expiredAt': order['expiredAt'],
          'kind': 'Offer',
          'nonce': order['nonce'],
          'startedAt': order['startedAt']
        },
        'signature': sign_result.signature.hex(),
    },
    'operationName': 'CreateOrder'
  }

  headers = {
    'authorization': f"Bearer {access_token}" 
  }
  print(data)
  print(headers)

  endpoint = 'https://graphql-gateway.axieinfinity.com/graphql'
  response =  requests.post(endpoint, json = data, headers = headers)
  print(response.text)


def get_token(signer):
  nonce = requests.get('https://athena.skymavis.com/v2/public/auth/ronin/fetch-nonce?address=' + signer.address)
  nonce_json = nonce.json()
  message = f"app.axieinfinity.com wants you to sign in with your Ronin account:\nronin:{signer.address.replace('0x','').lower()}\n\nI accept the Terms of Use (https://axieinfinity.com/terms-of-use) and the Privacy Policy (https://axieinfinity.com/privacy-policy)\n\nURI: https://app.axieinfinity.com\nVersion: 1\nChain ID: 2020\nNonce: {nonce_json['nonce']}\nIssued At: {nonce_json['issued_at']}\nExpiration Time: {nonce_json['expiration_time']}\nNot Before: {nonce_json['not_before']}"
  sign_result = signer.sign_message(encode_defunct(text=message))
  token_response = requests.post(
    'https://athena.skymavis.com/v2/public/auth/ronin/login',
    json = {
      'message':  message,
      'signature': sign_result.signature.hex()
    }
  )
  return token_response.json()['accessToken']



# 从链接中提取查询参数
def parse_criteria(url):
  # 获取查询字符串部分
  query_string = url.split('?')[1]

  # 将查询字符串拆分为键值对
  query_params_list = query_string.split('&')
  query_params = {}

  for param in query_params_list:
    key, value = param.split('=')
    if value.isdigit():
      value = int(value)
    elif key in query_params:
      query_params[key].append(value)
    else:
      query_params[key] = [value]
  return query_params

def log_info(msg):
  current = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())  
  print(f"[{current}] {msg}")

def main(): 
  # 读取配置
  with open('_batch_offer_env', 'r') as file:
    config = json.load(file)
  offer_price = config.get('offer_price')
  offer_count = int(config.get('offer_count'))
  mp_url = config.get('market_place_url')
  private_key = config.get('private_key')
  if (not mp_url.startswith("https://app.axieinfinity.com/marketplace/axies/")): 
    sys.exit("无效的链接市场链接，请检查_buy_axie_env文件中的market_place_url参数")
  if offer_count > 100 :
    sys.exit("最多发送100个OFFER")

  print(f'市场链接: {mp_url}')
  print(f'OFFER价格: {offer_price}')
  print(f'发送OFFER数量: {offer_count}')

  input("\033[0;31;40m请确认上述配置是否有误, 确认无误后按回车键继续:\033[0m")

  # 查询列表
  axie_list = fetch_axie(mp_url, 100)
  
  results = axie_list['results']
  if (len(results) == 0) :
    print("未查到符合条件的axie")
    return

  ronin_rpc = 'https://api.roninchain.com/rpc'
  provider = Web3.HTTPProvider(ronin_rpc)
  w3 = Web3(provider)
  signer = w3.eth.account.from_key(private_key)
  access_token = get_token(signer)
  # 发送OFFER
  offer_count = 0
  for axie in results:
    send_offer(signer, access_token, axie, Web3.to_wei(offer_price, 'ether'))
    break;



### ============方法定义 end =============
try: 
  main()
except KeyboardInterrupt:
    print('')
    print('取消脚本执行')
### ============脚本执行 start =============

