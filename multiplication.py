"""
乘法口诀表消消乐游戏模块
负责乘法游戏的配置和逻辑
"""
from flask import Blueprint

multiplication_bp = Blueprint('multiplication', __name__)

# 当前乘法消消乐游戏逻辑完全在前端实现
# 此模块预留用于未来可能的后端功能扩展
# 例如：游戏数据生成、成绩记录、排行榜等

@multiplication_bp.route('/api/multiplication/config')
def get_config():
    """获取乘法游戏配置"""
    config = {
        'max_number': 9,
        'total_pairs': 10,
        'game_mode': 'match'
    }
    return config

# 未来可扩展的功能：
# - 保存游戏成绩
# - 生成题目数据
# - 难度级别配置
# - 排行榜功能
