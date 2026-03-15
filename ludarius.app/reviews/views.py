from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from django.core.cache import cache
from .forms import RatingForm
from .models import Rating


def _rate_media(request, tmdb_id: int, media_type: str, redirect_name: str):
    key = f"rl:rating:{request.user.id}"
    if cache.get(key):
        messages.warning(request, "Espere alguns segundos para avaliar novamente.")
        return redirect(redirect_name, tmdb_id=tmdb_id)
    cache.set(key, 1, 5)

    form = RatingForm(request.POST)
    if form.is_valid():
        Rating.objects.update_or_create(
            user=request.user,
            media_type=media_type,
            tmdb_id=tmdb_id,
            defaults={"score": form.cleaned_data["score"]},
        )
        cache.delete(f"ratings:avg:{media_type}:{tmdb_id}")
    return redirect(redirect_name, tmdb_id=tmdb_id)


@login_required
def rate_movie(request, tmdb_id: int):
    if request.method == "POST":
        return _rate_media(request, tmdb_id, "movie", "tmdb_movie_detail")
    return redirect("tmdb_movie_detail", tmdb_id=tmdb_id)

@login_required
def rate_tv(request, tmdb_id: int):
    if request.method == "POST":
        return _rate_media(request, tmdb_id, "tv", "tmdb_tv_detail")
    return redirect("tmdb_tv_detail", tmdb_id=tmdb_id)
