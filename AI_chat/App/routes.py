from flask import render_template, request, jsonify, redirect, url_for, session
from . import app
from .models import User
import random

@app.route('/', methods=['GET'])
@app.route('/login', methods=['GET'])
def login_page():
    # 生成新验证码
    session['captcha'] = generate_captcha_code()
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    # 验证验证码
    if 'captcha' not in data or data['captcha'].lower() != session.get('captcha', '').lower():
        return jsonify(success=False, message='验证码错误')
    
    user = User.get_by_username(data['username'])
    if user and User.check_password(user, data['password']):
        # 登录成功
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify(success=True, message='登录成功！即将跳转到主页面...')
    else:
        return jsonify(success=False, message='用户名或密码错误')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    # 验证验证码
    if 'captcha' not in data or data['captcha'].lower() != session.get('captcha', '').lower():
        return jsonify(success=False, message='验证码错误')
    
    # 检查用户名是否已存在
    if User.get_by_username(data['username']):
        return jsonify(success=False, message='用户名已存在')
    
    # 检查密码是否一致
    if data.get('password') != data.get('confirm_password'):
        return jsonify(success=False, message='两次密码输入不一致')
    
    # 创建用户
    try:
        User.create(data['username'], data['password'])
        return jsonify(success=True, message='注册成功！请使用新账号登录。')
    except Exception as e:
        print(f"注册失败: {str(e)}")
        return jsonify(success=False, message='注册失败，请稍后再试')

@app.route('/captcha')
def generate_captcha():
    # 生成随机验证码
    chars = 'ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789'
    captcha = ''.join(random.choice(chars) for _ in range(4))
    session['captcha'] = captcha
    return jsonify(captcha=captcha)

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    if email:
        # 这里应发送重置密码邮件，实际项目中需要实现
        return jsonify(success=True, message='密码重置链接已发送到您的邮箱')
    return jsonify(success=False, message='请输入有效的邮箱地址')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

def generate_captcha_code():
    """生成随机验证码"""
    chars = 'ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789'
    return ''.join(random.choice(chars) for _ in range(4))