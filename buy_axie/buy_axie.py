import requests
import json
import os
import sys
import time
from web3 import Web3



### ============方法定义 start ============
# 根据市场链接查询axie列表
def fetch_axie(mp_url, size):
  # 从文件中读取query内容
  with open('get_brief_list.graphql', 'r') as file:
    query = file.read()

  data = {
    'query': query,
    'variables': {
        'from': 0,
        'size': size,
        'criteria': parse_criteria(mp_url)
    },
    'operationName': 'GetAxieBriefList'
  }
  endpoint = 'https://graphql-gateway.axieinfinity.com/graphql'
  response =  requests.post(endpoint, json = data)
  return response.json()['data']['axies']

def buy_axie(axie, private_key, gas_price):
  # 合约地址: https://app.roninchain.com/address/ronin:fff9ce5f71ca6178d3beecedb61e7eff1602950e
  mp_contract_address='0xfff9ce5f71ca6178d3beecedb61e7eff1602950e'
  # 这个invitor_address等同于账号里的邀请码功能，每笔交易成功后会官方会从收取的4.25%交易手续费中转1%到这个账户
  # 你也可以将它改为自己的购买账号以外的"其它"账号
  invitor_address = '0x8faf2b3f378d1ccb796b1e3adb1adf0a1a5e679d'
  ronin_rpc = 'https://api.roninchain.com/rpc'
  abi_file_path = os.path.abspath('marketplace_abi.json')
  provider = Web3.HTTPProvider(ronin_rpc)
  w3 = Web3(provider)

  with open(abi_file_path, 'r') as file:
      abi = json.load(file)
  mp_contract = w3.eth.contract(
      address=Web3.to_checksum_address(mp_contract_address), 
      abi=abi
  )
  signer = w3.eth.account.from_key(private_key)
  address = signer.address

  order = axie['order']
  data = mp_contract.encodeABI(fn_name='settleOrder', args=[
      [
          Web3.to_checksum_address(order['maker']),
          int(order['kind'] == 'Sell'),
          [[
              1,
              Web3.to_checksum_address(order['assets'][0]['address']),
              int(order['assets'][0]['id']),
              int(order['assets'][0]['quantity'])
          ]],
          int(order['expiredAt']),
          Web3.to_checksum_address(order['paymentToken']),
          int(order['startedAt']),
          int(order['basePrice']),
          int(order['endedAt']),
          int(order['endedPrice']),
          0,
          int(order['nonce']),
          int(order['marketFeePercentage'])
      ],
      order['signature'],
      int(order['currentPrice']),
      Web3.to_checksum_address(invitor_address),
      0
  ])
  transaction = mp_contract.functions.interactWith(
      'ORDER_EXCHANGE', data
  ).build_transaction({
      'chainId': 2020,
      'gas': 481337,
      'gasPrice': Web3.to_wei(int(gas_price), 'gwei'),
      'nonce': w3.eth.get_transaction_count(signer.address),
  })
  signed_txn = signer.sign_transaction(transaction)
  tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
  return w3.eth.wait_for_transaction_receipt(tx_hash)


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
    if key in ['auctionTypes', 'sort']:
      continue
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
  with open('_buy_axie_env', 'r') as file:
    config = json.load(file)

  limit_price_eth = config.get('limit_price')
  max_buy = int(config.get('max_buy'))
  mp_url = config.get('market_place_url')
  gas_price = int(config.get('gas_price'))
  private_key = config.get('private_key')
  if (not mp_url.startswith("https://app.axieinfinity.com/marketplace/axies/")): 
    sys.exit("无效的链接市场链接，请检查_buy_axie_env文件中的market_place_url参数")

  print(f'市场链接: {mp_url}')
  print(f'限制购买价格: {limit_price_eth}(低于此价格将自动购买)')
  print(f'最大购买数量: {max_buy}(买完以后停止执行)')

  input("\033[0;31;40m请确认上述配置是否有误, 确认无误后按回车键继续:\033[0m")
  
  print(f'开始执行:')
  buy_count = 0
  while True:
    # 延时1s执行
    time.sleep(1)
    
    try: 
      # 查询列表，只取价格最低的一个
      axie_list = fetch_axie(mp_url, 1)
    except Exception as e :
      error_message = str(e.args[0]) if e.args else "未知错误"
      log_info(f"查询失败: {error_message}")
      continue
    results = axie_list['results']
    if (len(results) == 0) :
      log_info("未查到符合条件的axie")
      continue

    floor_axie = results[0]
    floor_id = int(floor_axie['id'])
    floor_price = int(floor_axie['order']['currentPrice'])
    floor_price_eth = Web3.from_wei(floor_price, 'ether')
    floor_price_usd = float(floor_axie['order']['currentPriceUsd'])
    limit_price = Web3.to_wei(limit_price_eth, 'ether')
    log_info(f"总数: {axie_list['total']}, 地板ID: {floor_id}, 地板价: {round(floor_price_eth, 6)}(weth) (${round(floor_price_usd, 3)})")

    if (floor_price <= limit_price):
      # 购买axie
      print(f"  AxieId={floor_id} 符合条件，提交购买请求", end = "...")
      tx_receipt = buy_axie(floor_axie, private_key, gas_price)
      gas_used = Web3.from_wei(tx_receipt.gasUsed, 'ether') * Web3.to_wei(int(gas_price), 'gwei');
      transaction_hash = tx_receipt.transactionHash.hex()
      if tx_receipt.status == 1:
        buy_count += 1
        print(f"请求成功, 消耗gas: {gas_used}, 交易哈希: {transaction_hash}")
        if (buy_count >= max_buy):
          print(f"购买数量达到{max_buy},完成购买任务，终止执行")
      else:
        print(f"请求失败, 消耗gas:{gas_used}, 交易哈希: {transaction_hash}")



### ============方法定义 end =============
try: 
  main()
except KeyboardInterrupt:
    print('')
    print('取消脚本执行')
### ============脚本执行 start =============

