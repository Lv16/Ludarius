from django.contrib import admin
from .models import SocialFollow


@admin.register(SocialFollow)
class SocialFollowAdmin(admin.ModelAdmin):
    list_display = ('follower', 'following', 'created_at')
