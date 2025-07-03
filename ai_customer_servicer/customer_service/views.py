from django.shortcuts import render
import requests
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from rest_framework import viewsets
from .models import FAQ, Chat, Message, Profile
from .serializers import FAQSerializer, ChatSerializer, MessageSerializer, UserProfileSerializer
from openai import OpenAI
import uuid
from django.shortcuts import redirect
from django.db.models import Q
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
import random
from django.contrib.auth.decorators import login_required
from rest_framework.parsers import MultiPartParser, FormParser
from customer_service.rag_service import get_rag_service
# 在你的 views.py 文件中添加以下用户管理相关的视图函数

from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import user_passes_test
from datetime import datetime, timedelta
from django.utils import timezone

#add new
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_real_time_stats(request):
    """获取实时统计数据"""
    try:
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        # 获取当前日期
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # 总使用次数（Message总数）
        total_usage = Message.objects.count()
        yesterday_total_usage = Message.objects.filter(created_at__date__lt=today).count()
        
        # 今日对话量
        today_chats = Chat.objects.filter(created_at__date=today).count()
        yesterday_chats = Chat.objects.filter(created_at__date=yesterday).count()
        
        # 计算今日对话量变化百分比
        if yesterday_chats > 0:
            chats_change_percent = round(((today_chats - yesterday_chats) / yesterday_chats) * 100)
        else:
            chats_change_percent = 100 if today_chats > 0 else 0
        
        # 问题解决率计算（基于对话中是否有AI回复作为解决标准）
        total_chats_with_messages = Chat.objects.filter(messages__isnull=False).distinct().count()
        solved_chats = Chat.objects.filter(
            messages__sender='bot'
        ).distinct().count()
        
        if total_chats_with_messages > 0:
            solve_rate_percent = round((solved_chats / total_chats_with_messages) * 100)
        else:
            solve_rate_percent = 0
        
        # 昨天的问题解决率
        yesterday_total_chats = Chat.objects.filter(
            created_at__date=yesterday,
            messages__isnull=False
        ).distinct().count()
        yesterday_solved_chats = Chat.objects.filter(
            created_at__date=yesterday,
            messages__sender='bot'
        ).distinct().count()
        
        if yesterday_total_chats > 0:
            yesterday_solve_rate = round((yesterday_solved_chats / yesterday_total_chats) * 100)
        else:
            yesterday_solve_rate = 0
        
        solve_rate_change = solve_rate_percent - yesterday_solve_rate
        
        # 今日投诉（基于包含负面词汇的用户消息）
        negative_keywords = ['投诉', '问题', '错误', '不满', '差', '烂', '垃圾', '退款', '客服']
        today_complaints = Message.objects.filter(
            created_at__date=today,
            sender='user',
            content__iregex=r'(' + '|'.join(negative_keywords) + ')'
        ).count()
        
        yesterday_complaints = Message.objects.filter(
            created_at__date=yesterday,
            sender='user',
            content__iregex=r'(' + '|'.join(negative_keywords) + ')'
        ).count()
        
        # 计算投诉变化百分比
        if yesterday_complaints > 0:
            complaints_change_percent = round(((today_complaints - yesterday_complaints) / yesterday_complaints) * 100)
        else:
            complaints_change_percent = 100 if today_complaints > 0 else 0
        
        # API使用量（今日消息总数，包括用户和AI）
        today_api_usage = Message.objects.filter(created_at__date=today).count()
        
        # 计算总使用次数变化
        total_usage_change = total_usage - yesterday_total_usage
        
        return Response({
            'success': True,
            'data': {
                'total_usage': total_usage,
                'total_usage_change': f"+{total_usage_change}" if total_usage_change >= 0 else str(total_usage_change),
                'today_chats': today_chats,
                'chats_change_percent': chats_change_percent,
                'chats_change_text': f"{abs(chats_change_percent)}%{'↑' if chats_change_percent >= 0 else '↓'}",
                'solve_rate': f"{solve_rate_percent}%",
                'solve_rate_change': solve_rate_change,
                'solve_rate_change_text': f"{abs(solve_rate_change)}%{'↑' if solve_rate_change >= 0 else '↓'}",
                'today_complaints': today_complaints,
                'complaints_change_percent': complaints_change_percent,
                'complaints_change_text': f"{abs(complaints_change_percent)}%{'↑' if complaints_change_percent >= 0 else '↓'}",
                'today_api_usage': today_api_usage,
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'error': f'获取统计数据失败: {str(e)}'
        }, status=500)

#add new
# 检查是否为超级用户的装饰器
def is_superuser(user):
    return user.is_superuser

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_users_list(request):
    """获取用户列表（带分页和搜索）"""
    if not request.user.is_superuser:
        return Response({'error': '权限不足'}, status=403)
    
    # 获取查询参数
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))
    search = request.GET.get('search', '').strip()
    
    # 构建查询条件
    users = User.objects.all().order_by('-date_joined')
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    # 分页
    paginator = Paginator(users, page_size)
    page_obj = paginator.get_page(page)
    
    # 构造返回数据
    users_data = []
    for user in page_obj:
        # 获取用户角色
        if user.is_superuser:
            role = "超级管理员"
            permissions = "全权限"
        elif user.is_staff:
            role = "编辑员"
            permissions = "可编辑"
        else:
            role = "查看员"
            permissions = "只读"
        
        # 获取最后登录时间
        last_login = user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else '从未登录'
        
        # 判断在线状态（这里简化处理，可以根据实际需求调整）
        is_online = user.last_login and user.last_login > timezone.now() - timedelta(minutes=30) if user.last_login else False
        
        # 获取头像（从profile中）
        avatar_text = user.username[0].upper() if user.username else 'U'
        avatar_color = generate_avatar_color(user.id)
        
        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': role,
            'permissions': permissions,
            'last_login': last_login,
            'is_online': is_online,
            'status': '在线' if is_online else '离线',
            'avatar_text': avatar_text,
            'avatar_color': avatar_color,
            'is_active': user.is_active,
            'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M')
        })
    
    return Response({
        'users': users_data,
        'total': paginator.count,
        'current_page': page,
        'total_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous()
    })

