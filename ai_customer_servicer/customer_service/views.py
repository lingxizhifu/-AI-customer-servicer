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
    """发送消息并AI回复"""
    user_message = request.data.get('message', '')
    if not user_message:
        return Response({'error': '消息不能为空'}, status=400)
    try:
        chat = Chat.objects.get(id=chat_id, is_active=True)
    except Chat.DoesNotExist:
        return Response({'error': '对话不存在'}, status=404)
    # 检查是否为该对话的第一条用户消息
    if Message.objects.filter(chat=chat, sender='user').count() == 0:
        # 取前20字作为标题
        new_title = user_message.strip().replace('\n', ' ')[:20]
        chat.title = new_title if new_title else '新对话'
        chat.save()
    # 保存用户消息
    Message.objects.create(chat=chat, content=user_message, sender='user')
    # AI回复
    ai_reply = call_deepseek_ai(user_message=user_message)
    Message.objects.create(chat=chat, content=ai_reply, sender='bot')
    # 更新对话更新时间
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
    return render(request, 'overview_management.html')

def users_management(request):
    return render(request, 'users_management.html')

def faq_management(request):
    return render(request, 'faq_management.html')

# Create your views here.
