from django.contrib import admin
from .models import Comment

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("user", "media_type", "tmdb_id", "created_at")
    list_filter = ("media_type",)
    search_fields = ("user__username", "text")
