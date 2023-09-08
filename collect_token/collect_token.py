import requests
import json
import os
import sys
from eth_account.messages import encode_defunct
from web3 import Web3

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

def prepare_slp_withdraw(signer, amount):
  endpoint = 'https://game-api-origin.skymavis.com/v2/rpc/items/withdraw'
  token = get_token(signer)
  headers = {
    'authorization': f"Bearer {token}"
  }
  data = {"items":[{"amount":amount,"itemId":"slp"}]}
  response = requests.post(endpoint, json = data, headers = headers)
  return response.json()

def withdraw_slp(w3, signer, amount):
  axs_contract_address = Web3.to_checksum_address('0x97a9107c1793bc407d6f527b77e7fff4d812bece')
  payment_token = Web3.to_checksum_address('0xc99a6a985ed2cac1ef41640596c5a5f9f4e19ef5')
  usd_coin_address = Web3.to_checksum_address('0x0b7007c13325c48911f73a2dad5fa5dcbf808adc')
  portal_contract_address = Web3.to_checksum_address('0x36b628e771b0ca12a135e0a7b8e0394f99dce95b')

  with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'withdraw_abi.json'), 'r') as file:
    abi = json.load(file)
  portal_contract = w3.eth.contract(address=portal_contract_address, abi=abi)
  data = prepare_slp_withdraw(signer, amount);
  if '_errorMessage' in data:
    raise Exception(data.get('_errorMessage'))
  item = data['items'][0]
  transaction = portal_contract.functions.withdraw(
    [
        Web3.to_checksum_address(data.get('userAddress')),
        data.get('nonce'),
        data.get('expiredAt'),
        [[
            0,
            Web3.to_checksum_address(item.get('tokenAddress')),
            int(item.get('tokenId')),
            int(item.get('signedAmount')),
            int(item.get('tokenRarity'))
        ]],
        data.get('extraData')
    ],
    data.get('signature'),
    [
      axs_contract_address,
      payment_token,
      usd_coin_address
    ]
  ).build_transaction({
      'chainId': 2020,
      'gas': 400000,
      'gasPrice': Web3.to_wei(20, 'gwei'),
      'nonce': w3.eth.get_transaction_count(signer.address),
  })
  signed_txn = signer.sign_transaction(transaction)
  tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
  return w3.eth.wait_for_transaction_receipt(tx_hash)

# 查询用户SLP
def query_slp(address):
  profile = get_profile(address)
  user_id = profile['accountId']
  url = f"https://api-gateway.skymavis.com/origins/v2/community/users/{user_id}/items?itemIDs=slp"
  headers = {
    'Accept': 'application/json',
    'X-API-Key': 'bca6LjK8Xx96tcu881OrT0TmhnvvngnA'
  }
  response = requests.request("GET", url, headers=headers).json()
  return response['_items'][0]

def send_token(w3, contract, signer, amount, receiver):
  transaction = contract.functions.transfer(
      Web3.to_checksum_address(receiver),
      amount
  ).build_transaction({
      'chainId': 2020,
      'gas': 100000,
      'gasPrice': w3.to_wei('20', 'gwei'),
      'nonce': w3.eth.get_transaction_count(signer.address)
  })
  signed_tx = signer.sign_transaction(transaction)
  tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
  return w3.eth.wait_for_transaction_receipt(tx_hash)

def short_address(address):
  return address[2:6] + '...' + address[-4:] 

def display_axs(balance):
  balance_eth = Web3.from_wei(balance, 'ether')
  return f"{balance_eth:.6f}"

