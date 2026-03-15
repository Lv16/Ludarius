from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from comments.models import Comment
from favorites.models import Favorite
from movies.services.tmdb import get_movie_details, get_tv_details
from reviews.models import Rating


@login_required
def my_account(request):
    return render(request, "accounts/my_account.html")


def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def my_activity(request):
    tab = request.GET.get("tab", "comments").strip().lower()
    page = int(request.GET.get("page", 1) or 1)
    context = {"tab": tab}

    if tab == "comments":
        qs = Comment.objects.filter(user=request.user).order_by("-created_at")
        page_obj = Paginator(qs, 10).get_page(page)
        titles = _resolve_media_titles(page_obj)
        context["comments"] = [_serialize_comment(comment, titles) for comment in page_obj]
        context["page_obj"] = page_obj

    if tab == "ratings":
        ratings = Rating.objects.filter(user=request.user).order_by("-updated_at")[:50]
        titles = _resolve_media_titles(ratings)
        context["ratings_items"] = [_serialize_rating(rating, titles) for rating in ratings]

    if tab == "favorites":
        favorites = Favorite.objects.filter(user=request.user).order_by("-created_at")[:50]
        titles = _resolve_media_titles(favorites)
        context["favorites_items"] = [_serialize_favorite(favorite, titles) for favorite in favorites]

    return render(request, "accounts/my_activity.html", context)


def _resolve_media_titles(items) -> dict[tuple[str, int], str]:
    keys = []
    pairs = []
    for item in items:
        tmdb_id = getattr(item, "tmdb_id", None)
        media_type = getattr(item, "media_type", "")
        if not tmdb_id:
            continue
        pair = (media_type, tmdb_id)
        if pair in pairs:
            continue
        pairs.append(pair)
        keys.append(_media_title_cache_key(media_type, tmdb_id))

    cached_map = cache.get_many(keys)
    resolved = {}
    missing = []

    for media_type, tmdb_id in pairs:
        cache_key = _media_title_cache_key(media_type, tmdb_id)
        if cache_key in cached_map:
            resolved[(media_type, tmdb_id)] = cached_map[cache_key]
        else:
            missing.append((media_type, tmdb_id))

    to_cache = {}
    for media_type, tmdb_id in missing:
        title = _fetch_media_title(media_type, tmdb_id)
        resolved[(media_type, tmdb_id)] = title
        to_cache[_media_title_cache_key(media_type, tmdb_id)] = title

    if to_cache:
        cache.set_many(to_cache, 60 * 60 * 6)
    return resolved


def _media_title_cache_key(media_type: str, tmdb_id: int) -> str:
    return f"tmdb:title:{media_type}:{tmdb_id}"


def _fetch_media_title(media_type: str, tmdb_id: int) -> str:
    if not tmdb_id:
        return ""

    try:
        if media_type == "movie":
            data = get_movie_details(tmdb_id)
            return data.get("title") or ""
        if media_type == "tv":
            data = get_tv_details(tmdb_id)
            return data.get("name") or ""
    except Exception:
        return ""
    return ""


def _detail_url_name(media_type: str) -> str:
    return "tmdb_movie_detail" if media_type == "movie" else "tmdb_tv_detail"


def _serialize_comment(comment: Comment, titles: dict[tuple[str, int], str]) -> dict:
    return {
        "id": comment.id,
        "media_type": comment.media_type,
        "tmdb_id": comment.tmdb_id,
        "title": titles.get((comment.media_type, comment.tmdb_id), ""),
        "text": comment.text,
        "created_at": comment.created_at,
        "detail_url_name": _detail_url_name(comment.media_type),
    }


def _serialize_rating(rating: Rating, titles: dict[tuple[str, int], str]) -> dict:
    return {
        "media_type": rating.media_type,
        "tmdb_id": rating.tmdb_id,
        "title": titles.get((rating.media_type, rating.tmdb_id), ""),
        "score": rating.score,
        "updated_at": rating.updated_at,
        "detail_url_name": _detail_url_name(rating.media_type),
    }


def _serialize_favorite(favorite: Favorite, titles: dict[tuple[str, int], str]) -> dict:
    return {
        "media_type": favorite.media_type,
        "tmdb_id": favorite.tmdb_id,
        "title": titles.get((favorite.media_type, favorite.tmdb_id), ""),
        "created_at": favorite.created_at,
        "detail_url_name": _detail_url_name(favorite.media_type),
    }


User = get_user_model()


def public_profile(request, username: str):
    profile_user = get_object_or_404(User, username=username)

    comments_qs = Comment.objects.filter(user=profile_user).order_by("-created_at")
    ratings_qs = Rating.objects.filter(user=profile_user).order_by("-updated_at")
    favorites_qs = Favorite.objects.filter(user=profile_user).order_by("-created_at")

    stats = {
        "comments_count": comments_qs.count(),
        "ratings_count": ratings_qs.count(),
        "favorites_count": favorites_qs.count(),
    }

    page_comments = int(request.GET.get("page_comments", 1) or 1)
    page_ratings = int(request.GET.get("page_ratings", 1) or 1)

    comments_page = Paginator(comments_qs, 10).get_page(page_comments)
    ratings_page = Paginator(ratings_qs, 10).get_page(page_ratings)
    favorites = list(favorites_qs[:12])

    title_map = _resolve_media_titles(list(comments_page) + list(ratings_page) + favorites)
    comments_items = [_serialize_comment(comment, title_map) for comment in comments_page]
    ratings_items = [_serialize_rating(rating, title_map) for rating in ratings_page]
    favorites_items = [_serialize_favorite(favorite, title_map) for favorite in favorites]

    return render(
        request,
        "accounts/public_profile.html",
        {
            "profile_user": profile_user,
            "stats": stats,
            "comments_page": comments_page,
            "ratings_page": ratings_page,
            "comments_items": comments_items,
            "ratings_items": ratings_items,
            "favorites_items": favorites_items,
        },
    )
