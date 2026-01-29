from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.core.cache import cache
from .forms import RatingForm
from .models import Rating

@login_required
def rate_movie(request, tmdb_id: int):
    if request.method == "POST":
        form = RatingForm(request.POST)
        if form.is_valid():
            Rating.objects.update_or_create(
                user=request.user,
                media_type="movie",
                tmdb_id=tmdb_id,
                defaults={"score": form.cleaned_data["score"]},
            )
            cache.delete(f"ratings:avg:movie:{tmdb_id}")
    return redirect("tmdb_movie_detail", tmdb_id=tmdb_id)

@login_required
def rate_tv(request, tmdb_id: int):
    if request.method == "POST":
        form = RatingForm(request.POST)
        if form.is_valid():
            Rating.objects.update_or_create(
                user=request.user,
                media_type="tv",
                tmdb_id=tmdb_id,
                defaults={"score": form.cleaned_data["score"]},
            )
            cache.delete(f"ratings:avg:tv:{tmdb_id}")
    return redirect("tmdb_tv_detail", tmdb_id=tmdb_id)
