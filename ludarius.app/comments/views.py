from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from .forms import CommentForm
from .models import Comment

@login_required
def add_comment(request, movie_id):
    if request.method != "POST":
        return redirect("movie_detail", movie_id=movie_id)

    form = CommentForm(request.POST)
    if form.is_valid():
        Comment.objects.update_or_create(
            user=request.user,
            media_type="movie",
            tmdb_id=movie_id,
            defaults={"text": form.cleaned_data["text"]},
        )
    return redirect("movie_detail", movie_id=movie_id)


@login_required
def add_tmdb_movie_comment(request, tmdb_id):
    if request.method != "POST":
        return redirect("tmdb_movie_detail", tmdb_id=tmdb_id)

    form = CommentForm(request.POST)
    if form.is_valid():
        Comment.objects.update_or_create(
            user=request.user,
            media_type="movie",
            tmdb_id=tmdb_id,
            defaults={"text": form.cleaned_data["text"]},
        )
    return redirect("tmdb_movie_detail", tmdb_id=tmdb_id)

@login_required
def add_tmdb_tv_comment(request, tmdb_id: int):
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            Comment.objects.update_or_create(
                user=request.user,
                media_type="tv",
                tmdb_id=tmdb_id,
                defaults={"text": form.cleaned_data["text"]},
            )
    return redirect("tmdb_tv_detail", tmdb_id=tmdb_id)
