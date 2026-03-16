from django.conf import settings
from django.db import models


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    bio = models.CharField(max_length=280, blank=True)

    def __str__(self):
        return f"Profile<{self.user}>"


class MediaStatus(models.Model):
    class Status(models.TextChoices):
        WANT = "want", "Quero ver"
        WATCHING = "watching", "Assistindo"
        WATCHED = "watched", "Assistido"
        DROPPED = "dropped", "Dropado"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    media_type = models.CharField(max_length=10, choices=(("movie", "Filme"), ("tv", "Serie/Anime")))
    tmdb_id = models.IntegerField()
    status = models.CharField(max_length=20, choices=Status.choices)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "media_type", "tmdb_id")
        indexes = [
            models.Index(fields=["user", "updated_at"]),
            models.Index(fields=["media_type", "tmdb_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.user} {self.media_type}:{self.tmdb_id} -> {self.status}"


class Collection(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="collections")
    title = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user}::{self.title}"


class CollectionItem(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="items")
    media_type = models.CharField(max_length=10, choices=(("movie", "Filme"), ("tv", "Serie/Anime")))
    tmdb_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("collection", "media_type", "tmdb_id")
        indexes = [
            models.Index(fields=["media_type", "tmdb_id"]),
        ]

    def __str__(self):
        return f"{self.collection} -> {self.media_type}:{self.tmdb_id}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_notifications",
        null=True,
        blank=True,
    )
    verb = models.CharField(max_length=80)
    media_type = models.CharField(max_length=10, blank=True)
    tmdb_id = models.IntegerField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read", "created_at"]),
        ]

    def __str__(self):
        return f"Notification<{self.user}:{self.verb}>"


class AvailabilityAlert(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="availability_alerts")
    media_type = models.CharField(max_length=10, choices=(("movie", "Filme"), ("tv", "Serie/Anime")))
    tmdb_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "media_type", "tmdb_id")
        indexes = [
            models.Index(fields=["media_type", "tmdb_id"]),
        ]

    def __str__(self):
        return f"Alert<{self.user}:{self.media_type}:{self.tmdb_id}>"
