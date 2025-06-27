from App import app
from App.models import init_db

if __name__ == '__main__':
    # 确保在应用启动前初始化数据库
    with app.app_context():
        init_db(app)
    app.run(debug=True)