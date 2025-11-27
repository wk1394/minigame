"""
用户管理模块
负责用户管理、积分、会员等功能
"""
from flask import Blueprint, jsonify, request, session
import pymysql
import hashlib
from functools import wraps
import config

user_bp = Blueprint('user', __name__)

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

# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'message': '未登录'}), 401
        return f(*args, **kwargs)
    return decorated_function

@user_bp.route('/api/users')
@login_required
def get_users():
    """获取用户列表"""
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

@user_bp.route('/api/add-user', methods=['POST'])
@login_required
def add_user():
    """添加用户"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    membership_type = data.get('membership_type', 'free')
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

@user_bp.route('/api/user/score')
@login_required
def get_user_score():
    """获取用户积分"""
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

@user_bp.route('/api/user/membership')
@login_required
def get_user_membership():
    """获取用户会员信息"""
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
