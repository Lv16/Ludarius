# -*- coding: utf-8 -*-
from django.db import models
from django.conf import settings

class Comment(models.Model):
    MEDIA_TYPE_CHOICES = [
        ("movie", "filme"),
        ("tv", "série"),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default="movie")
    tmdb_id = models.IntegerField(null=True, blank=True)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("user", "media_type", "tmdb_id")
        ordering = ["-created_at"]
        
    def __str__(self):
        return f"{self.user.username} - {self.media_type}: {self.tmdb_id}"
