## 运行环境准备
- python3
- pip
- 安装依赖
```
pip install requests
pip install web3
pip install json
```

### 参数说明 

market_place_url: 特定筛选条件的市场链接,或者某个特定axie页面
limit_price: 价格低于此限制就购买(单位: weth),
max_buy: 购买数量,超过此购买数量后即停止执行,
gas_price: gas价格，同时提交请求情况下，gas越高越容易成交，默认20(单位GWEI)
receive_address: 出于安全考虑，购买成功后自动将axie转到此账户下,账户下不需要有任何代币
secret_key: 用于购买axie的账号，账号下需要有足够数量的ron和weth" 