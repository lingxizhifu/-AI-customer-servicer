from flask import Flask, render_template
import os

app = Flask(__name__)

# 配置静态文件夹
app.static_folder = 'images'
app.static_url_path = '/images'

@app.route('/')
def dashboard():
    """首页 - 系统概览模块"""
    return render_template('overview.html')

@app.route('/faq')
def faq_management():
    """FAQ知识库管理模块"""
    return render_template('faq.html')

@app.route('/users')
def user_management():
    """用户权限管理模块"""
    return render_template('users.html')

def setup_directories():
    """创建必要的文件夹结构"""
    directories = ['templates', 'images']
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"已创建 '{directory}' 文件夹")

if __name__ == '__main__':
    print("=" * 50)
    print("聆析智服管理系统")
    print("=" * 50)
    
    # 设置目录结构
    setup_directories()
    
    print("\n📁 项目文件夹结构:")
    print("├── app.py (Flask服务器)")
    print("├── templates/")
    print("│   ├── overview.html (数据中心页面)")
    print("│   ├── faq.html (FAQ管理页面)")
    print("│   └── users.html (用户管理页面)")
    print("└── images/")
    print("    ├── usage-icon.png (可选的统计图标)")
    print("    ├── chat-icon.png")
    print("    ├── solve-icon.png")
    print("    └── complaint-icon.png")
    
    print("\n🔗 系统路由:")
    print("📊 数据中心: http://localhost:5001/")
    print("📦 FAQ管理: http://localhost:5001/faq")
    print("👤 用户管理: http://localhost:5001/users")
    
    print("\n💡 使用说明:")
    print("1. 将 overview.html, faq.html, users.html 放入 templates 文件夹")
    print("2. 将图标文件放入 images 文件夹 (可选)")
    print("3. 运行此Python文件启动服务器")
    print("4. 通过浏览器访问上述路由地址")
    
    print(f"\n🚀 服务器启动中...")
    print(f"📍 访问地址: http://localhost:5001")
    print("按 Ctrl+C 停止服务器\n")
    
    # 启动Flask应用
    app.run(debug=True, host='0.0.0.0', port=5001)