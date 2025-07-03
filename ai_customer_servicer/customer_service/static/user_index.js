// 下拉菜单功能
function toggleDropdown() {
    const dropdown = document.getElementById('customerService');
    dropdown.classList.toggle('open');
}

// 关闭下拉菜单（点击其他地方时）
document.addEventListener('click', function(event) {
    const dropdown = document.getElementById('customerService');
    if (dropdown && !dropdown.contains(event.target)) {
        dropdown.classList.remove('open');
    }
});

// 标签页切换
function switchTab(tabName) {
    // 移除所有活动状态
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
    
    // 添加活动状态
    event.target.classList.add('active');
    document.getElementById(tabName + '-tab').classList.add('active');
}

// 导航功能
function navigate(page) {
    // 移除所有活动状态
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    
    // 添加当前页面活动状态
    event.target.classList.add('active');
    
    // 这里可以添加页面跳转逻辑
    console.log('导航到:', page);
    
    // 模拟页面跳转效果
    showNotification(`正在跳转到 ${getPageName(page)}...`);
}

function getPageName(page) {
    const pageNames = {
        'home': '首页',
        'ai-service': '人工智能客服',
        'messages': '消息中心',
        'profile': '用户中心'
    };
    return pageNames[page] || page;
}

// 显示头像预览模态框
function showAvatarModal() {
    const modal = document.getElementById('avatarModal');
    modal.classList.add('show');
    document.body.style.overflow = 'hidden'; // 禁止背景滚动
    
    // 添加ESC键关闭功能
    document.addEventListener('keydown', handleEscapeKey);
    
    // 添加触摸支持（移动端）
    addTouchSupport();
}

// 关闭头像预览模态框
function closeAvatarModal(event) {
    // 如果点击的是模态框内容区域（不是背景），则不关闭
    if (event && event.target.closest('.avatar-modal-content') && event.target !== document.querySelector('.avatar-close')) {
        return;
    }
    
    const modal = document.getElementById('avatarModal');
    modal.classList.add('closing');
    
    setTimeout(() => {
        modal.classList.remove('show', 'closing');
        document.body.style.overflow = ''; // 恢复背景滚动
        document.removeEventListener('keydown', handleEscapeKey);
        removeTouchSupport();
    }, 300);
}

// 处理ESC键关闭
function handleEscapeKey(event) {
    if (event.key === 'Escape') {
        closeAvatarModal();
    }
}

// 添加触摸支持
function addTouchSupport() {
    const modal = document.getElementById('avatarModal');
    let startY = 0;
    let currentY = 0;
    let isDragging = false;

    function handleTouchStart(e) {
        startY = e.touches[0].clientY;
        isDragging = true;
    }

    function handleTouchMove(e) {
        if (!isDragging) return;
        
        currentY = e.touches[0].clientY;
        const diffY = currentY - startY;
        
        // 向下滑动超过100px时关闭
        if (diffY > 100) {
            closeAvatarModal();
        }
        
        // 添加视觉反馈
        const content = modal.querySelector('.avatar-modal-content');
        if (diffY > 0) {
            content.style.transform = `translateY(${diffY}px) scale(${1 - diffY / 1000})`;
            content.style.opacity = 1 - diffY / 300;
        }
    }

    function handleTouchEnd() {
        isDragging = false;
        const content = modal.querySelector('.avatar-modal-content');
        content.style.transform = '';
        content.style.opacity = '';
    }

    modal.addEventListener('touchstart', handleTouchStart, { passive: true });
    modal.addEventListener('touchmove', handleTouchMove, { passive: true });
    modal.addEventListener('touchend', handleTouchEnd, { passive: true });
    
    // 保存引用以便后续移除
    modal._touchHandlers = { handleTouchStart, handleTouchMove, handleTouchEnd };
}

// 移除触摸支持
function removeTouchSupport() {
    const modal = document.getElementById('avatarModal');
    if (modal._touchHandlers) {
        modal.removeEventListener('touchstart', modal._touchHandlers.handleTouchStart);
        modal.removeEventListener('touchmove', modal._touchHandlers.handleTouchMove);
        modal.removeEventListener('touchend', modal._touchHandlers.handleTouchEnd);
        delete modal._touchHandlers;
    }
}

