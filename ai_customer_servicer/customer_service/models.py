from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """用户保存时同时保存Profile"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        Profile.objects.create(user=instance)

class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or f"对话 {self.id}"

class Chat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, default='新对话')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    sender = models.CharField(max_length=20)  # 'user' 或 'bot'
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.sender}: {self.content[:30]}"

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=50, default='常见问题')
    is_main = models.BooleanField(default=True)  # True表示启用，False表示禁用
    created_at = models.DateTimeField(auto_now_add=True)  # 新增字段
    updated_at = models.DateTimeField(auto_now=True)      # 新增字段

    def __str__(self):
        return self.question

    class Meta:
        ordering = ['-created_at']  # 按创建时间倒序排列

def avatar_upload_path(instance, filename):
    # 存到 media/avatars/目录下
    return f'avatars/{instance.user.id}_{filename}'

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    nickname = models.CharField(max_length=50, blank=True, null=True, verbose_name='昵称')
    mobile = models.CharField(max_length=20, blank=True, null=True, verbose_name='手机号')
    avatar = models.ImageField(upload_to=avatar_upload_path, blank=True, null=True, verbose_name='头像')

    def __str__(self):
        return self.nickname or self.user.username