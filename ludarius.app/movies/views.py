from django.shortcuts import render, get_object_or_404
from .models import Movie


def home(request):
    movies = Movie.objects.order_by("-created_at")[:30]
    return render(request, "movies/home.html", {"movies": movies})


from django.shortcuts import render, get_object_or_404
from .models import Movie

def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    availabilities = (
        movie.availabilities
        .select_related("platform")
        .order_by("platform__name", "access_type")
    )

    return render(
        request,
        "movies/detail.html",
        {"movie": movie, "availabilities": availabilities},
    )
