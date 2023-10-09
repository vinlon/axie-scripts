import requests
import json
import os
import curses
import time
from web3 import Web3

def list_charms(charm_ids):
  # 从文件中读取query内容
  with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'get_min_price.graphql'), 'r') as file:
    query = file.read()

  data = {
    'query': query,
    'variables': {
        'tokenIds': charm_ids
    },
    'operationName': 'GetMinPriceErc1155Tokens'
  }
  endpoint = 'https://graphql-gateway.axieinfinity.com/graphql'
  response =  requests.post(endpoint, json = data)
  return response.json()['data']['erc1155Tokens']['results']

def buy_charm(order, private_key, gas_price):
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
  settleOrderParams = [
      [
          Web3.to_checksum_address(order['maker']),
          int(order['kind'] == 'Sell'),
          [[
              2,
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
  ]
  data = mp_contract.encodeABI(fn_name='settleOrder', args=settleOrderParams)
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

def print_header(stdscr, start_time):
  stdscr.addstr(0, 0, "开始查询CHARMS信息(按'q'键退出)", curses.A_BOLD)
  stdscr.addstr(1, 0, "开始时间:" + start_time)
  
def print_content(stdscr, data):
  stdscr.addstr(2, 0, "当前时间:" + time.strftime("%Y-%m-%d %H:%M:%S"))
  stdscr.addstr(3, 0, f"查询次数:{data.get('query_count', 0)}")
  stdscr.addstr(4, 0, '正在查询' + ('=' * (data.get('loop') % 50)) + '>')
  stdscr.addstr(5, 0, "{:<20} {:<10} {:<15} {:<15} {:<10} {:<10}".format("REMARK", "CHARM_ID", "Limit Price", "Min Price", "Max Buy", "Buy Count"))
  row = 6
  for id, target in data.get('targets', []).items():
    # 格式化每一行的数据
    target_info = "{:<20} {:<10} {:<15} {:<15} {:<10} {:<10}".format(
        target.get('remark', '-'),
        id,
        target.get('limit_price_eth', '-'),
        f"{target.get('min_price_eth', 0):.6f}",
        target.get('max_buy', '0'),
        target.get('buy_count', '0')
    )
    stdscr.addstr(row, 0, target_info)
    row += 1
  stdscr.addstr(row, 0, "购买记录：")
  row += 1
  for log in data.get('buy_log', []):
    stdscr.addstr(row, 0, log)
    row += 1

def main(stdscr):
  # 读取配置
  with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_buy_charm_env'), 'r') as file:
    config = json.load(file)
  gas_price = int(config.get('gas_price'))
  private_key = config.get('private_key')
  # 提取所有的 id 作为数组
  target_ids = [target['id'] for target in config['targets']]
  # 创建一个以 id 为键的字典，以便按 id 进行索引
  targets_by_id = {target['id']: target for target in config['targets']}
  order_ids = []
  start_time = time.strftime("%Y-%m-%d %H:%M:%S")
  query_count = 0
  loop = 0
  buy_log = []

  curses.curs_set(0)  # 隐藏光标
  stdscr.nodelay(1)  # 设置为非阻塞输入
  stdscr.scrollok(True) # 开启窗口滚动
  print_header(stdscr, start_time)
  while True:
    query_count = query_count + 1
    loop = loop + 1
    try: 
      # 查询charms列表，包含最低价格
      charms = list_charms(target_ids)
    except Exception as e :
      continue
    
    for charm in charms:
      charm_id = charm['id']
      min_price = int(charm['minPrice'])
      min_price_eth = Web3.from_wei(min_price, 'ether')
      target = targets_by_id[charm_id]
      limit_price_eth = target['limit_price_eth']
      limit_price = Web3.to_wei(limit_price_eth, 'ether')
      target['min_price_eth'] = min_price_eth
      if (min_price > limit_price):
        continue
      order = charm['orders']['data'][0]
      order_id = order.get('id', 0)
      # 以防万一，再检查一下order的currentPrice
      order_min_price = int(order['currentPrice'])
      if (order_min_price > limit_price):
        continue
      # charm被买走后，短时间内仍然会被查到
      if order_id in order_ids:
        continue;
      order_ids.append(order_id)
      max_buy = target.get('max_buy', 0)
      buy_count = target.get('buy_count', 0)
      
      log = f"[charm_id={charm_id},order_id={order_id}]最低价为{min_price_eth}，低于{limit_price_eth}"
      if (buy_count >= max_buy):
        continue
      log = f"{log},符合购买条件，发送订单"
      buy_log.append(log)
      try: 
        tx_receipt = buy_charm(order, private_key, gas_price)
        gas_used = Web3.from_wei(tx_receipt.gasUsed, 'ether') * Web3.to_wei(int(gas_price), 'gwei');
        transaction_hash = tx_receipt.transactionHash.hex()
        if tx_receipt.status == 1:
          target['buy_count'] = buy_count + 1
          buy_log.append(f"请求成功, 消耗gas: {gas_used}, 交易哈希: {transaction_hash}")
        else:
          buy_log.append(f"请求失败, 消耗gas:{gas_used}, 交易哈希: {transaction_hash}")
      except Exception as e :
        error_message = str(e.args[0]) if e.args else "未知错误"
        buy_log.append(f"购买失败: {error_message}")
    # 输出动态内容
    stdscr.clear()
    print_header(stdscr, start_time)
    print_content(stdscr, {
      'query_count': query_count, 
      'targets':targets_by_id,
      'buy_log': buy_log,
      'loop': loop
    })
    stdscr.refresh()
    # 获取用户输入（非阻塞）
    key = stdscr.getch()
    # 处理输入
    if key == ord('q'):
        break
### ============方法定义 end =============
try: 
  if __name__ == "__main__":
    curses.wrapper(main)
except KeyboardInterrupt:
    print('取消脚本执行')
### ============脚本执行 start =============