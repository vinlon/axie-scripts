import blessing
import json

# 从.blessing_keys文件中读取想要祈福的账号
with open('.blessing_keys', 'r') as file:
  # 使用 json.load() 方法加载数据
  keys = json.load(file)

for key in keys:
  blessing.start(key)
      