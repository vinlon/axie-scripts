import requests
import json
import os
import sys
import time
import logging
import curses
from web3 import Web3

# 日志配置
logging.basicConfig(filename='query.log', level=logging.INFO, format='%(asctime)s - %(message)s')

### ============方法定义 start ============
# 根据市场链接查询axie列表
def fetch_axie(mp_url, size):
  # 从文件中读取query内容
  with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'get_brief_list.graphql'), 'r') as file:
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
  provider = Web3.HTTPProvider(ronin_rpc)
  w3 = Web3(provider)
  with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'marketplace_abi.json'), 'r') as file:
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
  query_string = url.split('?')[1] if '?' in url else ''

  # 将查询字符串拆分为键值对
  query_params_list = query_string.split('&')
  query_params = {}
  for param in query_params_list:
    if '=' not in param:
      continue
    key, value = param.split('=')
    if value.isdigit():
      value = int(value)
    if key == 'excludeParts':
      key = 'parts'
      value = '!' + value
    if key in ['auctionTypes', 'sort']:
      continue
    elif key in query_params:
      query_params[key].append(value)
    else:
      query_params[key] = [value]

  return query_params

def print_content(stdscr, data):
  stdscr.clear()
  stdscr.addstr(0, 0, f"市场链接: {data.get('mp_url')}")
  stdscr.addstr(1, 0, f"限制购买价格: {data.get('limit_price_eth')}(低于此价格将自动购买)")
  stdscr.addstr(2, 0, f"最大购买数量: {data.get('max_buy')}(买完以后停止执行)")
  stdscr.addstr(3, 0, f"查询次数: {data.get('loop')}, 已购数量: {data.get('buy_count')}")
  stdscr.addstr(4, 0, f"查询记录(只显示最新的10条，历史查询记录可以在query.log中查看):")
  stdscr.addstr(5, 0, "{:<20} {:<10} {:<10} {:<15} {:<10}".format("QUERY_TIME", "FLOOR_ID", "TOTAL", "PRICE_ETH", "PRICE_USD"))
  row = 6
  for query_log in reversed(data.get('query_logs', [])):
    # 格式化每一行的数据
    query_info = "{:<20} {:<10} {:<10} {:<15} {:<10}".format(
        query_log.get('query_time', '-'),
        query_log.get('floor_id', '-'),
        query_log.get('total', '-'),
        f"{query_log.get('floor_price_eth', '0'):.6f}",
        f"${query_log.get('floor_price_usd', '0'):.6f}"
    )
    stdscr.addstr(row, 0, query_info)
    row += 1
  stdscr.addstr(row, 0, f"购买记录:")
  row += 1
  stdscr.addstr(row, 0, "{:<20} {:<10} {:<10} {:<15} {:<15}".format("BUY_TIME", "AXIE_ID", "PRICE", "GAS_USED", "RESULT"))
  row += 1
  for buy_log in data.get('buy_logs'):
    buy_info = "{:<20} {:<10} {:<10} {:<15} {:<15}".format(
        buy_log.get('buy_time', '-'),
        buy_log.get('axie_id', '-'),
        f"{buy_log.get('price', 0):.6f}",
        f"${buy_log.get('gas_used', 0):.10f}",
        buy_log.get('result', '-')
    )
    stdscr.addstr(row, 0, buy_info)
    row += 1
  stdscr.refresh()

def main(stdscr): 
  # 读取配置
  with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_buy_axie_env'), 'r') as file:
    config = json.load(file)

  limit_price_eth = config.get('limit_price')
  max_buy = int(config.get('max_buy'))
  mp_url = config.get('market_place_url')
  gas_price = int(config.get('gas_price'))
  private_key = config.get('private_key')
  if (not mp_url.startswith("https://app.axieinfinity.com/marketplace/axies/")): 
    sys.exit("无效的链接市场链接，请检查_buy_axie_env文件中的market_place_url参数")

  
  stdscr.nodelay(1)   # 设置为非阻塞输入
  stdscr.addstr(0, 0, f'市场链接: {mp_url}')
  stdscr.addstr(1, 0, f'限制购买价格: {limit_price_eth}(低于此价格将自动购买)')
  stdscr.addstr(2, 0, f'最大购买数量: {max_buy}(买完以后停止执行)')
  stdscr.addstr(3, 0, "请确认上述配置是否有误, 确认无误后按回车键继续:")
  stdscr.refresh()
  # 等待用户按下任意键
  while True:
      key = stdscr.getch()
      if key != -1:
          break
  curses.curs_set(0)  # 隐藏光标 

  buy_count = 0
  data = {
    'mp_url': mp_url,
    'limit_price_eth': limit_price_eth,
    'max_buy': max_buy,
    'query_logs': [],
    'buy_logs': [],
    'buy_count': buy_count,
    'loop': 0
  }
  while True:
    # 延时1s执行
    time.sleep(1)
    data['loop'] += 1
    try: 
      # 查询列表，只取价格最低的一个
      axie_list = fetch_axie(mp_url, 1)
    except Exception as e :
      error_message = str(e.args[0]) if e.args else "未知错误"
      continue
    results = axie_list['results']
    if (len(results) == 0) :
      continue

    floor_axie = results[0]
    floor_id = int(floor_axie['id'])
    floor_price = int(floor_axie['order']['currentPrice'])
    floor_price_eth = Web3.from_wei(floor_price, 'ether')
    floor_price_usd = float(floor_axie['order']['currentPriceUsd'])
    limit_price = Web3.to_wei(limit_price_eth, 'ether')
    total = axie_list['total']
    is_match = floor_price <= limit_price
    msg = f"总数: {total}, 地板ID: {floor_id}, 地板价: {round(floor_price_eth, 6)}(weth) (${round(floor_price_usd, 3)})"
    logging.info(msg)
    data['query_logs'] = data['query_logs'][-9:]
    data['query_logs'].append({
      'query_time': time.strftime("%Y-%m-%d %H:%M:%S"),
      'floor_id': floor_id,
      'floor_price_eth': floor_price_eth,
      'floor_price_usd': floor_price_usd,
      'total': total
    })
    print_content(stdscr, data)
      
    if is_match:
      if (buy_count < max_buy):
        # 购买axie
        tx_receipt = buy_axie(floor_axie, private_key, gas_price)
        gas_used = Web3.from_wei(tx_receipt.gasUsed, 'ether') * Web3.to_wei(int(gas_price), 'gwei');
        transaction_hash = tx_receipt.transactionHash.hex()
        result = '购买失败' if tx_receipt.status == 0 else '购买成功'
        if tx_receipt.status == 1:
          buy_count += 1
      else:
        gas_used = 0
        transaction_hash = '-'
        result = f"购买进度{buy_count}/{max_buy},跳过"
      
      data['buy_logs'] = data['buy_logs'][-9:]
      data['buy_logs'].append({
        'buy_time': time.strftime("%Y-%m-%d %H:%M:%S"),
        'axie_id': floor_id,
        'price': floor_price_eth,
        'result': result,
        'gas_used': gas_used,
        'trans_hash': transaction_hash
      })
      print_content(stdscr, data)

### ============方法定义 end =============
try: 
  if __name__ == "__main__":
    curses.wrapper(main)
except KeyboardInterrupt:
    print('取消脚本执行')
### ============脚本执行 start =============

