import requests
from django.core.cache import cache
from django.db.models import Avg, Count
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.forms import CollectionAddItemForm, MediaStatusForm
from accounts.models import AvailabilityAlert, MediaStatus
from comments.forms import CommentForm
from comments.models import Comment
from favorites.models import Favorite
from reviews.forms import RatingForm
from reviews.models import Rating

from .models import Movie, MovieAvailability, StreamingPlatform
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
        "user_status": None,
        "comments": None,
        "comment_form": None,
        "status_form": None,
        "collection_form": None,
        "is_favorite": False,
        "has_availability_alert": False,
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
    state["user_status"] = MediaStatus.objects.filter(
        user=request.user,
        media_type=media_type,
        tmdb_id=tmdb_id,
    ).first()
    state["status_form"] = MediaStatusForm(
        initial={"status": state["user_status"].status} if state["user_status"] else None
    )
    state["collection_form"] = CollectionAddItemForm(user=request.user)
    state["has_availability_alert"] = AvailabilityAlert.objects.filter(
        user=request.user,
        media_type=media_type,
        tmdb_id=tmdb_id,
    ).exists()
    return state


def _get_media_social_summary(media_type: str, tmdb_id: int) -> dict:
    favorite_count = Favorite.objects.filter(media_type=media_type, tmdb_id=tmdb_id).count()
    comment_count = Comment.objects.filter(media_type=media_type, tmdb_id=tmdb_id).count()
    status_rows = (
        MediaStatus.objects
        .filter(media_type=media_type, tmdb_id=tmdb_id)
        .values("status")
        .annotate(total=Count("id"))
    )
    status_counts = {row["status"]: row["total"] for row in status_rows}
    return {
        "favorite_count": favorite_count,
        "comment_count": comment_count,
        "status_counts": status_counts,
    }


def _build_media_card(media_type: str, tmdb_id: int) -> dict | None:
    try:
        if media_type == "movie":
            data = get_movie_details(tmdb_id)
            title = data.get("title") or ""
            date = data.get("release_date") or ""
        else:
            data = get_tv_details(tmdb_id)
            title = data.get("name") or ""
            date = data.get("first_air_date") or ""
        return {
            "media_type": media_type,
            "tmdb_id": tmdb_id,
            "title": title,
            "date": date,
            "poster_url": data.get("poster_url", ""),
        }
    except Exception:
        return None


def _get_internal_rankings() -> dict:
    cache_key = "ludarius:internal-rankings"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    rankings = {
        "most_favorited": [],
        "most_commented": [],
        "top_rated": [],
        "most_wanted": [],
    }

    favorite_rows = (
        Favorite.objects.values("media_type", "tmdb_id")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )
    comment_rows = (
        Comment.objects.values("media_type", "tmdb_id")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )
    rating_rows = (
        Rating.objects.values("media_type", "tmdb_id")
        .annotate(avg_score=Avg("score"), total=Count("id"))
        .order_by("-avg_score", "-total")[:5]
    )
    wanted_rows = (
        MediaStatus.objects.filter(status=MediaStatus.Status.WANT)
        .values("media_type", "tmdb_id")
        .annotate(total=Count("id"))
        .order_by("-total")[:5]
    )

    for row in favorite_rows:
        card = _build_media_card(row["media_type"], row["tmdb_id"])
        if card:
            card["metric"] = row["total"]
            rankings["most_favorited"].append(card)

    for row in comment_rows:
        card = _build_media_card(row["media_type"], row["tmdb_id"])
        if card:
            card["metric"] = row["total"]
            rankings["most_commented"].append(card)

    for row in rating_rows:
        card = _build_media_card(row["media_type"], row["tmdb_id"])
        if card:
            card["metric"] = row["avg_score"]
            rankings["top_rated"].append(card)

    for row in wanted_rows:
        card = _build_media_card(row["media_type"], row["tmdb_id"])
        if card:
            card["metric"] = row["total"]
            rankings["most_wanted"].append(card)

    cache.set(cache_key, rankings, 60 * 5)
    return rankings