def generate_avatar_color(user_id):
    """根据用户ID生成头像颜色"""
    colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', 
        '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD'
    ]
    return colors[user_id % len(colors)]

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_user(request):
    """创建新用户"""
    if not request.user.is_superuser:
        return Response({'error': '权限不足'}, status=403)
    
    data = request.data
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'viewer')  # admin, editor, viewer
    first_name = data.get('first_name', '').strip()
    last_name = data.get('last_name', '').strip()
    
    # 验证必填字段
    if not username or not password:
        return Response({'error': '用户名和密码不能为空'}, status=400)
    
    # 检查用户名是否已存在
    if User.objects.filter(username=username).exists():
        return Response({'error': '用户名已存在'}, status=400)
    
    # 检查邮箱是否已存在
    if email and User.objects.filter(email=email).exists():
        return Response({'error': '邮箱已被使用'}, status=400)
    
    try:
        # 创建用户
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # 设置角色权限
        if role == 'admin':
            user.is_superuser = True
            user.is_staff = True
        elif role == 'editor':
            user.is_staff = True
        # viewer 默认权限即可
        
        user.save()
        
        # 创建对应的Profile
        from .models import Profile
        Profile.objects.create(user=user)
        
        return Response({'success': True, 'message': '用户创建成功', 'user_id': user.id})
    
    except Exception as e:
        return Response({'error': f'创建用户失败: {str(e)}'}, status=500)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user(request, user_id):
    """更新用户信息"""
    if not request.user.is_superuser:
        return Response({'error': '权限不足'}, status=403)
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': '用户不存在'}, status=404)
    
    data = request.data
    
    # 更新基本信息
    if 'username' in data:
        username = data['username'].strip()
        if username != user.username and User.objects.filter(username=username).exists():
            return Response({'error': '用户名已存在'}, status=400)
        user.username = username
    
    if 'email' in data:
        email = data['email'].strip()
        if email != user.email and User.objects.filter(email=email).exists():
            return Response({'error': '邮箱已被使用'}, status=400)
        user.email = email
    
    if 'first_name' in data:
        user.first_name = data['first_name'].strip()
    
    if 'last_name' in data:
        user.last_name = data['last_name'].strip()
    
    # 更新密码（如果提供）
    if 'password' in data and data['password'].strip():
        user.set_password(data['password'].strip())
    
    # 更新角色权限
    if 'role' in data:
        role = data['role']
        if role == 'admin':
            user.is_superuser = True
            user.is_staff = True
        elif role == 'editor':
            user.is_superuser = False
            user.is_staff = True
        else:  # viewer
            user.is_superuser = False
            user.is_staff = False
    
    # 更新状态
    if 'is_active' in data:
        user.is_active = data['is_active']
    
    try:
        user.save()
        return Response({'success': True, 'message': '用户信息更新成功'})
    except Exception as e:
        return Response({'error': f'更新失败: {str(e)}'}, status=500)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user(request, user_id):
    """删除用户"""
    if not request.user.is_superuser:
        return Response({'error': '权限不足'}, status=403)
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': '用户不存在'}, status=404)
    
    # 不能删除自己
    if user.id == request.user.id:
        return Response({'error': '不能删除自己的账户'}, status=400)
    
    try:
        user.delete()
        return Response({'success': True, 'message': '用户删除成功'})
    except Exception as e:
        return Response({'error': f'删除失败: {str(e)}'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_detail(request, user_id):
    """获取用户详细信息"""
    if not request.user.is_superuser:
        return Response({'error': '权限不足'}, status=403)
    
    try:
        user = User.objects.get(id=user_id)
        
        # 获取角色
        if user.is_superuser:
            role = "admin"
        elif user.is_staff:
            role = "editor"
        else:
            role = "viewer"
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': role,
            'is_active': user.is_active,
            'last_login': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None,
            'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        # 尝试获取Profile信息
        try:
            if hasattr(user, 'profile'):
                user_data.update({
                    'nickname': user.profile.nickname,
                    'mobile': user.profile.mobile,
                    'avatar': user.profile.avatar.url if user.profile.avatar else None
                })
        except:
            pass
        
        return Response(user_data)
    
    except User.DoesNotExist:
        return Response({'error': '用户不存在'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def batch_delete_users(request):
    """批量删除用户"""
    if not request.user.is_superuser:
        return Response({'error': '权限不足'}, status=403)
    
    user_ids = request.data.get('user_ids', [])
    if not user_ids:
        return Response({'error': '请选择要删除的用户'}, status=400)
    
    # 不能删除自己
    if request.user.id in user_ids:
        return Response({'error': '不能删除自己的账户'}, status=400)
    
    try:
        deleted_count = User.objects.filter(id__in=user_ids).delete()[0]
        return Response({
            'success': True, 
            'message': f'成功删除 {deleted_count} 个用户'
        })
    except Exception as e:
        return Response({'error': f'批量删除失败: {str(e)}'}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_users(request):
    """导出用户数据"""
    if not request.user.is_superuser:
        return Response({'error': '权限不足'}, status=403)
    
    users = User.objects.all().order_by('-date_joined')
    
    export_data = []
    for user in users:
        role = "超级管理员" if user.is_superuser else ("编辑员" if user.is_staff else "查看员")
        export_data.append({
            'ID': user.id,
            '用户名': user.username,
            '邮箱': user.email,
            '姓名': f"{user.first_name} {user.last_name}".strip(),
            '角色': role,
            '状态': '激活' if user.is_active else '禁用',
            '最后登录': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '从未登录',
            '注册时间': user.date_joined.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return Response({
        'success': True,
        'data': export_data,
        'total': len(export_data)
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_user_status(request, user_id):
    """切换用户激活状态"""
    if not request.user.is_superuser:
        return Response({'error': '权限不足'}, status=403)
    
    try:
        user = User.objects.get(id=user_id)
        
        # 不能禁用自己
        if user.id == request.user.id:
            return Response({'error': '不能禁用自己的账户'}, status=400)
        
        user.is_active = not user.is_active
        user.save()
        
        status_text = '激活' if user.is_active else '禁用'
        return Response({
            'success': True, 
            'message': f'用户已{status_text}',
            'is_active': user.is_active
        })
    
    except User.DoesNotExist:
        return Response({'error': '用户不存在'}, status=404)

#add new

@login_required(login_url='/login/')
def index(request):
    return render(request, 'index.html', {'user': request.user})

@login_required(login_url='/login/')
def user_index(request):
    return render(request, 'user_index.html', {'user': request.user})

class FAQViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer

DEEPSEEK_API_KEY = "sk-320e041c3508449388c6074324ba0095"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

def call_deepseek_ai(user_message=None, messages=None):
    """
    通用AI调用函数：
    - 传user_message时，自动构造标准对话消息
    - 传messages时，直接用自定义消息列表
    """
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    try:
        if messages is None:
            messages = [
                {"role": "system", "content": "你是一个专业的电商客服助手，隶属于淘宝平台，按照相关要求回复客户问题。请用不超过150字、精炼简洁地回答用户问题。"},
                {"role": "user", "content": user_message}
            ]
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            stream=False
        )
        reply = response.choices[0].message.content
        return reply[:150]
    except Exception as e:
        print("调用deepseek出错：", e)
        return "AI回复失败"

@api_view(['GET', 'POST'])
def create_chat_and_history(request):
    if request.method == 'POST':
        # 新建对话
        title = request.data.get('title', '新对话')
        chat = Chat.objects.create(title=title)
        serializer = ChatSerializer(chat)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        # 获取历史对话
        chats = Chat.objects.filter(is_active=True).order_by('-updated_at')
        serializer = ChatSerializer(chats, many=True)
        return Response(serializer.data)

@api_view(['POST'])
def send_message(request, chat_id):
    user_message = request.data.get('message', '')
    kb = request.GET.get('kb', request.data.get('kb', 'default'))
    kb_table_map = {
        'default': 'qa_data',
        'fashion': 'fashion_qa_data',
        'laobeijing': 'lbj_qa_data',  # 新增体育用品客服表
        # 可扩展更多
    }
    table_name = kb_table_map.get(kb, 'qa_data')
    if not user_message:
        return Response({'error': '消息不能为空'}, status=400)
    try:
        chat = Chat.objects.get(id=chat_id, is_active=True)
    except Chat.DoesNotExist:
        return Response({'error': '对话不存在'}, status=404)
    if Message.objects.filter(chat=chat, sender='user').count() == 0:
        new_title = user_message.strip().replace('\n', ' ')[:20]
        chat.title = new_title if new_title else '新对话'
        chat.save()
    Message.objects.create(chat=chat, content=user_message, sender='user')
    rag_service = get_rag_service()
    rag_result = rag_service.get_enhanced_response(user_message, table_name=table_name)
    enhanced_prompt = rag_result['enhanced_prompt']
    # 兜底：无知识库时查找tone表的描述
    import pymysql
    tone_id = None
    try:
        conn = pymysql.connect(host='localhost', port=3306, user='root', password='Awc5624/', database='ragdb', charset='utf8mb4')
        with conn.cursor() as cursor:
            # 优先查当前表的 tone_id
            cursor.execute(f"SELECT tone_id FROM {table_name} WHERE tone_id IS NOT NULL LIMIT 1")
            row = cursor.fetchone()
            if row and row[0]:
                tone_id = row[0]
            else:
                tone_id = 1  # 没查到就用默认
            cursor.execute("SELECT description FROM tone WHERE id=%s", (tone_id,))
            tone_row = cursor.fetchone()
            tone_desc = tone_row[0] if tone_row and tone_row[0] else '亲切友好，专业简洁'
        conn.close()
    except Exception as e:
        print("获取tone描述失败：", e)
        tone_desc = '亲切友好，专业简洁'
    print(f"【RAG】知识库无命中，启用兜底风格：{table_name}")
    enhanced_prompt = (
        f"你是一个专业的智能客服助手，名叫'聆析智服'。请用如下风格回答：{tone_desc}\n"
        f"用户问题: {user_message}\n"
        "如果你不知道答案，也请礼貌回复用户，可以从网络相关知识中获取信息并尽量给出有帮助的建议"
    )
    print("最终AI prompt：", enhanced_prompt)
    print(f"【DEBUG】当前kb参数：{kb}，table_name：{table_name}")
    try:
        ai_reply = call_deepseek_ai(user_message=enhanced_prompt)
    except Exception as e:
        print("AI接口异常：", e)
        ai_reply = "很抱歉，当前AI服务暂时无法回答您的问题。"
    Message.objects.create(chat=chat, content=ai_reply, sender='bot')
    chat.updated_at = chat.messages.latest('created_at').created_at
    chat.save()
    return Response({'ai_reply': ai_reply})

@api_view(['GET'])
def chat_messages(request, chat_id):
    """获取指定对话的所有消息"""
    try:
        chat = Chat.objects.get(id=chat_id, is_active=True)
    except Chat.DoesNotExist:
        return Response({'error': '对话不存在'}, status=404)
    messages = chat.messages.order_by('created_at')
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def search_chats(request):
    """搜索对话（按标题或消息内容）"""
    keyword = request.GET.get('keyword', '').strip()
    if not keyword:
        # 关键词为空时，返回全部对话
        chats = Chat.objects.filter(is_active=True).order_by('-updated_at')
        serializer = ChatSerializer(chats, many=True)
        return Response(serializer.data)
    chats = Chat.objects.filter(
        Q(is_active=True) & (
            Q(title__icontains=keyword) |
            Q(messages__content__icontains=keyword)
        )
    ).distinct().order_by('-updated_at')
    serializer = ChatSerializer(chats, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def clear_chats(request):
    """清空所有对话"""
    count = Chat.objects.filter(is_active=True).update(is_active=False)
    return Response({'message': f'已清空 {count} 条对话'})

@api_view(['DELETE'])
def delete_chat(request, chat_id):
    """删除指定对话"""
    try:
        chat = Chat.objects.get(id=chat_id, is_active=True)
        chat.is_active = False
        chat.save()
        return Response({'message': '对话已删除'})
    except Chat.DoesNotExist:
        return Response({'error': '对话不存在'}, status=404)

@api_view(['GET'])
def ai_polish_faq_answer(request, pk):
    try:
        faq = FAQ.objects.get(pk=pk)
    except FAQ.DoesNotExist:
        return Response({"error": "FAQ not found"}, status=404)

    messages = [
        {"role": "system", "content": "你是一个处理用户反馈的智能客服。请根据给定的标准答案，结合用户问题，给出专业、简洁、友好的回复。请用不超过150字、精炼简洁地回答。"},
        {"role": "user", "content": f"用户问题：{faq.question}\n标准答案：{faq.answer}"},
    ]
    ai_response = call_deepseek_ai(messages=messages)
    return Response({
        "question": faq.question,
        "polished_answer": ai_response
    })

# 登录页渲染
@api_view(['GET'])
def login_page(request):
    request.session['captcha'] = generate_captcha_code()
    return render(request, 'login.html')

# 登录接口
@api_view(['POST'])
def login_submit(request):
    data = request.data
    if data.get('captcha', '').lower() != request.session.get('captcha', '').lower():
        return Response({'success': False, 'message': '验证码错误'})
    user = authenticate(request, username=data.get('username'), password=data.get('password'))
    if user is not None:
        login(request, user)
        return Response({'success': True, 'message': '登录成功！即将跳转到主页面...', 'is_superuser': user.is_superuser})
    else:
        return Response({'success': False, 'message': '用户名或密码错误'})

# 注册接口
@api_view(['POST'])
def register_submit(request):
    data = request.data
    if data.get('captcha', '').lower() != request.session.get('captcha', '').lower():
        return Response({'success': False, 'message': '验证码错误'})
    if User.objects.filter(username=data.get('username')).exists():
        return Response({'success': False, 'message': '用户名已存在'})
    if data.get('password') != data.get('confirm_password'):
        return Response({'success': False, 'message': '两次密码输入不一致'})
    User.objects.create_user(data.get('username'), password=data.get('password'))
    return Response({'success': True, 'message': '注册成功！请使用新账号登录。'})

# 生成验证码接口
@api_view(['GET'])
def generate_captcha(request):
    captcha = generate_captcha_code()
    request.session['captcha'] = captcha
    return Response({'captcha': captcha})

def generate_captcha_code():
    chars = 'ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789'
    return ''.join(random.choice(chars) for _ in range(4))

# 忘记密码接口（仅返回提示）
@api_view(['POST'])
def forgot_password(request):
    email = request.data.get('email')
    if email:
        return Response({'success': True, 'message': '密码重置链接已发送到您的邮箱'})
    return Response({'success': False, 'message': '请输入有效的邮箱地址'})

# 登出接口
@api_view(['GET'])
def logout_view(request):
    logout(request)
    return redirect('/login/')

@api_view(['GET'])
def faq_groups(request):
    groups = []
    categories = FAQ.objects.values_list('category', flat=True).distinct()
    for cat in categories:
        questions = [
            {"id": f.id, "question": f.question}
            for f in FAQ.objects.filter(category=cat)
        ]
        groups.append({
            "group": f"关于{cat}，我猜你想咨询：",
            "questions": questions
        })
    return Response({
        "groups": groups
    })

def admin_index(request):
    return render(request, 'admin_index.html')

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def user_profile(request):
    user = request.user
    # GET: 返回信息
    if request.method == 'GET':
        # 自动补全Profile
        if not hasattr(user, 'profile') or user.profile is None:
            from .models import Profile
            Profile.objects.create(user=user)
            user.refresh_from_db()
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)
    # POST: 修改信息
    elif request.method == 'POST':
        profile = user.profile
        nickname = request.data.get('nickname', '').strip()
        mobile = request.data.get('mobile', '').strip()
        email = request.data.get('email', '').strip()
        avatar = request.FILES.get('avatar')
        if nickname:
            profile.nickname = nickname
        if mobile:
            profile.mobile = mobile
        if email:
            user.email = email
            user.save()
        if avatar:
            profile.avatar = avatar
        profile.save()
        return Response({'success': True, 'message': '信息修改成功！'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def user_avatar_upload(request):
    profile = request.user.profile
    avatar_file = request.FILES.get('avatar')
    if not avatar_file:
        return Response({'success': False, 'message': '未上传文件'}, status=400)
    profile.avatar = avatar_file
    profile.save()
    return Response({'success': True, 'avatar': profile.avatar.url})

def overview_management(request):
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    # 获取当前日期
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # 总使用次数（Message总数）
    total_usage = Message.objects.count()
    
    # 今日对话量
    today_chats = Chat.objects.filter(created_at__date=today).count()
    
    # 问题解决率计算（基于对话中是否有AI回复作为解决标准）
    total_chats_with_messages = Chat.objects.filter(messages__isnull=False).distinct().count()
    solved_chats = Chat.objects.filter(messages__sender='bot').distinct().count()
    
    if total_chats_with_messages > 0:
        solve_rate_percent = round((solved_chats / total_chats_with_messages) * 100)
        solve_rate = f"{solve_rate_percent}%"
    else:
        solve_rate = "0%"
    
    # 今日投诉（基于包含负面词汇的用户消息）
    negative_keywords = ['投诉', '问题', '错误', '不满', '差', '烂', '垃圾', '退款', '客服']
    today_complaints = Message.objects.filter(
        created_at__date=today,
        sender='user',
        content__iregex=r'(' + '|'.join(negative_keywords) + ')'
    ).count()
    
    # API使用量（今日消息总数）
    today_api_usage = Message.objects.filter(created_at__date=today).count()

    context = {
        'total_usage': total_usage,
        'today_chats': today_chats,
        'solve_rate': solve_rate,
        'today_complaints': today_complaints,
        'today_api_usage': today_api_usage,
    }
    return render(request, 'overview_management.html', context)

def users_management(request):
    return render(request, 'users_management.html')

# FAQ管理页面视图 - 修复版
@login_required(login_url='/login/')
def faq_management(request):
    """FAQ管理页面"""
    return render(request, 'faq_management.html', {'user': request.user})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def batch_enable_users(request):
    """批量激活用户"""
    if not request.user.is_superuser:
        return Response({'error': '权限不足'}, status=403)
    user_ids = request.data.get('user_ids', [])
    if not user_ids:
        return Response({'error': '请选择要激活的用户'}, status=400)
    # 不能激活自己以外的超级管理员（可选，视需求）
    updated = User.objects.filter(id__in=user_ids).update(is_active=True)
    return Response({'success': True, 'message': f'成功激活 {updated} 个用户'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def batch_disable_users(request):
    """批量禁用用户"""
    if not request.user.is_superuser:
        return Response({'error': '权限不足'}, status=403)
    user_ids = request.data.get('user_ids', [])
    if not user_ids:
        return Response({'error': '请选择要禁用的用户'}, status=400)
    # 不能禁用自己
    if request.user.id in user_ids:
        return Response({'error': '不能禁用自己的账户'}, status=400)
    updated = User.objects.filter(id__in=user_ids).update(is_active=False)
    return Response({'success': True, 'message': f'成功禁用 {updated} 个用户'})

# ===================以下是修复后的FAQ管理相关视图函数===================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_faqs_list(request):
    """获取FAQ列表（带分页和搜索）- 修复版"""
    try:
        # 获取查询参数
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))
        search = request.GET.get('search', '').strip()
        category = request.GET.get('category', '').strip()
        status = request.GET.get('status', '').strip()
        
        # 构建查询条件
        faqs = FAQ.objects.all().order_by('-id')
        
        # 关键词搜索
        if search:
            faqs = faqs.filter(
                Q(question__icontains=search) |
                Q(answer__icontains=search)
            )
        
        # 分类筛选
        if category:
            faqs = faqs.filter(category=category)
        
        # 状态筛选 (基于is_main字段，True为启用，False为禁用)
        if status == 'active':
            faqs = faqs.filter(is_main=True)
        elif status == 'inactive':
            faqs = faqs.filter(is_main=False)
        
        # 分页
        paginator = Paginator(faqs, page_size)
        page_obj = paginator.get_page(page)
        
        # 构造返回数据
        faqs_data = []
        for faq in page_obj:
            # 格式化时间
            created_time = faq.created_at.strftime('%Y-%m-%d') if hasattr(faq, 'created_at') and faq.created_at else timezone.now().strftime('%Y-%m-%d')
            updated_time = faq.updated_at.strftime('%Y-%m-%d') if hasattr(faq, 'updated_at') and faq.updated_at else timezone.now().strftime('%Y-%m-%d')
            
            faqs_data.append({
                'id': faq.id,
                'question': faq.question,
                'answer': faq.answer,
                'category': faq.category,
                'is_main': faq.is_main,
                'status_text': '启用' if faq.is_main else '禁用',
                'created_time': created_time,
                'updated_time': updated_time,
            })
        
        return Response({
            'faqs': faqs_data,
            'total': paginator.count,
            'current_page': page,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous()
        })
    
    except Exception as e:
        return Response({
            'error': f'获取FAQ列表失败: {str(e)}'
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_faq(request):
    """创建新FAQ - 修复版"""
    try:
        data = request.data
        question = data.get('question', '').strip()
        answer = data.get('answer', '').strip()
        category = data.get('category', '常见问题').strip()
        is_main = data.get('is_main', True)
        
        # 验证必填字段
        if not question or not answer:
            return Response({
                'success': False,
                'error': '问题和答案不能为空'
            }, status=400)
        
        # 检查是否已存在相同的问题
        if FAQ.objects.filter(question=question).exists():
            return Response({
                'success': False,
                'error': '该问题已经存在'
            }, status=400)
        
        faq = FAQ.objects.create(
            question=question,
            answer=answer,
            category=category,
            is_main=is_main
        )
        
        return Response({
            'success': True, 
            'message': 'FAQ创建成功', 
            'faq_id': faq.id
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'error': f'创建FAQ失败: {str(e)}'
        }, status=500)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_faq(request, faq_id):
    """更新FAQ信息 - 修复版"""
    try:
        faq = FAQ.objects.get(id=faq_id)
    except FAQ.DoesNotExist:
        return Response({
            'success': False,
            'error': 'FAQ不存在'
        }, status=404)
    
    try:
        data = request.data
        
        # 更新字段
        if 'question' in data:
            new_question = data['question'].strip()
            # 检查是否与其他FAQ重复（排除自己）
            if new_question != faq.question and FAQ.objects.filter(question=new_question).exclude(id=faq.id).exists():
                return Response({
                    'success': False,
                    'error': '该问题已经存在'
                }, status=400)
            faq.question = new_question
        
        if 'answer' in data:
            faq.answer = data['answer'].strip()
        
        if 'category' in data:
            faq.category = data['category'].strip()
        
        if 'is_main' in data:
            faq.is_main = data['is_main']
        
        # 验证必填字段
        if not faq.question or not faq.answer:
            return Response({
                'success': False,
                'error': '问题和答案不能为空'
            }, status=400)
        
        faq.save()
        return Response({
            'success': True, 
            'message': 'FAQ更新成功'
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'error': f'更新失败: {str(e)}'
        }, status=500)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_faq(request, faq_id):
    """删除FAQ - 修复版"""
    try:
        faq = FAQ.objects.get(id=faq_id)
        faq.delete()
        return Response({
            'success': True, 
            'message': 'FAQ删除成功'
        })
    except FAQ.DoesNotExist:
        return Response({
            'success': False,
            'error': 'FAQ不存在'
        }, status=404)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'删除失败: {str(e)}'
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_faq_detail(request, faq_id):
    """获取FAQ详细信息 - 修复版"""
    try:
        faq = FAQ.objects.get(id=faq_id)
        
        faq_data = {
            'id': faq.id,
            'question': faq.question,
            'answer': faq.answer,
            'category': faq.category,
            'is_main': faq.is_main,
        }
        
        return Response(faq_data)
    
    except FAQ.DoesNotExist:
        return Response({
            'error': 'FAQ不存在'
        }, status=404)
    except Exception as e:
        return Response({
            'error': f'获取FAQ详情失败: {str(e)}'
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def batch_delete_faqs(request):
    """批量删除FAQ - 修复版"""
    try:
        faq_ids = request.data.get('faq_ids', [])
        if not faq_ids:
            return Response({
                'success': False,
                'error': '请选择要删除的FAQ'
            }, status=400)
        
        deleted_count = FAQ.objects.filter(id__in=faq_ids).delete()[0]
        return Response({
            'success': True, 
            'message': f'成功删除 {deleted_count} 个FAQ'
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': f'批量删除失败: {str(e)}'
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_faqs(request):
    """导出FAQ数据 - 修复版"""
    try:
        faqs = FAQ.objects.all().order_by('-id')
        
        export_data = []
        for faq in faqs:
            created_time = faq.created_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(faq, 'created_at') and faq.created_at else ''
            updated_time = faq.updated_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(faq, 'updated_at') and faq.updated_at else ''
            
            export_data.append({
                'ID': faq.id,
                '问题': faq.question,
                '答案': faq.answer,
                '分类': faq.category,
                '状态': '启用' if faq.is_main else '禁用',
                '创建时间': created_time,
                '更新时间': updated_time,
            })
        
        return Response({
            'success': True,
            'data': export_data,
            'total': len(export_data)
        })
    
    except Exception as e:
        return Response({
            'success': False,
            'error': f'导出失败: {str(e)}'
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_faq_status(request, faq_id):
    """切换FAQ状态 - 修复版"""
    try:
        faq = FAQ.objects.get(id=faq_id)
        faq.is_main = not faq.is_main
        faq.save()
        
        status_text = '启用' if faq.is_main else '禁用'
        return Response({
            'success': True, 
            'message': f'FAQ已{status_text}',
            'is_main': faq.is_main
        })
    
    except FAQ.DoesNotExist:
        return Response({
            'success': False,
            'error': 'FAQ不存在'
        }, status=404)
    except Exception as e:
        return Response({
            'success': False,
            'error': f'操作失败: {str(e)}'
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_faq_categories(request):
    """获取FAQ分类列表 - 修复版"""
    try:
        categories = FAQ.objects.values_list('category', flat=True).distinct()
        return Response({
            'categories': list(categories)
        })
    except Exception as e:
        return Response({
            'error': f'获取分类失败: {str(e)}'
        }, status=500)

# Create your views here.