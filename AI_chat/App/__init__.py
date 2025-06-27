from flask import Flask
from .models import mysql
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
mysql.init_app(app)

from . import routes