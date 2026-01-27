from django.urls import path
from . import views

urlpatterns = [
    path("tmdb/movie/<int:tmdb_id>/rate/", views.rate_movie, name="rate_movie"),
    path("tmdb/tv/<int:tmdb_id>/rate/", views.rate_tv, name="rate_tv"),
]
