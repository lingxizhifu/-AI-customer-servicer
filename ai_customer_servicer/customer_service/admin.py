from django.contrib import admin


from django.contrib import admin
from .models import Conversation, Message, FAQ, Chat, Profile

admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(FAQ)
admin.site.register(Chat)
admin.site.register(Profile)
# Register your models here.
