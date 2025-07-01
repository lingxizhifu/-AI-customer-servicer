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
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)