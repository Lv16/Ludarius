from django.conf import settings
from django.db import models

class Favorite(models.Model):
    MEDIA_TYPES = (
        ("movie", "Movie"),
        ("tv", "TV"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    tmdb_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "media_type", "tmdb_id")
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["media_type", "tmdb_id"]),
        ]

    def __str__(self):
        return f"{self.user} favorited {self.media_type}:{self.tmdb_id}"
