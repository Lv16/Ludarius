from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("movie/<int:movie_id>/", views.movie_detail, name="movie_detail"),
    path("tmdb/movie/<int:tmdb_id>/", views.tmdb_movie_detail, name="tmdb_movie_detail"),
    path("tmdb/tv/<int:tmdb_id>/", views.tmdb_tv_detail, name="tmdb_tv_detail"),
    path("tmdb/image/<str:size>/<path:image_path>", views.tmdb_image_proxy, name="tmdb_image_proxy"),
    path("explorar/", views.explore, name="explore"),

]
