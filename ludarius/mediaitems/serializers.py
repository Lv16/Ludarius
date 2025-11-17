from rest_framework import serializers
from .models import MediaItem


class MediaItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaItem
        fields = ['id', 'external_id', 'title', 'media_type', 'description', 'poster_url', 'created_at']
