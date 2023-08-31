## 适用场景

持有多于1个axie账号的人，不愿意每天切换账号手动进行祈福，可通过设置定时任务每天定时运行此脚本，自动对多个账号进行祈福


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

复制batch_blessing_env.example文件并命名为_batch_blessing_env,将文件中的PRIVATE_KEY改为你的真实私钥

注意: 文件中包含私钥信息，请不要向任何人泄露，通过复制文件的方式分享代码时也一定要将_batch_blessing_env文件删除

### 单次使用

```
# 在脚本所在根目录下执行

python3 batch_blessing.py
```

### 定时任务


- Mac电脑下使用crontab配置定时任务

```
# 注意将 {script_path} 和 {python_path} 替换成真实路径
# 每天中行12:18自动执行脚本,并将执行日志写入run.log文件中

18 12 * * * cd {script_path} && {python_path}/python3 batch_blessing.py >> run.log 2>&1

```

- windows电脑请参考下面链接内的方法

```
https://blog.csdn.net/B11050729/article/details/131250072
```