// 更换头像
function changeAvatar() {
    document.getElementById('avatarUploadModal').style.display = 'flex';
}

function closeAvatarUploadModal() {
    document.getElementById('avatarUploadModal').style.display = 'none';
    document.getElementById('avatarPreview').innerHTML = '';
    document.getElementById('avatarUploadInput').value = '';
}

function previewAvatar(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('avatarPreview').innerHTML = `<img src="${e.target.result}" style="width:120px;height:120px;border-radius:50%;">`;
        };
        reader.readAsDataURL(file);
    }
}

function submitAvatar() {
    const file = document.getElementById('avatarUploadInput').files[0];
    if (!file) {
        showNotification('请先选择图片', 'error');
        return;
    }
    const formData = new FormData();
    formData.append('avatar', file);
    fetch('/api/user/avatar/', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': window.CSRF_TOKEN
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showNotification('头像修改成功！');
            closeAvatarUploadModal();
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification('头像修改失败: ' + (data.message || ''), 'error');
        }
    })
    .catch(() => showNotification('请求失败', 'error'));
}

// 确认注销
function confirmLogout() {
    if (confirm('确定要注销登录吗？')) {
        showNotification('正在注销登录...');
        setTimeout(() => {
            showNotification('注销成功，正在跳转到登录页面...');
        }, 1000);
    }
}

// 退出登录
function logout() {
    confirmLogout();
}

// 保存基本信息
function saveBasicInfo(event) {
    event.preventDefault();
    const formData = new FormData();
    formData.append('nickname', document.getElementById('nickname').value);
    formData.append('mobile', document.getElementById('mobile').value);
    formData.append('email', document.getElementById('email').value);
    fetch('/api/user/profile/', {
        method: 'POST',
        body: formData,
        credentials: 'same-origin',
        headers: {
            'X-CSRFToken': window.CSRF_TOKEN
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showNotification('信息修改成功！');
            // 可选：刷新页面或重新拉取用户信息
        } else {
            showNotification('修改失败: ' + (data.message || ''), 'error');
        }
    })
    .catch(err => {
        showNotification('请求失败', 'error');
    });
}

// 保存安全信息
function saveSecurityInfo(event) {
    event.preventDefault();
    
    const originalPassword = event.target.querySelector('input[placeholder="请输入原密码"]').value;
    const newPassword = event.target.querySelector('input[placeholder="请输入新密码"]').value;
    const email = event.target.querySelector('input[placeholder="请输入绑定邮箱"]').value;
    const verificationCode = event.target.querySelector('input[placeholder="请输入收到的验证码"]').value;
    
    if (!originalPassword || !newPassword || !email || !verificationCode) {
        showNotification('请填写所有必填项！', 'error');
        return;
    }
    
    showNotification('密码修改成功！');
}

// 发送验证码
function sendVerificationCode() {
    const email = document.querySelector('#security-tab input[placeholder="请输入绑定邮箱"]').value;
    
    if (!email) {
        showNotification('请先输入邮箱地址！', 'error');
        return;
    }
    
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = '发送中...';
    
    // 模拟发送验证码
    setTimeout(() => {
        btn.textContent = '已发送';
        showNotification('验证码已发送到您的邮箱！');
        
        // 60秒倒计时
        let countdown = 60;
        const timer = setInterval(() => {
            countdown--;
            btn.textContent = `${countdown}s后重发`;
            
            if (countdown <= 0) {
                clearInterval(timer);
                btn.disabled = false;
                btn.textContent = '获取验证码';
            }
        }, 1000);
    }, 1000);
}

