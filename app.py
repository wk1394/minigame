from flask import Flask, render_template, jsonify, request, session, redirect
import pymysql
import hashlib
from functools import wraps
import config
import json
import os
import random

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = config.SECRET_KEY

WORD_LIST_FILE = 'word_list.json'

# 密码加密函数
def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

# 数据库连接函数
def get_db_connection():
    return pymysql.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor
    )

# 游戏列表配置
GAMES = [
    {'name': '字字大冒险', 'route': '/word-quest', 'file': 'word-quest.html'},
    {'name': '乘法口诀表消消乐', 'route': '/multiplication-game', 'file': 'multiplication-game.html'}
]

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'message': '未登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

# 页面路由
@app.route('/')
@app.route('/index')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('index.html', games=GAMES)

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/user-management')
def user_management():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('user-management.html')

@app.route('/word-quest')
def word_quest():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('word-quest.html')

@app.route('/multiplication-game')
def multiplication_game():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('multiplication-game.html')

# API路由
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'user')  # 默认为普通用户

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
    session.clear()
    return jsonify({'message': '退出成功'}), 200

@app.route('/api/check-auth')
@login_required
def check_auth():
    return jsonify({
        'user_id': session['user_id'],
        'username': session['username'],
        'role': session.get('role', 'user')
    }), 200

@app.route('/api/games')
@login_required
def get_games():
    return jsonify([{'name': g['name'], 'url': g['route']} for g in GAMES])

@app.route('/api/users')
@login_required
def get_users():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                u.id,
                u.username,
                u.role,
                COALESCE(m.membership_type, 'free') as membership_type,
                COALESCE(SUM(s.score), 0) as total_score,
                DATE_FORMAT(m.start_date, '%Y-%m-%d %H:%i') as start_date
            FROM users u
            LEFT JOIN members m ON u.id = m.user_id
            LEFT JOIN scores s ON u.id = s.user_id
            GROUP BY u.id, u.username, u.role, m.membership_type, m.start_date
            ORDER BY u.id
        """)
        users = cur.fetchall()
        cur.close()

        return jsonify(users), 200
    except Exception as e:
        return jsonify({'message': f'获取用户列表失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/add-user', methods=['POST'])
@login_required
def add_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    membership_type = data.get('membership_type', 'free')
    role = data.get('role', 'user')  # 添加角色字段

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
            return jsonify({'message': '用户名已存在'}), 400

        # 创建用户
        hashed_password = hash_password(password)
        cur.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                   (username, hashed_password, role))
        user_id = cur.lastrowid

        # 创建会员记录
        cur.execute("INSERT INTO members (user_id, membership_type) VALUES (%s, %s)", (user_id, membership_type))

        conn.commit()
        cur.close()

        return jsonify({'message': '用户添加成功'}), 200
    except Exception as e:
        return jsonify({'message': f'添加失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/user/score')
@login_required
def get_user_score():
    conn = None
    try:
        user_id = session['user_id']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(SUM(score), 0) as total FROM scores WHERE user_id = %s", (user_id,))
        result = cur.fetchone()
        cur.close()
        return jsonify({'total_score': result['total']}), 200
    except Exception as e:
        return jsonify({'message': f'获取积分失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/user/membership')
@login_required
def get_user_membership():
    conn = None
    try:
        user_id = session['user_id']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT membership_type, start_date, end_date FROM members WHERE user_id = %s", (user_id,))
        member = cur.fetchone()
        cur.close()

        if member:
            return jsonify({
                'membership_type': member['membership_type'],
                'start_date': str(member['start_date']) if member['start_date'] else None,
                'end_date': str(member['end_date']) if member['end_date'] else None
            }), 200
        else:
            return jsonify({'membership_type': 'free'}), 200
    except Exception as e:
        return jsonify({'message': f'获取会员信息失败: {str(e)}'}), 500
    finally:
        if conn:
            conn.close()

# 词库管理 API
@app.route('/api/words', methods=['GET'])
def get_words():
    """获取词库"""
    try:
        if os.path.exists(WORD_LIST_FILE):
            with open(WORD_LIST_FILE, 'r', encoding='utf-8') as f:
                words = json.load(f)
            return jsonify(words), 200
        else:
            return jsonify([]), 200
    except Exception as e:
        return jsonify({'message': f'读取词库失败: {str(e)}'}), 500

@app.route('/api/words', methods=['POST'])
def save_words():
    """保存词库（增删改）"""
    try:
        words = request.json
        
        if not isinstance(words, list):
            return jsonify({'message': '数据格式错误'}), 400
        
        # 验证词库数量限制
        if len(words) > 40:
            return jsonify({'message': '词库最多只能有40个单词'}), 400
        
        # 验证每个单词的格式
        for word in words:
            if not isinstance(word, dict):
                return jsonify({'message': '单词格式错误'}), 400
            if 'word' not in word or 'missing' not in word or 'type' not in word:
                return jsonify({'message': '单词必须包含 word、missing 和 type 字段'}), 400
            if word['type'] not in ['en', 'cn']:
                return jsonify({'message': 'type 必须是 en 或 cn'}), 400
            if word['missing'] not in word['word']:
                return jsonify({'message': f'缺失字符"{word["missing"]}"必须在单词"{word["word"]}"中'}), 400
        
        # 保存到文件
        with open(WORD_LIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(words, f, ensure_ascii=False, indent=2)
        
        return jsonify({'message': '保存成功'}), 200
    except Exception as e:
        return jsonify({'message': f'保存失败: {str(e)}'}), 500

@app.route('/admin')
def admin_page():
    """词库管理页面"""
    return render_template('admin.html')

# 字字大冒险游戏 API
def load_word_list():
    """加载词库"""
    try:
        with open(WORD_LIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def make_display(word, missing):
    """生成带下划线的显示文本"""
    idx = word.find(missing)
    if idx == -1:
        return word[0] + '_' + word[1:]
    return word[:idx] + '_' + word[idx+len(missing):]

@app.route('/start')
def start_word_quest():
    """开始字字大冒险游戏"""
    words = load_word_list()
    total = min(40, len(words))
    if total == 0:
        return jsonify({'rounds': []}), 200
    
    samples = random.sample(words, total)
    rounds = []
    
    for i in range(0, total, 4):
        group = samples[i:i+4]
        items = []
        for it in group:
            display = make_display(it['word'], it.get('missing', ''))
            items.append({
                'word': it['word'],
                'missing': it.get('missing', ''),
                'type': it.get('type', 'en'),
                'display': display
            })
        answers = [it['missing'] for it in group]
        random.shuffle(answers)
        rounds.append({'items': items, 'answers': answers})
    
    return jsonify({'rounds': rounds}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3002, debug=True)
