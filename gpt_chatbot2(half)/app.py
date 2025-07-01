from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import os
import json
import uuid
from dotenv import load_dotenv
from models.chat import db, Chat, Message
from services.chat_service import ChatService

# 🆕 导入RAG服务
try:
    from services.rag_service import get_rag_service
    RAG_ENABLED = True
    print("✅ RAG服务已启用")
except ImportError as e:
    print(f"⚠️ RAG服务未启用: {e}")
    RAG_ENABLED = False

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

# 🆕 RAG配置
RAG_CONFIG = {
    'enabled': RAG_ENABLED,
    'similarity_threshold': float(os.getenv('RAG_SIMILARITY_THRESHOLD', '0.3')),
    'max_relevant_qa': int(os.getenv('RAG_MAX_RELEVANT_QA', '3')),
    'fallback_to_general': os.getenv('RAG_FALLBACK_TO_GENERAL', 'true').lower() == 'true'
}

# 当前聊天ID
current_chat_id = None

# 🆕 初始化RAG服务
if RAG_ENABLED:
    try:
        rag_service = get_rag_service()
        print("🤖 RAG知识库已就绪")
        
        # 显示知识库统计
        stats = rag_service.get_collection_stats()
        print(f"📊 知识库包含 {stats['total_documents']} 条问答数据")
    except Exception as e:
        print(f"❌ RAG服务初始化失败: {e}")
        RAG_ENABLED = False
        RAG_CONFIG['enabled'] = False

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
    """🆕 发送消息并保存到数据库 - RAG增强版本"""
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
        
        # 🆕 RAG增强处理
        rag_info = {}
        system_prompt = "你是一个专业的智能客服助手，名叫'聆析智服'。请用友好、专业、准确的语气回答用户问题，提供有用的帮助。回答要简洁明了，不超过200字。"
        
        if RAG_CONFIG['enabled'] and 'rag_service' in globals():
            try:
                # 获取RAG增强信息
                rag_result = rag_service.get_enhanced_response(user_message)
                
                # 使用增强的prompt
                if rag_result['has_relevant_info'] and rag_result['best_similarity'] >= RAG_CONFIG['similarity_threshold']:
                    system_prompt = rag_result['enhanced_prompt']
                    rag_info = {
                        'used_rag': True,
                        'relevant_qa_count': len(rag_result['relevant_qa']),
                        'best_similarity': rag_result['best_similarity'],
                        'confidence': rag_result['confidence'],
                        'category': rag_result['category']
                    }
                    print(f"🎯 RAG增强回复 - 相似度: {rag_result['best_similarity']}, 置信度: {rag_result['confidence']}")
                else:
                    rag_info = {
                        'used_rag': False,
                        'reason': 'no_relevant_info' if not rag_result['has_relevant_info'] else 'low_similarity',
                        'best_similarity': rag_result['best_similarity'],
                        'category': rag_result['category']
                    }
                    print(f"ℹ️ 使用通用回复 - 相似度过低: {rag_result['best_similarity']}")
                    
            except Exception as e:
                print(f"⚠️ RAG处理出错，使用通用模式: {e}")
                rag_info = {'used_rag': False, 'error': str(e)}
        else:
            rag_info = {'used_rag': False, 'reason': 'rag_disabled'}
        
        # 调用AI API
        if not DEEPSEEK_API_KEY:
            return jsonify({'error': 'API密钥未配置'}), 500
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        # 🆕 根据是否使用RAG调整温度参数
        temperature = 0.1 if rag_info.get('used_rag') else 0.3
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": user_message
                }
            ],
            "max_tokens": 800,
            "temperature": temperature,
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
                'chat_id': current_chat_id,
                'rag_info': rag_info  # 🆕 返回RAG信息
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

# 🆕 =============== RAG相关路由 ===============

@app.route('/rag/status', methods=['GET'])
def get_rag_status():
    """获取RAG系统状态"""
    try:
        if not RAG_CONFIG['enabled']:
            return jsonify({
                'success': True,
                'enabled': False,
                'reason': 'RAG service not available'
            })
        
        stats = rag_service.get_collection_stats()
        return jsonify({
            'success': True,
            'enabled': True,
            'config': RAG_CONFIG,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/rag/search', methods=['POST'])
def search_knowledge():
    """搜索知识库"""
    try:
        if not RAG_CONFIG['enabled']:
            return jsonify({'success': False, 'error': 'RAG服务未启用'}), 503
        
        data = request.get_json()
        query = data.get('query', '').strip()
        top_k = data.get('top_k', 10)
        
        if not query:
            return jsonify({'error': '搜索查询不能为空'}), 400
        
        results = rag_service.retrieve_relevant_qa(query, top_k=top_k)
        
        return jsonify({
            'success': True,
            'results': results,
            'query': query,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 创建数据库表
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    print("🚀 AI客服助手启动中...")
    print("🤖 使用DeepSeek AI引擎")
    print("💾 数据库: SQLite")
    
    if RAG_CONFIG['enabled']:
        print("🧠 RAG知识库: 已启用")
        if 'rag_service' in globals():
            stats = rag_service.get_collection_stats()
            print(f"📚 知识库包含: {stats['total_documents']} 条问答")
    else:
        print("⚠️ RAG知识库: 未启用")
    
    if not DEEPSEEK_API_KEY:
        print("❌ 警告: 请设置DEEPSEEK_API_KEY")
    
    print("📱 访问地址: http://localhost:5000")
    print("-" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)