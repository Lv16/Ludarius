from django.contrib import admin

from .models import AvailabilityAlert, Collection, CollectionItem, MediaStatus, Notification, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "bio")
    search_fields = ("user__username", "bio")


@admin.register(MediaStatus)
class MediaStatusAdmin(admin.ModelAdmin):
    list_display = ("user", "media_type", "tmdb_id", "status", "updated_at")
    list_filter = ("media_type", "status")
    search_fields = ("user__username", "tmdb_id")


class CollectionItemInline(admin.TabularInline):
    model = CollectionItem
    extra = 0


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "is_public", "created_at")
    list_filter = ("is_public",)
    search_fields = ("title", "user__username")
    inlines = [CollectionItemInline]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "actor", "verb", "media_type", "tmdb_id", "is_read", "created_at")
    list_filter = ("is_read", "media_type")
    search_fields = ("user__username", "actor__username", "verb")


@admin.register(AvailabilityAlert)
class AvailabilityAlertAdmin(admin.ModelAdmin):
    list_display = ("user", "media_type", "tmdb_id", "created_at")
    list_filter = ("media_type",)
    search_fields = ("user__username", "tmdb_id")
