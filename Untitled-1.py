import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# 解决平台插件问题
def fix_qt_plugin_path():
    if sys.platform == 'win32':
        # Windows 平台
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(
            os.path.dirname(sys.executable), 'Lib', 'site-packages', 'PyQt5', 'Qt', 'plugins'
        )
    elif sys.platform == 'darwin':
        # macOS 平台
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(
            os.path.dirname(sys.executable), '..', 'Resources', 'qt', 'plugins'
        )
    else:
        # Linux 平台
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(
            os.path.dirname(sys.executable), 'lib', 'qt', 'plugins'
        )

# 尝试修复插件路径问题
try:
    fix_qt_plugin_path()
except Exception as e:
    print(f"自动修复插件路径失败: {e}")

class ProfileWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("个人信息管理")
        self.setGeometry(100, 100, 900, 650)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f7fa;
                font-family: 'Microsoft YaHei', sans-serif;
            }
            QLabel {
                color: #333;
            }
            QPushButton {
                background-color: #4a6cf7;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3a5ce0;
            }
            QLineEdit, QComboBox {
                border: 1px solid #dcdfe6;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            QGroupBox {
                border: 1px solid #ebeef5;
                border-radius: 8px;
                margin-top: 20px;
                background-color: white;
                padding: 20px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                left: 10px;
                color: #4a6cf7;
                font-weight: bold;
            }
            QListWidget {
                border: none;
                background-color: transparent;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 12px 20px;
                border-bottom: 1px solid #ebeef5;
            }
            QListWidget::item:selected {
                background-color: #eef2ff;
                color: #4a6cf7;
                border-left: 3px solid #4a6cf7;
            }
        """)
        
        self.init_ui()
        
    def init_ui(self):
        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 左侧导航栏
        left_nav = QGroupBox("个人中心")
        left_nav_layout = QVBoxLayout(left_nav)
        left_nav_layout.setContentsMargins(0, 30, 0, 20)
        
        # 导航列表
        nav_list = QListWidget()
        nav_list.addItems(["基本信息", "账户安全", "通知设置", "隐私设置", "系统设置"])
        nav_list.setCurrentRow(0)
        nav_list.setFixedWidth(180)
        nav_list.setStyleSheet("""
            QListWidget::item {
                border-bottom: 1px solid #ebeef5;
            }
            QListWidget::item:last {
                border-bottom: none;
            }
        """)
        
        # 客服中心下拉菜单
        support_label = QLabel("客服中心")
        support_label.setStyleSheet("font-weight: bold; padding: 15px 20px 5px 20px;")
        
        support_combo = QComboBox()
        support_combo.addItems(["人工智能客服", "在线客服", "电话客服", "邮件支持"])
        support_combo.setCurrentIndex(0)
        support_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 15px;
                margin: 0 15px 15px 15px;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox:hover {
                background-color: #f5f7ff;
            }
        """)
        
        left_nav_layout.addWidget(nav_list)
        left_nav_layout.addWidget(support_label)
        left_nav_layout.addWidget(support_combo)
        left_nav_layout.addStretch()
        
        # 右侧内容区域
        right_content = QFrame()
        right_content.setStyleSheet("background-color: white; border-radius: 8px;")
        right_layout = QVBoxLayout(right_content)
        right_layout.setContentsMargins(30, 30, 30, 30)
        right_layout.setSpacing(20)
        
        # 顶部欢迎信息
        header_layout = QHBoxLayout()
        welcome_label = QLabel(f"<h2>欢迎您：<span style='color:#4a6cf7;'>USERNAME</span></h2>")
        
        # 头像区域
        avatar_layout = QVBoxLayout()
        avatar_layout.setAlignment(Qt.AlignCenter)
        avatar_layout.setSpacing(10)
        
        # 头像占位
        avatar = QLabel()
        avatar.setFixedSize(80, 80)
        avatar.setStyleSheet("""
            background-color: #eef2ff;
            border-radius: 40px;
            border: 2px solid #4a6cf7;
        """)
        
        # 头像图标（使用默认图标）
        avatar_icon = QLabel()
        avatar_icon.setAlignment(Qt.AlignCenter)
        avatar_icon.setFixedSize(40, 40)
        avatar_icon.setStyleSheet("background-color: #4a6cf7; border-radius: 20px;")
        
        # 头像文本
        avatar_text = QLabel("更换头像")
        avatar_text.setStyleSheet("color: #4a6cf7; font-weight: bold;")
        
        avatar_layout.addWidget(avatar)
        avatar_layout.addWidget(avatar_icon)
        avatar_layout.addWidget(avatar_text)
        
        # 注销按钮
        logout_btn = QPushButton("注销登录")
        logout_btn.setFixedWidth(100)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.logout)
        
        header_layout.addWidget(welcome_label)
        header_layout.addStretch()
        header_layout.addLayout(avatar_layout)
        header_layout.addWidget(logout_btn)
        
        # 基本信息表单
        form_group = QGroupBox("基本信息")
        form_layout = QFormLayout()
        form_layout.setHorizontalSpacing(40)
        form_layout.setVerticalSpacing(20)
        
        # ID
        id_label = QLabel("ID")
        id_value = QLabel("110910")
        id_value.setStyleSheet("font-weight: bold;")
        
        # 邮箱
        email_label = QLabel("邮箱")
        email_edit = QLineEdit("user@example.com")
        email_edit.setPlaceholderText("请输入邮箱")
        bind_btn = QPushButton("绑定")
        bind_btn.setFixedWidth(80)
        bind_btn.setCursor(Qt.PointingHandCursor)
        bind_btn.clicked.connect(self.bind_email)
        
        email_layout = QHBoxLayout()
        email_layout.addWidget(email_edit)
        email_layout.addWidget(bind_btn)
        
        # 手机号
        phone_label = QLabel("手机号")
        phone_value = QLabel("18772569895")
        phone_value.setStyleSheet("font-weight: bold;")
        
        # 昵称
        nickname_label = QLabel("昵称")
        nickname_edit = QLineEdit("USERNAME")
        
        # 用户名
        username_label = QLabel("用户名")
        username_value = QLabel("www.baogaoba.xyz")
        username_value.setStyleSheet("font-weight: bold;")
        
        # 添加到表单
        form_layout.addRow(id_label, id_value)
        form_layout.addRow(email_label, email_layout)
        form_layout.addRow(phone_label, phone_value)
        form_layout.addRow(nickname_label, nickname_edit)
        form_layout.addRow(username_label, username_value)
        form_group.setLayout(form_layout)
        
        # 保存按钮
        save_btn = QPushButton("保存信息")
        save_btn.setFixedHeight(45)
        save_btn.setStyleSheet("font-size: 16px;")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self.save_info)
        
        # 添加动画效果
        self.save_btn_animation = QPropertyAnimation(save_btn, b"geometry")
        self.save_btn_animation.setDuration(200)
        
        # 添加到右侧布局
        right_layout.addLayout(header_layout)
        right_layout.addWidget(form_group)
        right_layout.addStretch()
        right_layout.addWidget(save_btn)
        
        # 添加到主布局
        main_layout.addWidget(left_nav)
        main_layout.addWidget(right_content, 1)
        
        # 添加悬停动画
        self.add_hover_effects([bind_btn, logout_btn, save_btn])
    
    def add_hover_effects(self, buttons):
        for btn in buttons:
            # 鼠标进入事件
            btn.enterEvent = lambda event, b=btn: self.animate_button(b, True)
            # 鼠标离开事件
            btn.leaveEvent = lambda event, b=btn: self.animate_button(b, False)
    
    def animate_button(self, button, hover):
        animation = QPropertyAnimation(button, b"geometry")
        animation.setDuration(200)
        original_rect = button.geometry()
        
        if hover:
            animation.setStartValue(original_rect)
            animation.setEndValue(original_rect.adjusted(-2, -2, 2, 2))
        else:
            animation.setStartValue(original_rect)
            animation.setEndValue(original_rect.adjusted(2, 2, -2, -2))
        
        animation.start()
    
    def bind_email(self):
        QMessageBox.information(self, "邮箱绑定", "邮箱绑定功能已触发！")
    
    def save_info(self):
        # 添加保存按钮动画
        original_rect = self.sender().geometry()
        self.save_btn_animation.setStartValue(QRect(original_rect.x(), original_rect.y(), 
                                                  original_rect.width(), original_rect.height()))
        self.save_btn_animation.setEndValue(QRect(original_rect.x(), original_rect.y() + 5, 
                                                original_rect.width(), original_rect.height()))
        self.save_btn_animation.setDirection(QPropertyAnimation.Backward)
        self.save_btn_animation.start()
        
        QMessageBox.information(self, "保存信息", "个人信息已成功保存！")
    
    def logout(self):
        reply = QMessageBox.question(self, "注销登录", "确定要注销当前账号吗？",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            QMessageBox.information(self, "注销成功", "您已成功注销账号！")
            self.close()

if __name__ == "__main__":
    # 创建应用实例
    app = QApplication(sys.argv)
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    # 创建主窗口
    window = ProfileWindow()
    window.show()
    
    # 执行应用
    sys.exit(app.exec_())