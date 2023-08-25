## 适用场景

监控市场查询链接，如果出现符合条件的低价宠物则自动购买

## 注意事项

1. 一定要单独申请一个新的账号，只充够用的ron和weth进去，一方面防止开发者居心不良设置后门盗走你的私钥，另一方面也防止代码中有逻辑bug导致你损失太多资金.



## 运行环境准备
- python3
- pip
- 安装依赖

```
pip install requests
# 注意要安装6.x版本的web3库
pip install web3
pip install json
```


### 配置文件使用说明

复制buy_axie_env.example文件并重命名为_buy_axie_env, 并按照自己的实际情况修改其中的配置

注意: 配置文件中包含私钥信息，请不要向任何人泄露，通过复制文件的方式分享代码时也一定要将_buy_axie_env文件删除


```
market_place_url: 特定筛选条件的市场链接
limit_price: 价格低于此限制就购买(单位: weth)
secret_key: 用于购买axie的账号，账号下需要有足够数量的ron和weth" 
max_buy: 购买数量,超过此购买数量后即停止执行
gas_price: gas价格，同时提交请求情况下，gas越高越容易成交，默认20(单位GWEI)

```

### 运行脚本

```
# 在脚本所在根目录下执行

python3 buy_axie.py
```