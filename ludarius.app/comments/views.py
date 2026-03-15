from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect

from movies.models import Movie

from .forms import CommentForm
from .models import Comment


def _save_tmdb_comment(request, tmdb_id: int, media_type: str, redirect_name: str):
    key = f"rl:comment:{request.user.id}"
    if cache.get(key):
        messages.warning(request, "Espere alguns segundos para comentar novamente.")
        return redirect(redirect_name, tmdb_id=tmdb_id)
    cache.set(key, 1, 10)

    form = CommentForm(request.POST)
    if form.is_valid():
        text = form.cleaned_data["text"].strip()
        if not text:
            messages.error(request, "Seu comentario esta vazio.")
        else:
            Comment.objects.update_or_create(
                user=request.user,
                media_type=media_type,
                tmdb_id=tmdb_id,
                defaults={"text": text},
            )
    else:
        messages.error(request, "Nao foi possivel salvar seu comentario.")
    return redirect(redirect_name, tmdb_id=tmdb_id)


@login_required
def add_comment(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    if request.method != "POST":
        if movie.tmdb_id:
            return redirect("tmdb_movie_detail", tmdb_id=movie.tmdb_id)
        return redirect("movie_detail", movie_id=movie_id)

    if not movie.tmdb_id:
        messages.error(request, "Este filme local ainda nao esta vinculado ao catalogo TMDB.")
        return redirect("movie_detail", movie_id=movie_id)

    return _save_tmdb_comment(request, movie.tmdb_id, "movie", "tmdb_movie_detail")


@login_required
def add_tmdb_movie_comment(request, tmdb_id):
    if request.method != "POST":
        return redirect("tmdb_movie_detail", tmdb_id=tmdb_id)

    return _save_tmdb_comment(request, tmdb_id, "movie", "tmdb_movie_detail")


@login_required
def add_tmdb_tv_comment(request, tmdb_id: int):
    if request.method == "POST":
        return _save_tmdb_comment(request, tmdb_id, "tv", "tmdb_tv_detail")
    return redirect("tmdb_tv_detail", tmdb_id=tmdb_id)