// 通知功能
function showNotification(message, type = 'success') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'error' ? '#ff4757' : '#2ed573'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        z-index: 10000;
        font-size: 14px;
        font-weight: 500;
        transform: translateX(100%);
        transition: transform 0.3s ease;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // 显示动画
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // 3秒后自动隐藏
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    // 添加加载动画
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.5s ease';
        document.body.style.opacity = '1';
    }, 100);
    
    // 动态填充用户信息
    fetch('/api/user/profile/', {
        method: 'GET',
        credentials: 'same-origin',
        headers: {
            'Accept': 'application/json'
        }
    })
    .then(res => res.json())
    .then(data => {
        try {
            console.log('API返回数据:', data);
            // 头像
            const avatar = (data.profile && data.profile.avatar) ? data.profile.avatar : '';
            document.querySelectorAll('.profile-avatar, .avatar-large').forEach(el => {
                if (avatar) {
                    el.innerHTML = `<img src="${avatar}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
                } else {
                    el.innerHTML = '👤';
                }
            });
            // 用户名
            document.querySelectorAll('.username').forEach(el => el.textContent = data.username || '');
            // 欢迎语
            document.querySelectorAll('.welcome-text').forEach(el => el.textContent = '欢迎您：');
            // ID
            const idInput = document.getElementById('user_id');
            if (idInput) idInput.value = data.id || '';
            // 邮箱
            const emailInput = document.getElementById('email');
            if (emailInput) emailInput.value = data.email || '';
            // 手机号
            const mobileInput = document.getElementById('mobile');
            if (mobileInput) mobileInput.value = (data.profile && data.profile.mobile) ? data.profile.mobile : '';
            // 昵称
            const nicknameInput = document.getElementById('nickname');
            if (nicknameInput) nicknameInput.value = (data.profile && data.profile.nickname) ? data.profile.nickname : (data.username || '');
            // 邮箱展示
            const userEmail = document.querySelector('.user-email');
            if (userEmail) userEmail.textContent = data.email || '';
            // 头像大图信息
            const avatarH3 = document.querySelector('.avatar-info h3');
            if (avatarH3) avatarH3.textContent = (data.profile && data.profile.nickname) ? data.profile.nickname : (data.username || '');
            const avatarP = document.querySelector('.avatar-info p');
            if (avatarP) avatarP.textContent = 'ID: ' + (data.id || '');
        } catch (e) {
            console.error('赋值出错:', e);
            showNotification('用户信息赋值出错: ' + e, 'error');
        }
    })
    .catch(err => {
        showNotification('用户信息加载失败', 'error');
        console.error('加载失败:', err);
    });
    
    console.log('联析智服用户管理系统已加载完成');
});

// 表单验证增强
document.querySelectorAll('.form-control').forEach(input => {
    input.addEventListener('focus', function() {
        this.style.transform = 'scale(1.02)';
    });
    
    input.addEventListener('blur', function() {
        this.style.transform = 'scale(1)';
    });
});

function togglePasswordVisibility() {
    const pwdInput = document.getElementById('newPasswordInput');
    const eyeIcon = document.getElementById('eyeIcon');
    if (!pwdInput || !eyeIcon) return;
    if (pwdInput.type === 'password') {
        pwdInput.type = 'text';
        // 显示眼睛（不带斜线）
        eyeIcon.innerHTML = '<path d="M1 12C2.73 16.11 7 20 12 20c5 0 9.27-3.89 11-8-1.73-4.11-6-8-11-8-5 0-9.27 3.89-11 8z"/><circle cx="12" cy="12" r="3"/>';
    } else {
        pwdInput.type = 'password';
        // 显示灰色眼睛带斜线
        eyeIcon.innerHTML = '<path d="M17.94 17.94A10.06 10.06 0 0 1 12 20C7 20 2.73 16.11 1 12c.73-1.64 1.81-3.16 3.06-4.41"/><path d="M22.54 12.88A10.06 10.06 0 0 0 12 4c-1.61 0-3.16.38-4.54 1.06"/><line x1="1" y1="1" x2="23" y2="23"/><path d="M9.53 9.53A3.5 3.5 0 0 0 12 15.5c1.38 0 2.63-.83 3.16-2.03"/>';
    }
}