def main():
  with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_collect_token_env'), 'r') as file:
    config = json.load(file)
  with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'token_abi.json'), 'r') as file:
    abi = json.load(file)

  ronin_rpc = 'https://api.roninchain.com/rpc'
  slp_contract_address = Web3.to_checksum_address('0xa8754b9fa15fc18bb59458815510e40a12cd2014')
  axs_contract_address = Web3.to_checksum_address('0x97a9107c1793bc407d6f527b77e7fff4d812bece')
  provider = Web3.HTTPProvider(ronin_rpc)
  w3 = Web3(provider)
  slp_contract = w3.eth.contract(address=slp_contract_address, abi=abi)
  axs_contract = w3.eth.contract(address=axs_contract_address, abi=abi)

  print('1. 查询游戏内可提现SLP')
  print("{:<15} {:<15} {:<15}".format("ADDRESS", "GAME_SLP", "可提现_SLP"))
  for private_key in config.get('accounts', []):
    signer = w3.eth.account.from_key(private_key)
    slp = query_slp(signer.address)
    print("{:<15} {:<15} {:<15}".format(
      short_address(signer.address),
      slp.get('quantity', 0),
      slp.get('withdrawable', 0),
      "WITHDRAWABLE"
    ))
  user_input = input("\033[0;31;40m是否自动提现SLP(yes/no)? \033[0m")
  if user_input == "yes":
    # 提现
    print('1.1 开始提现')
    withdraw_count = 0
    withdraw_total_amount = 0
    for private_key in config.get('accounts', []):
      signer = w3.eth.account.from_key(private_key)
      address = signer.address
      withdraw_amount = 1
      try:
        tx_receipt = withdraw_slp(w3, signer, 1)
        gas_used = Web3.from_wei(tx_receipt.gasUsed, 'ether') * Web3.to_wei(20, 'gwei');
        if tx_receipt.status == 1:
          result = f'提现成功({withdraw_amount} slp), 消耗gas = {gas_used:.6f} ron'
          withdraw_count += 1
          withdraw_total_amount += withdraw_count
        else:
          result = '提现失败'

      except Exception as e :
        result = '提现失败:' + str(e.args[0]) if e.args else "未知错误"
      print(f"{short_address(address)}: {result}")
      print(f"# 提现成功账户数量:{withdraw_count}, 提现总金额：{withdraw_total_amount} slp")
  else:
    print("\033[0;31;40m放弃提现\033[0m")

  print('2. 查询账户余额')
  print("{:<15} {:<15} {:<15}".format("ADDRESS", "WALLET_SLP", "WALLET_AXS"))
  for private_key in config.get('accounts', []):
    signer = w3.eth.account.from_key(private_key)
    address = signer.address
    slp_balance = slp_contract.functions.balanceOf(address).call()
    axs_balance = axs_contract.functions.balanceOf(address).call()
    print("{:<15} {:<15} {:<15}".format(
      short_address(address),
      slp_balance,
      display_axs(axs_balance)
    ))
  receiver = config.get('receiver')
  user_input = input(f"\033[0;31;40m是否将所有SLP和AXS转账到指定账户({short_address(receiver)})(yes/no)? \033[0m")
  if user_input == "yes":
    # 提现
    print('2.1 开始转账')
    axs_total = 0
    slp_total = 0
    for private_key in config.get('accounts', []):
      signer = w3.eth.account.from_key(private_key)
      address = signer.address
      print(f"[{short_address(address)}] ", end = '', flush = True)
      slp_amount = 1
      axs_amount = w3.to_wei('0.1', 'ether')
      slp_tx_receipt = send_token(w3, slp_contract, signer, slp_amount, receiver)
      slp_gas_used = Web3.from_wei(slp_tx_receipt.gasUsed, 'ether') * Web3.to_wei(20, 'gwei');
      if slp_tx_receipt.status == 1:
        slp_total += slp_amount
        print(f"SLP转账成功({slp_amount} slp)", end = ',', flush = True)
      else: 
        print('SLP转账失败', end = ',', flush = True)
      axs_tx_receipt = send_token(w3, axs_contract, signer, axs_amount, receiver)
      axs_gas_used = Web3.from_wei(slp_tx_receipt.gasUsed, 'ether') * Web3.to_wei(20, 'gwei');
      if axs_tx_receipt.status == 1:
        axs_total += axs_amount
        print(f"AXS转账成功({w3.from_wei(axs_amount, 'ether')} axs)")
      else: 
        print('AXS转账失败')
      print(f"# SLP总金额：{slp_total}, AXS总金额: {w3.from_wei(axs_total, 'ether')}")
      
  else:
    print("\033[0;31;40m放弃转账\033[0m")
  user_input = input("\033[0;31;40m是否查看账户最终状态(yes/no)? \033[0m")
  if user_input != "yes":
    print("\033[0;31;40m放弃查看，执行结束\033[0m")
    return
  print('3.1 查询账户状态')
  print("{:<15} {:<15} {:<15} {:<15} {:<15}".format("ADDRESS", "GAME_SLP", "WALLET_SLP", "WALLET_AXS", "可提现_SLP"))
  for private_key in config.get('accounts', []):
    signer = w3.eth.account.from_key(private_key)
    address = signer.address
    slp = query_slp(address)
    slp_balance = slp_contract.functions.balanceOf(address).call()
    axs_balance = axs_contract.functions.balanceOf(address).call()
    print("{:<15} {:<15} {:<15} {:<15} {:<15}".format(
      short_address(signer.address),
      slp.get('quantity', 0),
      slp_balance,
      display_axs(axs_balance),
      slp.get('withdrawable', 0)
    ))

try: 
  main()
except KeyboardInterrupt:
    print('取消脚本执行')

