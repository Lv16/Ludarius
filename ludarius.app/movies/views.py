import requests
from django.core.cache import cache
from django.db.models import Avg, Count
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render

from comments.forms import CommentForm
from comments.models import Comment
from favorites.models import Favorite
from reviews.forms import RatingForm
from reviews.models import Rating

from .models import Movie
from .services.tmdb import (
    get_movie_details,
    get_movie_watch_providers,
    get_popular_movies,
    get_popular_tv,
    get_top_rated_movies,
    get_top_rated_tv,
    get_trending_movies,
    get_trending_tv,
    get_tv_details,
    get_tv_watch_providers,
    search_multi,
)


def _get_local_movie_data(tmdb_id: int):
    local_movie = (
        Movie.objects.filter(tmdb_id=tmdb_id)
        .prefetch_related("availabilities__platform")
        .first()
    )

    availabilities = []
    if local_movie:
        availabilities = (
            local_movie.availabilities.select_related("platform")
            .order_by("platform__name", "access_type")
        )
    return local_movie, availabilities


def _get_ratings_summary(media_type: str, tmdb_id: int) -> dict:
    avg_key = f"ratings:avg:{media_type}:{tmdb_id}"
    avg_data = cache.get(avg_key)

    if avg_data is None:
        agg = Rating.objects.filter(media_type=media_type, tmdb_id=tmdb_id).aggregate(
            avg=Avg("score"),
            count=Count("id"),
        )
        avg_data = {"avg": agg["avg"], "count": agg["count"]}
        cache.set(avg_key, avg_data, 60 * 5)
    return avg_data


def _get_user_media_state(request, media_type: str, tmdb_id: int) -> dict:
    state = {
        "user_rating": None,
        "user_comment": None,
        "comments": None,
        "comment_form": None,
        "is_favorite": False,
    }
    if not request.user.is_authenticated:
        return state

    state["user_rating"] = Rating.objects.filter(
        user=request.user,
        media_type=media_type,
        tmdb_id=tmdb_id,
    ).first()
    state["is_favorite"] = Favorite.objects.filter(
        user=request.user,
        media_type=media_type,
        tmdb_id=tmdb_id,
    ).exists()
    state["comments"] = (
        Comment.objects.filter(media_type=media_type, tmdb_id=tmdb_id)
        .select_related("user")
        .all()
    )
    state["user_comment"] = (
        Comment.objects.filter(media_type=media_type, tmdb_id=tmdb_id, user=request.user)
        .order_by("-created_at")
        .first()
    )
    state["comment_form"] = CommentForm()
    return state


def home(request):
    q = request.GET.get("q", "").strip()
    media_type = request.GET.get("type", "all").strip().lower()
    try:
        page = int(request.GET.get("page", 1) or 1)
    except (TypeError, ValueError):
        page = 1
    page = max(page, 1)

    results = []
    trending_movies = []
    trending_tv = []
    trending_feed = []
    total_pages = 1
    has_prev = False
    has_next = False

    if q:
        try:
            data = search_multi(q, page=page)
            results = data["results"]
            page = data["page"]
            total_pages = data["total_pages"]
            has_prev = page > 1
            has_next = page < total_pages
        except Exception:
            results = []
            page = 1
            total_pages = 1
            has_prev = False
            has_next = False

        if media_type in ("movie", "tv"):
            results = [r for r in results if r.get("media_type") == media_type]
    else:
        try:
            trending_movies = get_trending_movies()
        except Exception:
            trending_movies = []

        try:
            trending_tv = get_trending_tv()
        except Exception:
            trending_tv = []

        for movie in trending_movies:
            trending_feed.append(
                {
                    "media_type": "movie",
                    "tmdb_id": movie.get("tmdb_id"),
                    "title": movie.get("title", ""),
                    "date": movie.get("release_date", ""),
                    "rating": movie.get("rating"),
                    "poster_url": movie.get("poster_url", ""),
                }
            )

        for tv in trending_tv:
            trending_feed.append(
                {
                    "media_type": "tv",
                    "tmdb_id": tv.get("tmdb_id"),
                    "title": tv.get("name", ""),
                    "date": tv.get("first_air_date", ""),
                    "rating": tv.get("rating"),
                    "poster_url": tv.get("poster_url", ""),
                }
            )

        if media_type in ("movie", "tv"):
            trending_feed = [item for item in trending_feed if item["media_type"] == media_type]

        trending_feed.sort(key=lambda item: (item["rating"] is None, -(item["rating"] or 0)))
        trending_feed = trending_feed[:30]

    return render(
        request,
        "movies/home.html",
        {
            "q": q,
            "type": media_type,
            "results": results,
            "trending_feed": trending_feed,
            "page": page,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
        },
    )


