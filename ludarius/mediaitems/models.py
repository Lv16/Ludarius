from django.db import models


class MediaItem(models.Model):
    MEDIA_TYPES = [( 'movie', 'Movie'), ('series', 'Series'), ('game', 'Game'), ('book', 'Book')]
    external_id = models.CharField(max_length=200, blank=True, null=True)
    title = models.CharField(max_length=300)
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES)
    description = models.TextField(blank=True)
    poster_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.media_type})"
