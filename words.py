"""
字字大冒险游戏模块
负责词库管理和游戏逻辑
"""
from flask import Blueprint, jsonify, request, render_template
import json
import os
import random

words_bp = Blueprint('words', __name__)

WORD_LIST_FILE = 'word_list.json'

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

@words_bp.route('/api/words', methods=['GET'])
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

@words_bp.route('/api/words', methods=['POST'])
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

@words_bp.route('/admin')
def admin_page():
    """词库管理页面"""
    return render_template('admin.html')

@words_bp.route('/start')
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
