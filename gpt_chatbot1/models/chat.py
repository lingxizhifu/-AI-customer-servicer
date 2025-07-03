"""
聊天记录数据模型
"""
from datetime import datetime, timezone, timedelta
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 设置中国时区
CHINA_TZ = timezone(timedelta(hours=8))

def get_china_time():
    """获取中国时间"""
    return datetime.now(CHINA_TZ)

def format_china_time(dt):
    """格式化为中国时间"""
    if dt.tzinfo is None:
        # 如果没有时区信息，假设是UTC时间，转换为中国时间
        utc_dt = dt.replace(tzinfo=timezone.utc)
        china_dt = utc_dt.astimezone(CHINA_TZ)
    else:
        china_dt = dt.astimezone(CHINA_TZ)
    
    return china_dt.strftime('%H:%M')

class Chat(db.Model):
    """聊天会话模型"""
    __tablename__ = 'chats'
    
    id = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(200), nullable=False, default='新对话')
    created_at = db.Column(db.DateTime, default=lambda: get_china_time().replace(tzinfo=None))
    updated_at = db.Column(db.DateTime, default=lambda: get_china_time().replace(tzinfo=None), onupdate=lambda: get_china_time().replace(tzinfo=None))
    is_active = db.Column(db.Boolean, default=True)
    
    # 关系：一个聊天包含多条消息
    messages = db.relationship('Message', backref='chat', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        """转换为字典"""
        last_msg = self.messages.order_by(Message.created_at.desc()).first()
        
        # 获取最后一条消息的信息
        last_message_info = None
        if last_msg:
            # 确保时间显示正确
            message_time = get_china_time().strftime('%H:%M')  # 使用当前时间作为显示时间
            last_message_info = {
                'content': last_msg.content[:50] + '...' if len(last_msg.content) > 50 else last_msg.content,
                'sender': last_msg.sender,
                'time': message_time
            }
        
        return {
            'id': self.id,
            'title': self.title,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'message_count': self.messages.count(),
            'last_message': last_message_info
        }

class Message(db.Model):
    """消息模型"""
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.String(50), db.ForeignKey('chats.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(20), nullable=False)  # 'user' 或 'bot'
    created_at = db.Column(db.DateTime, default=lambda: get_china_time().replace(tzinfo=None))
    
    def to_dict(self):
        """转换为字典"""
        # 使用中国时区格式化时间
        china_time = get_china_time().strftime('%H:%M')
        
        return {
            'id': self.id,
            'content': self.content,
            'sender': self.sender,
            'created_at': self.created_at.isoformat(),
            'time': china_time  # 使用当前中国时间
        }