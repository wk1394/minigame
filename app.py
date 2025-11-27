"""
主应用入口
负责登录注册、游戏路由注册
"""
from flask import Flask, render_template, jsonify, request, session, redirect
import pymysql
import hashlib
from functools import wraps
import config

# 导入各模块的蓝图
from user import user_bp
from words import words_bp
from multiplication import multiplication_bp

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = config.SECRET_KEY

# 注册蓝图
app.register_blueprint(user_bp)
app.register_blueprint(words_bp)
app.register_blueprint(multiplication_bp)

# 游戏列表配置
GAMES = [
    {'name': '字字大冒险', 'route': '/word-quest', 'file': 'word-quest.html'},
    {'name': '乘法口诀表消消乐', 'route': '/multiplication-game', 'file': 'multiplication-game.html'},
    {'name': '仙境大冒险 — 生字听写小游戏', 'route': '/listen-write', 'file': 'listen_write.html'},
    {'name': '英语单词分类游戏', 'route': '/classification', 'file': 'classification.html'},
    {'name': '恐龙智益答题游戏', 'route': '/pvz', 'file': 'pvz.html'},
]

# ============== 工具函数 ==============

def hash_password(password):
    """密码加密"""
    return hashlib.md5(password.encode()).hexdigest()

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor
    )

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'message': '未登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

# ============== 页面路由 ==============

@app.route('/')
@app.route('/index')
def index():
    """主页"""
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('index.html', games=GAMES)

@app.route('/login')
def login_page():
    """登录页面"""
    return render_template('login.html')

@app.route('/user-management')
def user_management():
    """用户管理页面"""
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('user-management.html')

@app.route('/word-quest')
def word_quest():
    """字字大冒险游戏页面"""
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('word-quest.html')

@app.route('/multiplication-game')
def multiplication_game():
    """乘法口诀表消消乐页面"""
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('multiplication-game.html')

@app.route('/listen-write')
def listen_write():
    """仙境大冒险 — 生字听写小游戏页面"""
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('listen_write.html')

@app.route('/classification')
def classification():
    """英语单词分类游戏页面"""
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('classification.html')

@app.route('/pvz')
def pvz():
    """恐龙智益答题游戏页面"""
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('pvz.html')

# ============== 认证 API ==============

@app.route('/api/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')

    if not username or not password:
        return jsonify({'message': '用户名和密码不能为空'}), 400

    if role not in ['admin', 'user']:
        return jsonify({'message': '角色类型错误'}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 检查用户是否存在
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            cur.close()
            return jsonify({'message': '用户名已存在'}), 400

        # 创建用户
        hashed_password = hash_password(password)
        cur.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                   (username, hashed_password, role))
        user_id = cur.lastrowid

        # 创建会员记录
        cur.execute("INSERT INTO members (user_id, membership_type) VALUES (%s, 'free')", (user_id,))

        conn.commit()
        cur.close()

        # 自动登录
        session['user_id'] = user_id
        session['username'] = username
        session['role'] = role

        return jsonify({'message': '注册成功', 'user_id': user_id, 'role': role}), 200
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"注册错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'注册失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': '用户名和密码不能为空'}), 400

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, password, role FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and user['password'] == hash_password(password):
            session['user_id'] = user['id']
            session['username'] = username
            session['role'] = user['role']

            # 根据角色返回不同的跳转路径
            redirect_url = '/user-management' if user['role'] == 'admin' else '/'

            return jsonify({
                'message': '登录成功',
                'role': user['role'],
                'redirect': redirect_url
            }), 200
        else:
            return jsonify({'message': '用户名或密码错误'}), 401
    except Exception as e:
        return jsonify({'message': f'登录失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/logout', methods=['POST'])
def logout():
    """用户登出"""
    session.clear()
    return jsonify({'message': '退出成功'}), 200

@app.route('/api/check-auth')
@login_required
def check_auth():
    """检查登录状态"""
    return jsonify({
        'user_id': session['user_id'],
        'username': session['username'],
        'role': session.get('role', 'user')
    }), 200

# ============== 游戏 API ==============

@app.route('/api/games')
@login_required
def get_games():
    """获取游戏列表"""
    return jsonify([{'name': g['name'], 'url': g['route']} for g in GAMES])

# ============== 应用启动 ==============

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3002, debug=True)