def _fallback_suggestion_items() -> list[dict]:
    return [
        {"media_type": "movie", "tmdb_id": 157336, "title": "Interestelar", "date": "2014-11-05"},
        {"media_type": "movie", "tmdb_id": 27205, "title": "A Origem", "date": "2010-07-15"},
        {"media_type": "movie", "tmdb_id": 603, "title": "Matrix", "date": "1999-03-30"},
        {"media_type": "movie", "tmdb_id": 550, "title": "Clube da Luta", "date": "1999-10-15"},
        {"media_type": "movie", "tmdb_id": 680, "title": "Pulp Fiction", "date": "1994-09-10"},
        {"media_type": "movie", "tmdb_id": 299536, "title": "Vingadores: Guerra Infinita", "date": "2018-04-25"},
        {"media_type": "tv", "tmdb_id": 1396, "title": "Breaking Bad", "date": "2008-01-20"},
        {"media_type": "tv", "tmdb_id": 1399, "title": "Game of Thrones", "date": "2011-04-17"},
        {"media_type": "tv", "tmdb_id": 66732, "title": "Stranger Things", "date": "2016-07-15"},
        {"media_type": "tv", "tmdb_id": 100088, "title": "The Last of Us", "date": "2023-01-15"},
        {"media_type": "tv", "tmdb_id": 37854, "title": "One Piece", "date": "1999-10-20"},
        {"media_type": "tv", "tmdb_id": 46260, "title": "Naruto", "date": "2002-10-03"},
    ]


def _popular_suggestion_items() -> list[dict]:
    items = []

    try:
        for movie in get_popular_movies()[:5]:
            items.append(
                {
                    "media_type": "movie",
                    "tmdb_id": movie.get("tmdb_id"),
                    "title": movie.get("title", ""),
                    "date": movie.get("release_date", ""),
                }
            )
    except Exception:
        pass

    try:
        for tv in get_popular_tv()[:5]:
            items.append(
                {
                    "media_type": "tv",
                    "tmdb_id": tv.get("tmdb_id"),
                    "title": tv.get("name", ""),
                    "date": tv.get("first_air_date", ""),
                }
            )
    except Exception:
        pass

    return items or _fallback_suggestion_items()


def search_suggestions(request):
    q = request.GET.get("q", "").strip()
    media_type = request.GET.get("type", "all").strip().lower()

    try:
        if len(q) >= 2:
            items = search_multi(q, page=1).get("results", [])
        else:
            items = _popular_suggestion_items()
    except Exception:
        items = []

    if not items:
        items = _popular_suggestion_items()

    if media_type in ("movie", "tv"):
        items = [item for item in items if item.get("media_type") == media_type]
        if not items:
            items = [
                item
                for item in _fallback_suggestion_items()
                if item.get("media_type") == media_type
            ]

    results = []
    for item in items[:8]:
        tmdb_id = item.get("tmdb_id")
        item_type = item.get("media_type")
        title = item.get("title", "")

        if not tmdb_id or not item_type or not title:
            continue

        results.append(
            {
                "title": title,
                "label": "Filme" if item_type == "movie" else "Serie/Anime",
                "date": item.get("date", ""),
                "url": (
                    f"/tmdb/movie/{tmdb_id}/"
                    if item_type == "movie"
                    else f"/tmdb/tv/{tmdb_id}/"
                ),
            }
        )

    response = JsonResponse({"results": results})
    response["Cache-Control"] = "no-store"
    return response


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
            "suggestion_options": _fallback_suggestion_items(),
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
            **_get_internal_rankings(),
        },
    )


def provider_list(request):
    providers = (
        MovieAvailability.objects.values("platform__id", "platform__name")
        .annotate(total=Count("id"))
        .order_by("platform__name")
    )
    return render(request, "movies/provider_list.html", {"providers": providers})


def provider_detail(request, platform_id: int):
    platform = get_object_or_404(StreamingPlatform, id=platform_id)
    access_type = request.GET.get("access_type", "").strip().lower()

    availabilities = MovieAvailability.objects.filter(platform=platform).select_related("movie")
    if access_type in {"subscription", "rent", "buy"}:
        availabilities = availabilities.filter(access_type=access_type)
    else:
        access_type = ""

    availabilities = availabilities.order_by("movie__title")

    return render(
        request,
        "movies/provider_detail.html",
        {
            "platform": platform,
            "access_type": access_type,
            "availabilities": availabilities,
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
    social_summary = _get_media_social_summary("movie", tmdb_id)

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
            **social_summary,
            "rating_form": RatingForm(),
            **user_state,
        },
    )


def tmdb_tv_detail(request, tmdb_id):
    tv = get_tv_details(tmdb_id)
    providers = get_tv_watch_providers(tmdb_id)
    avg_data = _get_ratings_summary("tv", tmdb_id)
    user_state = _get_user_media_state(request, "tv", tmdb_id)
    social_summary = _get_media_social_summary("tv", tmdb_id)

    return render(
        request,
        "movies/tmdb_tv_detail.html",
        {
            "tv": tv,
            "providers": providers,
            "ratings_avg": avg_data["avg"],
            "ratings_count": avg_data["count"],
            **social_summary,
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
