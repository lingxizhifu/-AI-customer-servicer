from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FAQViewSet, ai_polish_faq_answer
from .views import create_chat_and_history, send_message, chat_messages, search_chats, clear_chats, delete_chat
from .views import index
from .views import login_page, login_submit, register_submit, generate_captcha, forgot_password, logout_view
from .views import faq_groups
from .views import admin_index
from .views import user_profile
from .views import user_index
from .views import user_avatar_upload
from .views import overview_management
from .views import users_management
from .views import faq_management
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

# 用户管理相关导入
from .views import (
    get_users_list, create_user, update_user, delete_user, 
    get_user_detail, batch_delete_users, export_users, toggle_user_status,
    batch_enable_users, batch_disable_users
)

# FAQ管理相关导入
from .views import (
    get_faqs_list, create_faq, update_faq, delete_faq,
    get_faq_detail, batch_delete_faqs, export_faqs, 
    toggle_faq_status, get_faq_categories
)

#API视图导入
from .views import get_real_time_stats

router = DefaultRouter()
router.register(r'faqs', FAQViewSet)

urlpatterns = [
    path('', index, name='index'),
    path('chat/', index, name='index'),
    path('', include(router.urls)),
    path('admin_index/', admin_index, name='admin_index'),
    path('faqs/<int:pk>/polish/', ai_polish_faq_answer, name='ai_polish_faq_answer'),
    path('chats/', create_chat_and_history, name='create_chat_and_history'),  # 合并GET+POST
    path('chats/<uuid:chat_id>/send/', send_message, name='send_message'),
    path('chats/<uuid:chat_id>/messages/', chat_messages, name='chat_messages'),
    path('chats/search/', search_chats, name='search_chats'),
    path('chats/clear/', clear_chats, name='clear_chats'),
    path('chats/<uuid:chat_id>/', delete_chat, name='delete_chat'),
    path('login/', login_page, name='login_page'),
    path('login/submit/', login_submit, name='login_submit'),
    path('register/', register_submit, name='register_submit'),
    path('captcha/', generate_captcha, name='generate_captcha'),
    path('forgot-password/', forgot_password, name='forgot_password'),
    path('logout/', logout_view, name='logout'),
    path('api/chats/faq_groups/', faq_groups),
    path('api/user/profile/', user_profile, name='user_profile'),
    path('user_index/', user_index, name='user_index'),
    path('api/user/avatar/', user_avatar_upload, name='user_avatar_upload'),
    path('overview_management/', overview_management, name='overview_management'),
    path('users_management/', users_management, name='users_management'),
    path('faq_management/', faq_management, name='faq_management'),
        
    # 用户管理相关API
    path('api/users/', get_users_list, name='get_users_list'),
    path('api/users/create/', create_user, name='create_user'),
    path('api/users/<int:user_id>/', get_user_detail, name='get_user_detail'),
    path('api/users/<int:user_id>/update/', update_user, name='update_user'),
    path('api/users/<int:user_id>/delete/', delete_user, name='delete_user'),
    path('api/users/<int:user_id>/toggle-status/', toggle_user_status, name='toggle_user_status'),
    path('api/users/batch-delete/', batch_delete_users, name='batch_delete_users'),
    path('api/users/export/', export_users, name='export_users'),
    path('api/users/batch-enable/', batch_enable_users, name='batch_enable_users'),
    path('api/users/batch-disable/', batch_disable_users, name='batch_disable_users'),

    # FAQ管理相关API
    path('api/faqs/', get_faqs_list, name='get_faqs_list'),
    path('api/faqs/create/', create_faq, name='create_faq'),
    path('api/faqs/<int:faq_id>/', get_faq_detail, name='get_faq_detail'),
    path('api/faqs/<int:faq_id>/update/', update_faq, name='update_faq'),
    path('api/faqs/<int:faq_id>/delete/', delete_faq, name='delete_faq'),
    path('api/faqs/<int:faq_id>/toggle-status/', toggle_faq_status, name='toggle_faq_status'),
    path('api/faqs/batch-delete/', batch_delete_faqs, name='batch_delete_faqs'),
    path('api/faqs/export/', export_faqs, name='export_faqs'),
    path('api/faqs/categories/', get_faq_categories, name='get_faq_categories'),



    

    # 其他API
    path('api/overview/stats/', get_real_time_stats, name='get_real_time_stats'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else '')
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    if hasattr(settings, 'MEDIA_URL') and hasattr(settings, 'MEDIA_ROOT'):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)