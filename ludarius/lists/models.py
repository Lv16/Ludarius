from django.db import models
from django.conf import settings


class List(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class ListItem(models.Model):
    list = models.ForeignKey(List, related_name='items', on_delete=models.CASCADE)
    media = models.ForeignKey('mediaitems.MediaItem', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
