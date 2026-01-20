# movies/admin.py
from django.contrib import admin
from .models import Movie, StreamingPlatform, MovieAvailability


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'release_date', 'rating')
    search_fields = ('title', 'original_title')


@admin.register(StreamingPlatform)
class StreamingPlatformAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(MovieAvailability)
class MovieAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('movie', 'platform', 'access_type', 'price')
    list_filter = ('access_type', 'platform')
