from django.shortcuts import render, get_object_or_404
from .models import Movie
from comments.forms import CommentForm
from .services.tmdb import search_movies
from .services.tmdb import get_movie_details, get_movie_watch_providers


def home(request):
    q = request.GET.get("q", "").strip()
    movies = Movie.objects.all().order_by("-created_at")
    if q:
        movies = movies.filter(title__icontains=q)
    movies = movies[:50]
    
    tmdb_results = []
    if q:
        try:
            tmdb_results = search_movies(q)
        except Exception:
            tmdb_results = []
            
    return render(request, "movies/home.html", {
        "movies": movies,
        "q": q,
        "tmdb_results": tmdb_results,
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

    providers = {}
    try:
        providers = get_movie_watch_providers(tmdb_id, region="BR")
    except Exception:
        providers = {"link": "", "flatrate": [], "rent": [], "buy": []} 
        
    return render(request, "movies/tmdb_detail.html", {
        "movie": movie,
        "providers": providers,
    })
        
    