def explore(request):
    popular_movies = []
    popular_tv = []
    top_movies = []
    top_tv = []

    try:
        popular_movies = get_popular_movies()
    except Exception:
        popular_movies = []

    try:
        popular_tv = get_popular_tv()
    except Exception:
        popular_tv = []

    try:
        top_movies = get_top_rated_movies()
    except Exception:
        top_movies = []

    try:
        top_tv = get_top_rated_tv()
    except Exception:
        top_tv = []

    return render(
        request,
        "movies/explore.html",
        {
            "popular_movies": popular_movies[:20],
            "popular_tv": popular_tv[:20],
            "top_movies": top_movies[:20],
            "top_tv": top_tv[:20],
        },
    )


def movie_detail(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    if movie.tmdb_id:
        return redirect("tmdb_movie_detail", tmdb_id=movie.tmdb_id)

    availabilities = (
        movie.availabilities.select_related("platform").order_by("platform__name", "access_type")
    )

    return render(
        request,
        "movies/detail.html",
        {
            "movie": movie,
            "availabilities": availabilities,
        },
    )


def tmdb_movie_detail(request, tmdb_id):
    movie = get_movie_details(tmdb_id)
    providers = get_movie_watch_providers(tmdb_id)
    local_movie, availabilities = _get_local_movie_data(tmdb_id)
    avg_data = _get_ratings_summary("movie", tmdb_id)
    user_state = _get_user_media_state(request, "movie", tmdb_id)

    return render(
        request,
        "movies/tmdb_detail.html",
        {
            "movie": movie,
            "providers": providers,
            "local_movie": local_movie,
            "availabilities": availabilities,
            "ratings_avg": avg_data["avg"],
            "ratings_count": avg_data["count"],
            "rating_form": RatingForm(),
            **user_state,
        },
    )


def tmdb_tv_detail(request, tmdb_id):
    tv = get_tv_details(tmdb_id)
    providers = get_tv_watch_providers(tmdb_id)
    avg_data = _get_ratings_summary("tv", tmdb_id)
    user_state = _get_user_media_state(request, "tv", tmdb_id)

    return render(
        request,
        "movies/tmdb_tv_detail.html",
        {
            "tv": tv,
            "providers": providers,
            "ratings_avg": avg_data["avg"],
            "ratings_count": avg_data["count"],
            "rating_form": RatingForm(),
            **user_state,
        },
    )


def tmdb_image_proxy(request, size: str, image_path: str):
    allowed_sizes = {"w92", "w154", "w185", "w342", "w500", "w780", "original"}
    if size not in allowed_sizes:
        return HttpResponseBadRequest("invalid_size")
    safe_path = (image_path or "").lstrip("/")
    if not safe_path:
        return HttpResponseBadRequest("invalid_path")

    url = f"https://image.tmdb.org/t/p/{size}/{safe_path}"
    try:
        res = requests.get(url, stream=True, timeout=8)
        if res.status_code != 200:
            return HttpResponse(status=res.status_code)
        content_type = res.headers.get("Content-Type", "image/jpeg")
        response = HttpResponse(res.content, content_type=content_type)
        response["Cache-Control"] = "public, max-age=86400"
        return response
    except requests.RequestException:
        return HttpResponse(status=502)
