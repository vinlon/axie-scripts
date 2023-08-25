## AXP自动升级

查询账号下可以升级的axie,自动升级（未充分测试，慎用)

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

## 使用说明 

复制batch_ascend_env.example文件并命名为_batch_ascend_env,将文件中的PRIVATE_KEY改为你的真实私钥

注意: 文件中包含私钥信息，请不要向任何人泄露，通过复制文件的方式分享代码时也一定要将_batch_ascend_env文件删除

### 单次使用

```
# 在脚本所在根目录下执行

python3 batch_ascend.py
```