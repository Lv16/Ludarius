from django.urls import path
from . import views

urlpatterns = [
    path("tmdb/movie/<int:tmdb_id>/comment/", views.add_tmdb_movie_comment, name="add_tmdb_movie_comment"),
    path("tmdb/tv/<int:tmdb_id>/comment/", views.add_tmdb_tv_comment, name="add_tmdb_tv_comment"),
]
