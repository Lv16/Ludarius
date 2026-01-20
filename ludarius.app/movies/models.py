# movies/models.py
from django.db import models


class StreamingPlatform(models.Model):
    name = models.CharField(max_length=100)
    logo_url = models.URLField(blank=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=200)
    original_title = models.CharField(max_length=200, blank=True, null=True)
    synopsis = models.TextField(blank=True, null=True)
    release_date = models.DateField(null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    poster_url = models.URLField(blank=True)
    backdrop_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class MovieAvailability(models.Model):
    ACCESS_TYPE_CHOICES = [
        ('subscription', 'Assinatura'),
        ('rent', 'Aluguel'),
        ('buy', 'Compra'),
    ]

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='availabilities')
    platform = models.ForeignKey(StreamingPlatform, on_delete=models.CASCADE)
    access_type = models.CharField(max_length=20, choices=ACCESS_TYPE_CHOICES)
    price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    link = models.URLField()

    def __str__(self):
        return f"{self.movie.title} - {self.platform.name}"
