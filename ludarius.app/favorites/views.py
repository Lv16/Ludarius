from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .models import Favorite

@login_required
def toggle_favorite_movie(request, tmdb_id: int):
    if request.method == "POST":
        obj, created = Favorite.objects.get_or_create(
            user=request.user, media_type="movie", tmdb_id=tmdb_id
        )
        if not created:
            obj.delete()
    return redirect("tmdb_movie_detail", tmdb_id=tmdb_id)

@login_required
def toggle_favorite_tv(request, tmdb_id: int):
    if request.method == "POST":
        obj, created = Favorite.objects.get_or_create(
            user=request.user, media_type="tv", tmdb_id=tmdb_id
        )
        if not created:
            obj.delete()
    return redirect("tmdb_tv_detail", tmdb_id=tmdb_id)
