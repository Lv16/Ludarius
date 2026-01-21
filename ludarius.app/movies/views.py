from django.shortcuts import render, get_object_or_404
from .models import Movie
from comments.models import Comment


def home(request):
    q = request.GET.get("q", "").strip()
    movies = Movie.objects.all().order_by("-created_at")
    if q:
        movies = movies.filter(title__icontains=q)
    movies = movies[:50]
    
    return render(request, "movies/home.html", {"movies": movies, "q": q})


def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    
    availabilities = (
        movie.availabilities
        .select_related("platform")
        .order_by("platform__name", "access_type")
    )
    
    comments = None
    form = None
    
    if request.user.is_authenticated:
        comments = movie.comments.select_related("user").all()
        form = CommentForm()
        
    return render(request, "movies/detail.html", {
        "movie": movie,
        "availabilities": availabilities,
        "comments": comments,
        "comment_form": form,
    })
