from django.urls import path
from . import views

urlpatterns = [
    path("tmdb/movie/<int:tmdb_id>/favorite/", views.toggle_favorite_movie, name="favorite_movie"),
    path("tmdb/tv/<int:tmdb_id>/favorite/", views.toggle_favorite_tv, name="favorite_tv"),
]
