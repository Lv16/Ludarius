from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .models import Favorite


def _toggle_favorite(request, tmdb_id: int, media_type: str, redirect_name: str):
    obj, created = Favorite.objects.get_or_create(
        user=request.user,
        media_type=media_type,
        tmdb_id=tmdb_id,
    )
    if not created:
        obj.delete()
    return redirect(redirect_name, tmdb_id=tmdb_id)


@login_required
def toggle_favorite_movie(request, tmdb_id: int):
    if request.method == "POST":
        return _toggle_favorite(request, tmdb_id, "movie", "tmdb_movie_detail")
    return redirect("tmdb_movie_detail", tmdb_id=tmdb_id)

@login_required
def toggle_favorite_tv(request, tmdb_id: int):
    if request.method == "POST":
        return _toggle_favorite(request, tmdb_id, "tv", "tmdb_tv_detail")
    return redirect("tmdb_tv_detail", tmdb_id=tmdb_id)
