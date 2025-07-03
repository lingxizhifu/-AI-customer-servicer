from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import os
import json
import uuid
from dotenv import load_dotenv
from models.chat import db, Chat, Message
from services.chat_service import ChatService

# 加载环境变量
load_dotenv()

# 创建Flask应用
app = Flask(__name__)
CORS(app)

# 数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

# 初始化数据库
db.init_app(app)

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

# 当前聊天ID
current_chat_id = None

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/chat/new', methods=['POST'])
def new_chat():
    """创建新聊天"""
    global current_chat_id
    try:
        chat = ChatService.create_new_chat()
        current_chat_id = chat.id
        return jsonify({
            'success': True,
            'chat_id': chat.id,
            'message': '已创建新聊天'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/chat/send', methods=['POST'])
def send_message():
    """发送消息并保存到数据库"""
    global current_chat_id
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': '消息不能为空'}), 400
        
        # 如果没有当前聊天，创建新聊天
        if not current_chat_id:
            chat = ChatService.create_new_chat()
            current_chat_id = chat.id
        
        # 保存用户消息
        ChatService.save_message(current_chat_id, user_message, 'user')
        
        # 调用AI API
        if not DEEPSEEK_API_KEY:
            return jsonify({'error': 'API密钥未配置'}), 500
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的智能客服助手，名叫'聆析智服'。请用友好、专业、准确的语气回答用户问题，提供有用的帮助。回答要简洁明了，不超过200字。"
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "max_tokens": 800,
            "temperature": 0.3,
            "stream": False
        }
        
        response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            ai_message = result['choices'][0]['message']['content']
            
            # 保存AI回复
            ChatService.save_message(current_chat_id, ai_message, 'bot')
            
            return jsonify({
                'success': True,
                'message': ai_message,
                'chat_id': current_chat_id
            })
        else:
            return jsonify({'success': False, 'error': 'AI服务暂时不可用'}), 500
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return jsonify({'success': False, 'error': '服务暂时不可用'}), 500

@app.route('/chat/history', methods=['GET'])
def get_chat_history():
    """获取聊天历史"""
    try:
        chats = ChatService.get_chat_history()
        return jsonify({'success': True, 'chats': chats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/chat/<chat_id>/messages', methods=['GET'])
def get_chat_messages(chat_id):
    """获取指定聊天的消息"""
    global current_chat_id
    try:
        chat_data = ChatService.get_chat_messages(chat_id)
        if not chat_data:
            return jsonify({'success': False, 'error': '聊天不存在'}), 404
        
        current_chat_id = chat_id
        return jsonify({'success': True, 'data': chat_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/chat/search', methods=['GET'])
def search_chats():
    """搜索聊天记录"""
    try:
        keyword = request.args.get('keyword', '').strip()
        if not keyword:
            return jsonify({'success': False, 'error': '搜索关键词不能为空'}), 400
        
        chats = ChatService.search_chats(keyword)
        return jsonify({'success': True, 'chats': chats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/chat/clear', methods=['POST'])
def clear_chats():
    """清空所有聊天记录"""
    global current_chat_id
    try:
        count = ChatService.clear_all_chats()
        current_chat_id = None
        return jsonify({
            'success': True,
            'message': f'已清空 {count} 条聊天记录'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/chat/<chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """删除指定聊天"""
    global current_chat_id
    try:
        success = ChatService.delete_chat(chat_id)
        if success:
            if current_chat_id == chat_id:
                current_chat_id = None
            return jsonify({'success': True, 'message': '聊天已删除'})
        else:
            return jsonify({'success': False, 'error': '聊天不存在'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 创建数据库表
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    print("🚀 AI客服助手启动中...")
    print("🤖 使用DeepSeek AI引擎")
    print("💾 数据库: SQLite")
    
    if not DEEPSEEK_API_KEY:
        print("❌ 警告: 请设置DEEPSEEK_API_KEY")
    
    print("📱 访问地址: http://localhost:5000")
    print("-" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)