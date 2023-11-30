import requests
import json
import os
import sys
from datetime import datetime, timedelta
from eth_account.messages import encode_defunct
from eth_account.messages import encode_structured_data
from web3 import Web3

### ============方法定义 start ============
def sell_axie(signer, access_token, axie_id, price_eth):
  with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sign_message_template.json'), 'r') as file:
    message = json.load(file)
  # 注意: 签名时的数据结构和graphql请求时的不太一样
  started_at = int(datetime.now().timestamp())
  expired_at = int((datetime.now() + timedelta(days=184)).timestamp())
  payment_token = '0xc99a6a985ed2cac1ef41640596c5a5f9f4e19ef5'
  axie_address = '0x32950db2a7164ae833121501c797d79e7b79d74c'
  message['message'] = {
    'maker': signer.address,
    'kind': 1,
    'assets': [{
      'erc': 1,
      'addr': axie_address,
      'id': int(axie_id),
      'quantity': 0
    }],
    'expiredAt': expired_at,
    'paymentToken': payment_token,
    'startedAt': started_at,
    'basePrice': Web3.to_wei(price_eth, 'ether'),
    'endedAt': 0,
    'endedPrice': 0,
    'expectedState': 0,
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
          'basePrice': str(Web3.to_wei(price_eth, 'ether')),
          'endedAt': 0,
          'endedPrice': "0",
          'expectedState': "",
          'expiredAt': expired_at,
          'kind': 'Sell',
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
    print('挂单失败:' + response.json()['errors'][0]['message'])
  else:
    print(f'挂单成功,axie_id={axie_id}, price={price_eth}')


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


# 发送graphql请求
def graphql(data): 
  endpoint = 'https://graphql-gateway.axieinfinity.com/graphql'
  headers = {
  }
  return requests.post(endpoint, json = data, headers = headers)

def main(axie_id, price): 
  # 读取配置
  with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_sell_axie_env'), 'r') as file:
    config = json.load(file)
  private_key = config.get('private_key')
  ronin_rpc = 'https://api.roninchain.com/rpc'
  provider = Web3.HTTPProvider(ronin_rpc)
  w3 = Web3(provider)
  signer = w3.eth.account.from_key(private_key)
  access_token = get_token(signer)
  # 上架 axie
  sell_axie(signer, access_token, axie_id, price)



### ============方法定义 end =============
try: 
  main(sys.argv[1], sys.argv[2])
except Exception as ex:
  print(ex)
### ============脚本执行 start =============

