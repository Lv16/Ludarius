from django.shortcuts import render, get_object_or_404

from comments.forms import CommentForm
from comments.models import Comment
from .models import Movie
from .services.tmdb import (
    get_movie_details,
    get_movie_watch_providers,
    get_trending_movies,
    get_trending_tv,
    get_tv_details,
    get_tv_watch_providers,
    search_multi,
)


def home(request):
    q = request.GET.get("q", "").strip()

    results = []
    trending_movies = []
    trending_tv = []

    if q:
        try:
            results = search_multi(q)
        except Exception:
            results = []
    else:
        try:
            trending_movies = get_trending_movies()
        except Exception:
            trending_movies = []

        try:
            trending_tv = get_trending_tv()
        except Exception:
            trending_tv = []

    return render(request, "movies/home.html", {
        "q": q,
        "results": results,
        "trending_movies": trending_movies,
        "trending_tv": trending_tv,
    })

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
    
def tmdb_movie_detail(request, tmdb_id):
    movie = get_movie_details(tmdb_id)

    try:
        providers = get_movie_watch_providers(tmdb_id, region="BR")
    except Exception:
        providers = {"link": "", "flatrate": [], "rent": [], "buy": []}

    comments = None
    comment_form = None

    if request.user.is_authenticated:
        comments = Comment.objects.filter(media_type="movie", tmdb_id=tmdb_id).select_related("user")
        comment_form = CommentForm()

    return render(request, "movies/tmdb_detail.html", {
        "movie": movie,
        "providers": providers,
        "comments": comments,
        "comment_form": comment_form,
    })

def tmdb_tv_detail(request, tmdb_id):
    tv = get_tv_details(tmdb_id)

    try:
        providers = get_tv_watch_providers(tmdb_id, region="BR")
    except Exception:
        providers = {"link": "", "flatrate": [], "rent": [], "buy": []}

    comments = None
    comment_form = None

    if request.user.is_authenticated:
        comments = Comment.objects.filter(media_type="tv", tmdb_id=tmdb_id).select_related("user")
        comment_form = CommentForm()

    return render(request, "movies/tmdb_tv_detail.html", {
        "tv": tv,
        "providers": providers,
        "comments": comments,
        "comment_form": comment_form,
    })
