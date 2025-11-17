from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'media', 'status', 'created_at')
    search_fields = ('user__username', 'media__title')
