// 获取csrftoken
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');

class AuthPage {
    constructor() {
        this.loginForm = document.getElementById('loginForm');
        this.registerForm = document.getElementById('registerForm');
        this.loginSuccessMessage = document.getElementById('loginSuccessMessage');
        this.captchaCodes = [];
        this.init();
    }

    init() {
        // 表单切换
        document.getElementById('showRegister').addEventListener('click', (e) => {
            e.preventDefault();
            this.showRegisterForm();
        });
        document.getElementById('showLogin').addEventListener('click', (e) => {
            e.preventDefault();
            this.showLoginForm();
        });
        const headerLoginBtn = document.getElementById('headerLoginBtn');
        if (headerLoginBtn) {
            headerLoginBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.showLoginForm();
            });
        }

        // 验证码点击刷新
        document.getElementById('captchaImage').addEventListener('click', () => {
            this.refreshCaptcha('captchaImage');
        });
        document.getElementById('captchaImageRegister').addEventListener('click', () => {
            this.refreshCaptcha('captchaImageRegister');
        });

        // 表单提交
        this.loginForm.querySelector('form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin(e);
        });
        this.registerForm.querySelector('form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleRegister(e);
        });

        // 忘记密码
        document.getElementById('forgotPassword').addEventListener('click', (e) => {
            e.preventDefault();
            this.handleForgotPassword();
        });

        // 输入框焦点效果
        document.querySelectorAll('.form-input').forEach(input => {
            input.addEventListener('focus', (e) => {
                e.target.parentElement.classList.add('focused');
            });
            input.addEventListener('blur', (e) => {
                e.target.parentElement.classList.remove('focused');
            });
        });

        // 初始刷新验证码
        this.refreshCaptcha('captchaImage');
        this.refreshCaptcha('captchaImageRegister');
    }

    refreshCaptcha(elementId) {
        fetch('/captcha/')
            .then(response => response.json())
            .then(data => {
                const captchaElement = document.getElementById(elementId);
                captchaElement.textContent = data.captcha;
                captchaElement.style.transform = 'scale(0.8)';
                setTimeout(() => {
                    captchaElement.style.transform = 'scale(1)';
                }, 150);
            })
            .catch(error => {
                // 本地备用验证码逻辑
                const chars = 'ABCDEFGHJKMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789';
                let result = '';
                for (let i = 0; i < 4; i++) {
                    result += chars.charAt(Math.floor(Math.random() * chars.length));
                }
                const captchaElement = document.getElementById(elementId);
                captchaElement.textContent = result;
            });
    }

    clearAllErrorsAndInputs(form) {
        form.querySelectorAll('.error-message').forEach(error => {
            error.classList.remove('show');
        });
        form.querySelectorAll('.form-input').forEach(input => {
            input.value = '';
        });
        if (this.loginSuccessMessage) this.loginSuccessMessage.classList.remove('show');
    }

    showLoginForm() {
        this.loginForm.classList.remove('hidden');
        this.registerForm.classList.add('hidden');
        this.clearAllErrorsAndInputs(this.loginForm);
        this.refreshCaptcha('captchaImage');
    }

    showRegisterForm() {
        this.registerForm.classList.remove('hidden');
        this.loginForm.classList.add('hidden');
        this.clearAllErrorsAndInputs(this.registerForm);
        this.refreshCaptcha('captchaImageRegister');
    }

    handleLogin(e) {
        const form = e.target;
        const isValid = this.validateForm(form);
        if (isValid) {
            const submitBtn = form.querySelector('.submit-btn');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span>⏳</span> 登录中...';
            submitBtn.disabled = true;
            // 收集表单数据
            const formData = {
                username: form.querySelector('input[type="text"]').value,
                password: form.querySelector('input[type="password"]').value,
                captcha: form.querySelector('.captcha-input').value
            };
            fetch('/login/submit/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showSuccessMessage(data.message || '登录成功！');
                    setTimeout(() => {
                        if (data.is_superuser) {
                            window.location.href = '/overview_management/';
                        } else {
                            window.location.href = '/chat/';
                        }
                    }, 1500);
                } else {
                    if (data.errors) {
                        Object.keys(data.errors).forEach(field => {
                            const errorElement = form.querySelector(`[data-field="${field}"] .error-message`);
                            if (errorElement) {
                                this.showError(errorElement, data.errors[field][0]);
                            }
                        });
                    } else {
                        this.showError(
                            form.querySelector('.error-message:last-child'),
                            data.message || '登录失败，请检查输入'
                        );
                    }
                    this.refreshCaptcha('captchaImage');
                }
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            })
            .catch(error => {
                console.error('登录请求失败:', error);
                this.showError(
                    form.querySelector('.error-message:last-child'),
                    '网络错误，请重试'
                );
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            });
        }
    }

    handleRegister(e) {
        const form = e.target;
        const isValid = this.validateForm(form);
        if (isValid) {
            const submitBtn = form.querySelector('.submit-btn');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span>⏳</span> 注册中...';
            submitBtn.disabled = true;
            // 收集表单数据
            const formData = {
                username: form.querySelector('input[type="text"]').value,
                password: form.querySelector('input[type="password"]').value,
                confirm_password: form.querySelectorAll('input[type="password"]')[1].value,
                captcha: form.querySelector('.captcha-input').value
            };
            fetch('/register/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showSuccessMessage(data.message || '注册成功！');
                    setTimeout(() => {
                        this.showLoginForm();
                    }, 1500);
                } else {
                    if (data.errors) {
                        Object.keys(data.errors).forEach(field => {
                            const errorElement = form.querySelector(`[data-field="${field}"] .error-message`);
                            if (errorElement) {
                                this.showError(errorElement, data.errors[field][0]);
                            }
                        });
                    } else {
                        this.showError(
                            form.querySelector('.error-message:last-child'),
                            data.message || '注册失败，请检查输入'
                        );
                    }
                    this.refreshCaptcha('captchaImageRegister');
                }
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            })
            .catch(error => {
                console.error('注册请求失败:', error);
                this.showError(
                    form.querySelector('.error-message:last-child'),
                    '网络错误，请重试'
                );
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            });
        }
    }

    handleForgotPassword() {
        const email = prompt('请输入您的邮箱地址：');
        if (email) {
            fetch('/forgot-password/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify({ email })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(`密码重置链接已发送到 ${email}，请查收邮件。`);
                } else {
                    alert(data.message || '密码重置请求失败');
                }
            })
            .catch(error => {
                console.error('密码重置请求失败:', error);
                alert('网络错误，请重试');
            });
        }
    }

    validateForm(form) {
        const inputs = form.querySelectorAll('.form-input');
        let isValid = true;
        inputs.forEach(input => {
            const errorElement = input.parentElement.querySelector('.error-message');
            if (!input.value.trim()) {
                this.showError(errorElement, '此字段不能为空');
                isValid = false;
            } else {
                this.hideError(errorElement);
            }
        });
        return isValid;
    }

    showError(errorElement, message) {
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.classList.add('show');
        }
    }

    hideError(errorElement) {
        if (errorElement) {
            errorElement.classList.remove('show');
        }
    }

    showSuccessMessage(message) {
        this.loginSuccessMessage.textContent = message;
        this.loginSuccessMessage.classList.add('show');
        setTimeout(() => {
            this.loginSuccessMessage.classList.remove('show');
        }, 5000);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const authPage = new AuthPage();
});
