"""
聊天服务逻辑
"""
import uuid
from datetime import datetime
from models.chat import db, Chat, Message
from sqlalchemy import or_, and_

class ChatService:
    
    @staticmethod
    def create_new_chat(title="新对话"):
        """创建新聊天"""
        chat_id = str(uuid.uuid4())
        chat = Chat(id=chat_id, title=title)
        db.session.add(chat)
        db.session.commit()
        return chat
    
    @staticmethod
    def save_message(chat_id, content, sender):
        """保存消息到数据库"""
        message = Message(chat_id=chat_id, content=content, sender=sender)
        db.session.add(message)
        
        # 更新聊天的最后更新时间和标题
        chat = Chat.query.get(chat_id)
        if chat:
            chat.updated_at = datetime.utcnow()
            # 如果是第一条用户消息，用它作为聊天标题
            if sender == 'user' and chat.title == '新对话':
                chat.title = content[:30] + '...' if len(content) > 30 else content
        
        db.session.commit()
        return message
    
    @staticmethod
    def get_chat_history(limit=50):
        """获取聊天历史"""
        chats = Chat.query.filter_by(is_active=True).order_by(Chat.updated_at.desc()).limit(limit).all()
        return [chat.to_dict() for chat in chats]
    
    @staticmethod
    def get_chat_messages(chat_id):
        """获取指定聊天的所有消息"""
        chat = Chat.query.get(chat_id)
        if not chat:
            return None
        
        messages = Message.query.filter_by(chat_id=chat_id).order_by(Message.created_at.asc()).all()
        return {
            'chat': chat.to_dict(),
            'messages': [msg.to_dict() for msg in messages]
        }
    
    @staticmethod
    def search_chats(keyword):
        """搜索聊天记录"""
        chats = db.session.query(Chat).join(Message).filter(
            and_(
                Chat.is_active == True,
                or_(
                    Chat.title.contains(keyword),
                    Message.content.contains(keyword)
                )
            )
        ).distinct().order_by(Chat.updated_at.desc()).all()
        return [chat.to_dict() for chat in chats]
    
    @staticmethod
    def delete_chat(chat_id):
        """删除指定聊天"""
        chat = Chat.query.get(chat_id)
        if chat:
            chat.is_active = False
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def clear_all_chats():
        """清空所有聊天记录"""
        chats = Chat.query.filter_by(is_active=True).all()
        for chat in chats:
            chat.is_active = False
        db.session.commit()
        return len(chats)