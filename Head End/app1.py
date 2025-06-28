import http.server
import socketserver
import os
import webbrowser
from threading import Timer

def open_browser():
    """3秒后自动打开浏览器"""
    webbrowser.open('http://localhost:8000')

def start_server():
    """启动HTTP服务器"""
    PORT = 8000
    
    # 检查Head End目录是否有index.html文件
    html_path = os.path.join('Head End', 'index.html')
    if not os.path.exists(html_path):
        print("错误: 找不到 index.html 文件!")
        print(f"请确保将生成的HTML代码保存为 '{html_path}' 文件")
        return
    
    # 切换到Head End目录
    os.chdir('Head End')
    
    # 创建static文件夹（如果不存在）
    if not os.path.exists('static'):
        os.makedirs('static')
        print("已创建 'static' 文件夹，请将您的AI图标放在此文件夹中")
    
    Handler = http.server.SimpleHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"服务器已启动!")
        print(f"访问地址: http://localhost:{PORT}")
        print(f"请将AI图标图片放在 'static' 文件夹中")
        print(f"然后在HTML中使用路径: ./static/your-ai-icon.png")
        print("按 Ctrl+C 停止服务器")
        
        # 3秒后自动打开浏览器
        Timer(3.0, open_browser).start()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")

if __name__ == "__main__":
    start_server()