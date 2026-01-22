from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("movie/<int:movie_id>/", views.movie_detail, name="movie_detail"),
    path("tmdb/movie/<int:tmdb_id>/", views.tmdb_movie_detail, name="tmdb_movie_detail"),
]
