# 后端管理界面以及ai回答后的问题推送我都没有实现



# ai_customer_servicer 项目说明

## 项目简介
本项目基于 Django，整合了 gpt_chatbot1 聊天机器人全部功能，支持多轮对话、AI 智能回复、FAQ 动态加载、历史消息管理等，适用于客服、问答等场景。

## 主要功能
- 多轮对话与 AI 智能回复
- 聊天历史记录管理（搜索、删除、清空）
- FAQ 常见问题动态加载与美观展示
- FAQ 问题润色
- 前后端接口完全分离，RESTful 风格
- 支持 MySQL 数据库

## 本地运行完整流程（详细步骤）

### 1. 克隆项目代码
```bash
git clone <your_repo_url>
cd ai_customer_servicer
```

### 2. 创建并激活虚拟环境
- Windows:
  ```bash
  python -m venv venv
  venv\Scripts\activate
  ```
- macOS/Linux:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置 MySQL 数据库
1. **创建数据库**（用你的 MySQL 工具或命令行）：
   ```sql
   CREATE DATABASE your_db_name DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
2. **在 `ai_customer_servicer/settings.py` 或 `.env` 文件中配置数据库连接**：
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'your_db_name',
           'USER': 'your_db_user',
           'PASSWORD': 'your_db_password',
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
   ```

### 5. 生成并应用数据库迁移
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. 创建超级用户（可选，用于后台管理）
```bash
python manage.py createsuperuser
```
按提示输入用户名、邮箱、密码。

### 7. （可选）导入初始 FAQ 或其它数据
如有初始数据文件（如 `initial_data.json`）：
```bash
python manage.py loaddata initial_data.json
```

### 8. 启动开发服务器
```bash
python manage.py runserver
```
默认访问地址：http://127.0.0.1:8000/

### 9. 访问后台管理（可选）
http://127.0.0.1:8000/admin/
用第6步创建的超级用户登录。

## 常见问题与排查

- **MySQL 连接报错**：请检查数据库名、用户名、密码、端口是否正确，MySQL 服务是否已启动。
- **依赖安装失败**：请确认已激活虚拟环境，pip 版本为最新版，MySQL 已安装开发库（如 Windows 需安装 MySQL Connector/C）。
- **静态文件不显示**：开发环境下 Django 会自动处理，生产环境需执行 `python manage.py collectstatic`。

## 常用管理命令
- 启动开发服务器：`