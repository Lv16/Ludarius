from django.contrib import admin
from .models import List, ListItem


@admin.register(List)
class ListAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_public', 'created_at')


@admin.register(ListItem)
class ListItemAdmin(admin.ModelAdmin):
    list_display = ('list', 'media', 'order')
