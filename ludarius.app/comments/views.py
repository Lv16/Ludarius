from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from movies.models import Movie
from .forms import CommentForm
from .models import Comment

@login_required
def add_comment(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            # um comentário por usuário por filme
            Comment.objects.update_or_create(
                user=request.user,
                movie=movie,
                defaults={"text": form.cleaned_data["text"]},
            )

    return redirect("movie_detail", movie_id=movie.id)
