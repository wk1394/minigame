from flask import Flask, send_file, jsonify, request, session, redirect
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# MySQL配置
app.config['MYSQL_HOST'] = config.MYSQL_HOST
app.config['MYSQL_USER'] = config.MYSQL_USER
app.config['MYSQL_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DB'] = config.MYSQL_DB

mysql = MySQL(app)

# 游戏列表配置
GAMES = [
    {'name': '消消乐', 'route': '/multiplication-game', 'file': 'multiplication-game.html'}
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
    return send_file('index.html')

@app.route('/login')
def login_page():
    return send_file('login.html')

@app.route('/user-management')
def user_management():
    if 'user_id' not in session:
        return redirect('/login')
    return send_file('user-management.html')

@app.route('/multiplication-game')
def multiplication_game():
    if 'user_id' not in session:
        return redirect('/login')
    return send_file('multiplication-game.html')

# API路由
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': '用户名和密码不能为空'}), 400

    try:
        cur = mysql.connection.cursor()

        # 检查用户是否存在
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            return jsonify({'message': '用户名已存在'}), 400

        # 创建用户
        hashed_password = generate_password_hash(password)
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        user_id = cur.lastrowid

        # 创建会员记录
        cur.execute("INSERT INTO members (user_id, membership_type) VALUES (%s, 'free')", (user_id,))

        mysql.connection.commit()
        cur.close()

        # 自动登录
        session['user_id'] = user_id
        session['username'] = username

        return jsonify({'message': '注册成功'}), 200
    except Exception as e:
        return jsonify({'message': f'注册失败: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': '用户名和密码不能为空'}), 400

    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, password FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            return jsonify({'message': '登录成功'}), 200
        else:
            return jsonify({'message': '用户名或密码错误'}), 401
    except Exception as e:
        return jsonify({'message': f'登录失败: {str(e)}'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': '退出成功'}), 200

@app.route('/api/check-auth')
@login_required
def check_auth():
    return jsonify({'user_id': session['user_id'], 'username': session['username']}), 200

@app.route('/api/games')
@login_required
def get_games():
    return jsonify([{'name': g['name'], 'url': g['route']} for g in GAMES])

@app.route('/api/users')
@login_required
def get_users():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT
                u.id,
                u.username,
                COALESCE(m.membership_type, 'free') as membership_type,
                COALESCE(SUM(s.score), 0) as total_score,
                DATE_FORMAT(m.start_date, '%%Y-%%m-%%d %%H:%%i') as start_date
            FROM users u
            LEFT JOIN members m ON u.id = m.user_id
            LEFT JOIN scores s ON u.id = s.user_id
            GROUP BY u.id, u.username, m.membership_type, m.start_date
            ORDER BY u.id
        """)
        users = cur.fetchall()
        cur.close()

        result = []
        for user in users:
            result.append({
                'id': user[0],
                'username': user[1],
                'membership_type': user[2],
                'total_score': user[3],
                'start_date': user[4]
            })

        return jsonify(result), 200
    except Exception as e:
        return jsonify({'message': f'获取用户列表失败: {str(e)}'}), 500

@app.route('/api/add-user', methods=['POST'])
@login_required
def add_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    membership_type = data.get('membership_type', 'free')

    if not username or not password:
        return jsonify({'message': '用户名和密码不能为空'}), 400

    try:
        cur = mysql.connection.cursor()

        # 检查用户是否存在
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            return jsonify({'message': '用户名已存在'}), 400

        # 创建用户
        hashed_password = generate_password_hash(password)
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        user_id = cur.lastrowid

        # 创建会员记录
        cur.execute("INSERT INTO members (user_id, membership_type) VALUES (%s, %s)", (user_id, membership_type))

        mysql.connection.commit()
        cur.close()

        return jsonify({'message': '用户添加成功'}), 200
    except Exception as e:
        return jsonify({'message': f'添加失败: {str(e)}'}), 500

@app.route('/api/user/score')
@login_required
def get_user_score():
    try:
        user_id = session['user_id']
        cur = mysql.connection.cursor()
        cur.execute("SELECT COALESCE(SUM(score), 0) FROM scores WHERE user_id = %s", (user_id,))
        total_score = cur.fetchone()[0]
        cur.close()
        return jsonify({'total_score': total_score}), 200
    except Exception as e:
        return jsonify({'message': f'获取积分失败: {str(e)}'}), 500

@app.route('/api/user/membership')
@login_required
def get_user_membership():
    try:
        user_id = session['user_id']
        cur = mysql.connection.cursor()
        cur.execute("SELECT membership_type, start_date, end_date FROM members WHERE user_id = %s", (user_id,))
        member = cur.fetchone()
        cur.close()

        if member:
            return jsonify({
                'membership_type': member[0],
                'start_date': str(member[1]) if member[1] else None,
                'end_date': str(member[2]) if member[2] else None
            }), 200
        else:
            return jsonify({'membership_type': 'free'}), 200
    except Exception as e:
        return jsonify({'message': f'获取会员信息失败: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3002)
