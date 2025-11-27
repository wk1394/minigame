# 学习小站 - Mini Game Platform

一个支持多个教育小游戏的 Web 平台，包含用户管理、游戏系统和词库管理功能。

## 项目结构

```
mini-game/
├── templates/              # HTML 模板文件
│   ├── index.html         # 主页（游戏列表）
│   ├── login.html         # 登录页面
│   ├── user-management.html  # 用户管理页面
│   ├── word-quest.html    # 字字大冒险游戏
│   ├── multiplication-game.html  # 乘法口诀表消消乐
│   └── admin.html         # 词库管理后台
│
├── static/                # 静态资源
│   ├── css/              # CSS 样式文件
│   └── js/               # JavaScript 文件
│
├── app.py                # Flask 主应用（用户管理 + 游戏路由）
├── words.py              # 独立的字字大冒险服务（可选）
├── config.py             # 数据库配置
├── word_list.json        # 词库数据文件
├── requirements.txt      # Python 依赖
└── README.md            # 项目说明文档
```

## 功能模块

### 1. 用户系统
- 用户注册/登录
- 角色管理（管理员/普通用户）
- 会员系统
- 积分系统

### 2. 游戏列表

#### 字字大冒险 (Word Quest)
- 填空游戏，根据提示填入缺失的字符
- 支持中文和英文词汇
- 计时挑战，连对奖励
- 40 个词库上限
- 路由：`/word-quest`

#### 乘法口诀表消消乐
- 乘法口诀匹配游戏
- 点击配对问题和答案
- 计时功能
- 路由：`/multiplication-game`

### 3. 管理后台
- 词库在线编辑（增删改）
- 用户管理
- 路由：`/admin`

## 安装和运行

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置数据库
编辑 `config.py`，设置 MySQL 数据库连接信息：
```python
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'your_password'
MYSQL_DB = 'your_database'
SECRET_KEY = 'your_secret_key'
```

### 3. 初始化数据库
运行 SQL 脚本创建必要的表：
- users 表
- members 表
- scores 表

### 4. 启动应用
```bash
python app.py
```

应用将在 `http://localhost:3002` 启动

## API 接口

### 用户相关
- `POST /api/register` - 用户注册
- `POST /api/login` - 用户登录
- `POST /api/logout` - 用户登出
- `GET /api/check-auth` - 检查登录状态
- `GET /api/users` - 获取用户列表（需登录）
- `POST /api/add-user` - 添加用户（需登录）

### 游戏相关
- `GET /api/games` - 获取游戏列表
- `GET /start` - 开始字字大冒险游戏（获取题目）

### 词库管理
- `GET /api/words` - 获取词库
- `POST /api/words` - 保存词库（增删改）

## 添加新游戏

要添加新游戏，需要：

1. 在 `templates/` 目录创建游戏 HTML 文件
2. 在 `app.py` 中的 `GAMES` 列表添加游戏配置：
```python
GAMES = [
    {'name': '游戏名称', 'route': '/game-route', 'file': 'game-file.html'}
]
```
3. 在 `app.py` 中添加路由处理函数：
```python
@app.route('/game-route')
def game_route():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('game-file.html')
```

## 技术栈

- **后端**: Flask (Python)
- **数据库**: MySQL + PyMySQL
- **前端**: HTML5, CSS3, JavaScript (原生)
- **会话管理**: Flask Session

## 开发说明

- 所有游戏页面都需要登录才能访问
- 使用 `@login_required` 装饰器保护需要认证的路由
- 词库文件 `word_list.json` 最多支持 40 个单词
- 密码使用 MD5 加密存储

## 注意事项

- 确保 MySQL 服务已启动
- 首次运行需要创建数据库表结构
- 建议使用虚拟环境管理 Python 依赖
- 生产环境请修改 `SECRET_KEY` 和数据库密码
