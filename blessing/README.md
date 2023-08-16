## 适用场景

持有多于1个axie账号的人，不愿意每天切换账号手动进行祈福，可通过设置定时任务每天定时运行此脚本，自动对多个账号进行祈福


## 运行环境准备

- python3  
- pip  
- 安装依赖  

```
pip install requests
pip install web3
pip install json
```

## 使用说明 

### 单次使用

### 定时任务

```
# 注意将 {script_path} 和 {python_path} 替换成真实路径
# 每天中行12:18自动执行脚本,并将执行日志写入run.log文件中

18 12 * * * cd {script_path}/blessing/ && {python_path}/python3 batch_blessing.py >> run.log 2>&1

```


## 注意事项

1. 请注意不要向任何人泄露你的密钥，也不要将包含 .batch_blessing_env 的文件的脚本分享给任何人或存放到任何非本人的电脑上

