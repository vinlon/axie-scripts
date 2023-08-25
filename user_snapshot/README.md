## 适用场景(未完成)

一次性查看多个账号的胜率，阵容，装备，资产等信息，只需要提供ronin address列表，执行命令后生成html页面，打开页面后即可查看账户信息

## TODO

1. 脚本执行流程优化

2. 数据查看页面增加筛选搜索功能，页面样式优化


## 文件说明

```
# data
- data_charms.json: charm_id和图片的对应关系
- data_charms_per_rarity.json: 当前赛季的各个阶段的charm_id列表，用于查询用户持有的charm
- data_runes.json: rune_id和图片的对应关系
- data_runes_per_rarity.json: 当前赛季的各个阶段的rune_id列表，用于查询用户持有的rune
- data_user_map.json: 用户ID和用户名的对应关系，通过ronin地址查询获得

# html
- index.html: 程序最终生成的页面代码
- index_template.html: 页面模板文件，将数据写入后即可生成index.html

# python
- load_rune_and_charms.py: 加载rune和charm数据，理论上每个赛初只需要执行一次，且需要修改代码中season参数的值
- load_user_info.py: 根据user_snapshot_env中定义的address查询用户ID和名称写入data_user_map.json,每次新增账号都需要重新执行此脚本
- user_snapshot.py: 查询用户数据
- user_snapshot_env: 需要查询的用户address
```