from django.conf import settings
from django.db import models

class Rating(models.Model):
    MEDIA_TYPES = (
        ("movie", "Movie"),
        ("tv", "TV"),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPES)
    tmdb_id = models.IntegerField()
    score = models.PositiveSmallIntegerField()  # 1..10
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "media_type", "tmdb_id")
        indexes = [
            models.Index(fields=["media_type", "tmdb_id"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user} rated {self.media_type}:{self.tmdb_id} = {self.score}"
