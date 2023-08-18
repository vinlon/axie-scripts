import requests
import json
import os
import sys
import time
from eth_account.messages import encode_defunct
from web3 import Web3

def list_my_axies(address):
  # 从文件中读取query内容
  with open('get_brief_list.graphql', 'r') as file:
    query = file.read()

  data = {
    'query': query,
    'variables': {
        'criteria': {
            "level": [9, 30]
        },
        'owner': address
    },
    'operationName': 'GetAxieBriefList'
  }
  endpoint = 'https://graphql-gateway.axieinfinity.com/graphql'
  response =  requests.post(endpoint, json = data)
  return response.json()['data']['axies']['results']

def ascend_axie_level_message(axie_id, access_token):
  with open('ascend_axie_level_message.graphql', 'r') as file:
    query = file.read()

  data = {
    'query': query,
    'variables': {
      'axieId': axie_id
    },
    'operationName': 'GetAscendLevelMessage'
  }
  headers = {
    'authorization': f"Bearer {access_token}" 
  }

  endpoint = 'https://graphql-gateway.axieinfinity.com/graphql'
  response = requests.post(endpoint, json = data, headers = headers)
  print(response.text)
  return response.json()['data']['ascendAxieLevelMessage']

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


def ascend(message, signer, w3): 
  axp_contract_address='0x32950db2a7164ae833121501c797d79e7b79d74c'
  abi_file_path = os.path.abspath('ascend_abi.json')
  with open(abi_file_path, 'r') as file:
      abi = json.load(file)
  axp_contract = w3.eth.contract(
      address=Web3.to_checksum_address(axp_contract_address), 
      abi=abi
  )

  axie_infinity_shard_address = '0x97a9107c1793bc407d6f527b77e7fff4d812bece'
  wrapped_ron_address = '0xe514d9deb7966c8be0ca922de8a064264ea6bcd4'
  usd_coin_address = '0x0b7007c13325c48911f73a2dad5fa5dcbf808adc'

  transaction = axp_contract.functions.ascendLevel(
    int(message['axieId']),
      int(message['level']),
      int(message['deadline']),
      [
         Web3.to_checksum_address(axie_infinity_shard_address),
         Web3.to_checksum_address(wrapped_ron_address),
         Web3.to_checksum_address(usd_coin_address),
      ],
      message['signature']
  ).build_transaction({
      'chainId': 2020,
      'nonce': w3.eth.get_transaction_count(signer.address),
      'gasPrice': w3.to_wei(20, 'gwei')
  })
  
  signed_txn = signer.sign_transaction(transaction)
  tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
  return w3.eth.wait_for_transaction_receipt(tx_hash)

def main(private_key): 
  ronin_rpc = 'https://api.roninchain.com/rpc'
  provider = Web3.HTTPProvider(ronin_rpc)
  w3 = Web3(provider)
  signer = w3.eth.account.from_key(private_key)
  print(f'账号: {signer.address} 开始检索')
  
  # 查询符合条件的axie
  list = list_my_axies(signer.address)
  # 获取登录token
  access_token = get_token(signer)

  # 遍历所有axie, 符合条件的进行升级
  for axie in list:
    axie_id = axie['id']
    shouldAscend = axie['axpInfo']['shouldAscend']
    level = axie['axpInfo']['level']
    if not shouldAscend: 
      continue
    print(f"  发现符合条件的axie, ID={axie_id}, level={level}, 开始升级", end = "")
    message = ascend_axie_level_message(axie_id, access_token)
    tx_receipt = ascend(message, signer, w3)

    gas_used = Web3.from_wei(tx_receipt.gasUsed, 'ether') * Web3.to_wei(20, 'gwei');
    transaction_hash = tx_receipt.transactionHash.hex()
    if tx_receipt.status == 1:
      print(f",升级成功, 消耗gas: {gas_used}, 交易哈希: {transaction_hash}")
    else:
      print(f",升级失败, 消耗gas:{gas_used}, 交易哈希: {transaction_hash}")



# 从.blessing_keys文件中读取想要祈福的账号
with open('_batch_ascend_env', 'r') as file:
  # 使用 json.load() 方法加载数据
  keys = json.load(file)

# 遍历所有账号，挨个祈福
for key in keys:
  main(key)

