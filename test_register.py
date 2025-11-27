import requests
import json

# 测试注册接口
def test_register():
    url = 'http://localhost:3002/api/register'

    # 测试数据
    test_users = [
        {'username': 'testuser1', 'password': 'password123'},
        {'username': 'testuser2', 'password': 'password456'},
    ]

    for user in test_users:
        print(f"\n测试注册用户: {user['username']}")
        try:
            response = requests.post(url, json=user, timeout=5)
            print(f"状态码: {response.status_code}")
            print(f"响应: {response.json()}")
        except Exception as e:
            print(f"错误: {str(e)}")

# 测试数据库连接
def test_db_connection():
    import pymysql
    import sys
    sys.path.append('.')
    import config

    print("测试数据库连接...")
    try:
        conn = pymysql.connect(
            host=config.MYSQL_HOST,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DB
        )
        print("✓ 数据库连接成功")

        cur = conn.cursor()
        cur.execute("SHOW TABLES")
        tables = cur.fetchall()
        print(f"✓ 数据库中的表: {tables}")

        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        print(f"✓ 当前用户数: {count}")

        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ 数据库连接失败: {str(e)}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("开始测试注册接口")
    print("=" * 50)

    # 先测试数据库连接
    if test_db_connection():
        print("\n" + "=" * 50)
        # 再测试注册接口
        test_register()

    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)
