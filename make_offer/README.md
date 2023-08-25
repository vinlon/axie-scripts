## 适用场景

监控市场查询链接，给符合条件的宠物发送OFFER (慎用，因为一旦别人同意OFFER就会自动扣费，而这里只有批量发OFFER的脚本，没有批量取消OFFER的脚本)

## 注意事项

1. 一定要单独申请一个新的账号，只充够用的ron和weth进去，一方面防止开发者居心不良设置后门盗走你的私钥，另一方面也防止代码中有逻辑bug导致你损失太多资金.

2. 发送offer不需要gas费，但取消offer需要


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

复制batch_offer_env.example文件并重命名为_batch_offer_env, 并按照自己的实际情况修改其中的配置

注意: 配置文件中包含私钥信息，请不要向任何人泄露，通过复制文件的方式分享代码时也一定要将_batch_offer_env文件删除


```
private_key: 用于发送offer的账号，账号下需要有足够数量的ron和weth
market_place_url: 特定筛选条件的市场链接, 支持选中【Not For Sale】筛选条件
offer_price: offer价格
offer_count: 发送offer数量
```

### 运行脚本

```
# 在脚本所在根目录下执行

python3 batch_offer.py
```