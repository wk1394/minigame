from flask import Flask, send_file, jsonify

app = Flask(__name__)

# 游戏列表配置
GAMES = [
    {'name': '消消乐', 'route': '/multiplication-game', 'file': 'multiplication-game.html'}
]

@app.route('/')
@app.route('/index')
def index():
    return send_file('index.html')

@app.route('/api/games')
def get_games():
    return jsonify([{'name': g['name'], 'url': g['route']} for g in GAMES])

# 动态游戏路由
@app.route('/multiplication-game')
def multiplication_game():
    return send_file('multiplication-game.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3002)
