from flask import Flask, jsonify, send_from_directory, request, render_template_string
import json, random, os


app = Flask(__name__, static_folder='static')

WORDLIST_PATH = 'word_list.json'
def load_words():
    try:
        with open(WORDLIST_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


WORDS = load_words()


# 验证与辅助函数
def validate_wordlist(data):
    if not isinstance(data, list):
        return False, '词库必须是列表'
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            return False, f'第 {i+1} 项必须是对象'
    if 'word' not in item or 'missing' not in item:
        return False, f'第 {i+1} 项缺少字段 word 或 missing'
    return True, 'OK'


def make_display(word, missing):
    idx = word.find(missing)
    if idx == -1:
        return word[0] + '_' + word[1:]
    return word[:idx] + '_' + word[idx+len(missing):]

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/start')
def start():
    global WORDS
    total = min(40, len(WORDS))
    samples = random.sample(WORDS, total)
    rounds = []
    for i in range(0, total, 4):
        group = samples[i:i+4]
        items = []
        for it in group:
            display = make_display(it['word'], it.get('missing',''))
            items.append({
            'word': it['word'],
            'missing': it.get('missing',''),
            'type': it.get('type','en'),
            'display': display
            })
        answers = [it['missing'] for it in group]
        random.shuffle(answers)
        rounds.append({'items': items, 'answers': answers})
    return jsonify({'rounds': rounds})


# 管理界面
admin_html = """
<h2>词库管理</h2>
<form method="POST" action="/upload" enctype="multipart/form-data">
<p>上传新的 wordlist.json：</p>
<input type="file" name="file" accept="application/json" required>
<button type="submit">上传</button>
</form>
<hr>
<h3>当前词库内容：</h3>
<pre>{{ words }}</pre>
"""


@app.route('/admin')
def admin():
    global WORDS
    return render_template_string(admin_html, words=json.dumps(WORDS, ensure_ascii=False, indent=2))


# 上传接口
@app.route('/upload', methods=['POST'])
def upload():
    global WORDS
    file = request.files.get('file')
    if not file:
        return '未选择文件', 400
    try:
        data = json.load(file)
    except Exception:
        return 'JSON 格式错误', 400
    ok, msg = validate_wordlist(data)
    if not ok:
        return f'词库验证失败：{msg}', 400
    with open(WORDLIST_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        WORDS = load_words()
        return '上传成功，词库已更新！<br><a href="/admin">返回管理页面</a>'


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)