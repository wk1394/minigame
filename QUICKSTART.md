# 快速启动指南

## 启动步骤

### 1. 检查环境
```bash
# 确保已安装 Python 3.7+
python --version

# 确保 MySQL 服务已启动
```

### 2. 安装依赖
```bash
cd d:\workspace\mini-game
pip install -r requirements.txt
```

### 3. 配置数据库
编辑 `config.py` 文件：
```python
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = '你的密码'
MYSQL_DB = '你的数据库名'
SECRET_KEY = '随机密钥'
```

### 4. 启动应用
```bash
python app.py
```

### 5. 访问应用
打开浏览器访问：`http://localhost:3002`

## 功能访问

| 功能 | 地址 |
|------|------|
| 登录页面 | http://localhost:3002/login |
| 主页（游戏列表） | http://localhost:3002/ |
| 字字大冒险 | http://localhost:3002/word-quest |
| 乘法口诀表消消乐 | http://localhost:3002/multiplication-game |
| 词库管理 | http://localhost:3002/admin |
| 用户管理 | http://localhost:3002/user-management |

## 默认账号

首次使用需要注册账号，在登录页面点击注册。

## 目录说明

```
mini-game/
├── templates/         → 所有 HTML 页面
├── static/           → CSS、JS 等静态资源
├── app.py           → 主程序（启动这个）
├── word_list.json   → 词库文件
└── config.py        → 配置文件（需要编辑）
```

## 管理功能

### 词库管理
1. 登录后访问 `/admin`
2. 可以添加、编辑、删除单词
3. 最多支持 40 个单词
4. 修改后自动保存到 `word_list.json`

### 用户管理
1. 需要管理员权限
2. 访问 `/user-management`
3. 可以查看、添加用户
4. 管理会员状态

## 故障排查

### 1. 无法连接数据库
- 检查 MySQL 是否运行
- 检查 `config.py` 配置是否正确
- 确认数据库和表已创建

### 2. 页面显示 404
- 确认 `templates/` 目录下有对应的 HTML 文件
- 检查文件名是否正确

### 3. 词库加载失败
- 检查 `word_list.json` 文件是否存在
- 检查 JSON 格式是否正确
- 确认文件编码为 UTF-8

### 4. 登录后跳转失败
- 检查 Session 配置
- 清除浏览器 Cookie
- 确认 `SECRET_KEY` 已设置

## 开发建议

- 开发时使用 `debug=True`（已默认开启）
- 生产环境记得改为 `debug=False`
- 定期备份 `word_list.json` 和数据库
- 建议使用虚拟环境

## 端口修改

如果 3002 端口被占用，修改 `app.py` 最后一行：
```python
app.run(host='0.0.0.0', port=你的端口, debug=True)
```
