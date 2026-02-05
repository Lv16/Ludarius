from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest
import requests
from comments.forms import CommentForm
from comments.models import Comment
from .models import Movie
from favorites.models import Favorite
from reviews.forms import RatingForm
from reviews.models import Rating
from django.db.models import Avg, Count
from django.core.cache import cache
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
    media_type = request.GET.get("type", "all").strip().lower()  # all | movie | tv
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

        # filtro também na busca (opcional, mas útil)
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

        # Normaliza e mistura num feed único
        for m in trending_movies:
            trending_feed.append({
                "media_type": "movie",
                "tmdb_id": m.get("tmdb_id"),
                "title": m.get("title", ""),
                "date": m.get("release_date", ""),
                "rating": m.get("rating"),
                "poster_url": m.get("poster_url", ""),
            })

        for t in trending_tv:
            trending_feed.append({
                "media_type": "tv",
                "tmdb_id": t.get("tmdb_id"),
                "title": t.get("name", ""),
                "date": t.get("first_air_date", ""),
                "rating": t.get("rating"),
                "poster_url": t.get("poster_url", ""),
            })

        if media_type in ("movie", "tv"):
            trending_feed = [x for x in trending_feed if x["media_type"] == media_type]

        trending_feed.sort(key=lambda x: (x["rating"] is None, -(x["rating"] or 0)))

        trending_feed = trending_feed[:30]

    return render(request, "movies/home.html", {
        "q": q,
        "type": media_type,          # pro template destacar o filtro
        "results": results,
        "trending_feed": trending_feed,
        "page": page,
        "total_pages": total_pages,
        "has_prev": has_prev,
        "has_next": has_next,
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
        comments = (
            Comment.objects
            .filter(media_type="movie", tmdb_id=movie_id)
            .select_related("user")
            .all()
        )
        form = CommentForm()
        
    return render(request, "movies/detail.html", {
        "movie": movie,
        "availabilities": availabilities,
        "comments": comments,
        "comment_form": form,
    })
    
def tmdb_movie_detail(request, tmdb_id):
    movie = get_movie_details(tmdb_id)
    providers = get_movie_watch_providers(tmdb_id)

    # Média Ludarius (cache curto)
    avg_key = f"ratings:avg:movie:{tmdb_id}"
    avg_data = cache.get(avg_key)

    if avg_data is None:
        agg = Rating.objects.filter(media_type="movie", tmdb_id=tmdb_id).aggregate(
            avg=Avg("score"),
            count=Count("id"),
        )
        avg_data = {
            "avg": agg["avg"],
            "count": agg["count"],
        }
        cache.set(avg_key, avg_data, 60 * 5)  # 5 min

    rating_form = RatingForm()
    user_rating = None
    user_comment = None
    comments = None
    comment_form = None
    is_favorite = False

    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(
            user=request.user,
            media_type="movie",
            tmdb_id=tmdb_id
        ).first()
        is_favorite = Favorite.objects.filter(
            user=request.user,
            media_type="movie",
            tmdb_id=tmdb_id
        ).exists()
        comments = (
            Comment.objects
            .filter(media_type="movie", tmdb_id=tmdb_id)
            .select_related("user")
            .all()
        )
        user_comment = (
            Comment.objects
            .filter(media_type="movie", tmdb_id=tmdb_id, user=request.user)
            .order_by("-created_at")
            .first()
        )
        comment_form = CommentForm()

    return render(request, "movies/tmdb_detail.html", {
        "movie": movie,
        "providers": providers,
        "ratings_avg": avg_data["avg"],
        "ratings_count": avg_data["count"],
        "rating_form": rating_form,
        "user_rating": user_rating,
        "is_favorite": is_favorite,
        "comments": comments,
        "comment_form": comment_form,
        "user_comment": user_comment,
    })
    
def tmdb_tv_detail(request, tmdb_id):
    tv = get_tv_details(tmdb_id)
    providers = get_tv_watch_providers(tmdb_id)

    avg_key = f"ratings:avg:tv:{tmdb_id}"
    avg_data = cache.get(avg_key)

    if avg_data is None:
        agg = Rating.objects.filter(media_type="tv", tmdb_id=tmdb_id).aggregate(
            avg=Avg("score"),
            count=Count("id"),
        )
        avg_data = {"avg": agg["avg"], "count": agg["count"]}
        cache.set(avg_key, avg_data, 60 * 5)

    rating_form = RatingForm()
    user_rating = None
    user_comment = None
    comments = None
    comment_form = None
    is_favorite = False

    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(
            user=request.user,
            media_type="tv",
            tmdb_id=tmdb_id
        ).first()
        is_favorite = Favorite.objects.filter(
            user=request.user,
            media_type="tv",
            tmdb_id=tmdb_id
        ).exists()
        comments = (
            Comment.objects
            .filter(media_type="tv", tmdb_id=tmdb_id)
            .select_related("user")
            .all()
        )
        user_comment = (
            Comment.objects
            .filter(media_type="tv", tmdb_id=tmdb_id, user=request.user)
            .order_by("-created_at")
            .first()
        )
        comment_form = CommentForm()

    return render(request, "movies/tmdb_tv_detail.html", {
        "tv": tv,
        "providers": providers,
        "ratings_avg": avg_data["avg"],
        "ratings_count": avg_data["count"],
        "rating_form": rating_form,
        "user_rating": user_rating,
        "is_favorite": is_favorite,
        "comments": comments,
        "comment_form": comment_form,
        "user_comment": user_comment,
    })


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
