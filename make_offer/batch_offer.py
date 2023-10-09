import requests
import json
import os
import sys
from datetime import datetime, timedelta
from eth_account.messages import encode_defunct
from eth_account.messages import encode_structured_data
from web3 import Web3

### ============方法定义 start ============
# 根据市场链接查询axie列表
def fetch_axie(mp_url, size):
  # 从文件中读取query内容
  with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'get_brief_list.graphql'), 'r') as file:
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

def get_expected_state(axie_id):
  url = "https://api-gateway.skymavis.com/rpc"
  mp_contract_address = '0xfff9ce5f71ca6178d3beecedb61e7eff1602950e'
  # 不清楚下面数据的生成规则 ，但通过对比知道只需要替换其中和axie_id有关的部分就可以了
  data = f"0x95a4ec0000000000000000000000000000000000000000000000000000000000000000400000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000000e4f524445525f45584348414e474500000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c4f99fdd2800000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000032950db2a7164ae833121501c797d79e7b79d74c000000000000000000000000{format(int(axie_id), 'x').zfill(40)}000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
  payload = json.dumps({
    'id': 50,
    'jsonrpc': '2.0',
    'params': [
      {
        'to': mp_contract_address,
        'data': data
      },
      'latest'
    ],
    'method': 'eth_call'
  })
  headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'X-API-Key': 'bca6LjK8Xx96tcu881OrT0TmhnvvngnA'
  }
  response = requests.request("POST", url, data=payload, headers = headers)
  return response.json()['result']


def send_offer(signer, access_token, axie, offer_price):
  with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sign_message_template.json'), 'r') as file:
    message = json.load(file)
  axie_id = axie['id']
  # 注意: 签名时的数据结构和graphql请求时的不太一样
  started_at = int(datetime.now().timestamp())
  expired_at = int((datetime.now() + timedelta(days=3)).timestamp())
  expected_state =  int(get_expected_state(axie_id), 16)
  payment_token = '0xc99a6a985ed2cac1ef41640596c5a5f9f4e19ef5'
  axie_address = '0x32950db2a7164ae833121501c797d79e7b79d74c'
  message['message'] = {
    'maker': signer.address,
    'kind': 0,
    'assets': [{
      'erc': 1,
      'addr': axie_address,
      'id': int(axie_id),
      'quantity': 0
    }],
    'expiredAt': expired_at,
    'paymentToken': payment_token,
    'startedAt': started_at,
    'basePrice': int(offer_price),
    'endedAt': 0,
    'endedPrice': 0,
    'expectedState': expected_state,
    'nonce': 0,
    'marketFeePercentage': 425
  }
  sign_result = signer.sign_message(encode_structured_data(message))
  with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'create_order.graphql'), 'r') as file:
    query = file.read()
  data = {
    'query': query,
    'variables': {
        # 注意: 签名时的数据结构和graphql请求时的不太一样
        'order': {
          'assets': [{
            'erc': 'Erc721',
            'address': axie_address,
            'id': axie_id,
            'quantity': '0'
          }],
          'basePrice': str(offer_price),
          'endedAt': 0,
          'endedPrice': "0",
          'expectedState': str(expected_state),
          'expiredAt': expired_at,
          'kind': 'Offer',
          'nonce': 0,
          'startedAt': started_at
        },
        'signature': sign_result.signature.hex(),
    },
    'operationName': 'CreateOrder'
  }

  headers = {
    'authorization': f"Bearer {access_token}" 
  }
  endpoint = 'https://graphql-gateway.axieinfinity.com/graphql'
  response =  requests.post(endpoint, json = data, headers = headers)
  if 'errors' in response.json():
    print(response.json()['errors'][0]['message'])
  else:
    print('offer success')


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
    if key == 'excludeParts':
      key = 'parts'
      value = '!' + value
    if key in ['sort', 'page']:
      continue
    elif key in query_params:
      query_params[key].append(value)
    else:
      query_params[key] = [value]

  return query_params

def main(): 
  # 读取配置
  with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_batch_offer_env'), 'r') as file:
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

  # 查询列表
  axie_list = fetch_axie(mp_url, 100)
  results = axie_list['results']
  if len(results) == 0:
    print('未查到符合查询条件的记录')
    return
  floor_axie = results[0]
  floor_info = f",第一个符合条件的ID为{floor_axie['id']}"
  order = floor_axie['order']

  if order is not None:
    floor_info += f",价格为:{Web3.from_wei(int(order['currentPrice']), 'ether')}"
  else:
    floor_info += ',未出售'
  print(f"共有{axie_list['total']}符合条件的记录,返回结果数量:{len(results)}{floor_info}")
  input("\033[0;31;40m请确认上述配置是否有误, 确认无误后按回车键继续:\033[0m")

  ronin_rpc = 'https://api.roninchain.com/rpc'
  provider = Web3.HTTPProvider(ronin_rpc)
  w3 = Web3(provider)
  signer = w3.eth.account.from_key(private_key)
  access_token = get_token(signer)
  # 发送OFFER
  count = 0
  for axie in results:
    print(f"send offer to {axie['id']}", end = ' ... ')
    send_offer(signer, access_token, axie, Web3.to_wei(offer_price, 'ether'))
    count += 1
    if count >= offer_count:
      break;


### ============方法定义 end =============
try: 
  main()
except KeyboardInterrupt:
    print('')
    print('取消脚本执行')
### ============脚本执行 start =============

