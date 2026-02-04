from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponse
from .forms import CommentForm
from .models import Comment
from django.core.cache import cache

@login_required
def add_comment(request, movie_id):
    if request.method != "POST":
        return redirect("movie_detail", movie_id=movie_id)

    key = f"rl:comment:{request.user.id}"
    if cache.get(key):
        return HttpResponse("Espere alguns segundos para comentar novamente.", status=429)
    cache.set(key, 1, 10)  # 10 segundos

    form = CommentForm(request.POST)
    if form.is_valid():
        text = form.cleaned_data["text"].strip()
        if not text:
            messages.error(request, "Seu comentário está vazio.")
        else:
            Comment.objects.update_or_create(
                user=request.user,
                media_type="movie",
                tmdb_id=movie_id,
                defaults={"text": text},
            )
    else:
        messages.error(request, "Não foi possível salvar seu comentário.")
    return redirect("movie_detail", movie_id=movie_id)


@login_required
def add_tmdb_movie_comment(request, tmdb_id):
    if request.method != "POST":
        return redirect("tmdb_movie_detail", tmdb_id=tmdb_id)

    key = f"rl:comment:{request.user.id}"
    if cache.get(key):
        return HttpResponse("Espere alguns segundos para comentar novamente.", status=429)
    cache.set(key, 1, 10)  # 10 segundos

    form = CommentForm(request.POST)
    if form.is_valid():
        text = form.cleaned_data["text"].strip()
        if not text:
            messages.error(request, "Seu comentário está vazio.")
        else:
            Comment.objects.update_or_create(
                user=request.user,
                media_type="movie",
                tmdb_id=tmdb_id,
                defaults={"text": text},
            )
    else:
        messages.error(request, "Não foi possível salvar seu comentário.")
    return redirect("tmdb_movie_detail", tmdb_id=tmdb_id)

@login_required
def add_tmdb_tv_comment(request, tmdb_id: int):
    if request.method == "POST":
        key = f"rl:comment:{request.user.id}"
        if cache.get(key):
            return HttpResponse("Espere alguns segundos para comentar novamente.", status=429)
        cache.set(key, 1, 10)  # 10 segundos

        form = CommentForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data["text"].strip()
            if not text:
                messages.error(request, "Seu comentário está vazio.")
            else:
                Comment.objects.update_or_create(
                    user=request.user,
                    media_type="tv",
                    tmdb_id=tmdb_id,
                    defaults={"text": text},
                )
        else:
            messages.error(request, "Não foi possível salvar seu comentário.")
    return redirect("tmdb_tv_detail", tmdb_id=tmdb_id)
