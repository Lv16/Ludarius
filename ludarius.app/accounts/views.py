from django.contrib import messages
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from comments.models import Comment
from favorites.models import Favorite
from movies.services.tmdb import get_movie_details, get_tv_details
from reviews.models import Rating

from .forms import CollectionAddItemForm, CollectionForm, MediaStatusForm, ProfileForm
from .models import AvailabilityAlert, Collection, CollectionItem, MediaStatus, Notification, Profile


@login_required
def my_account(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        profile_form = ProfileForm(request.POST, instance=profile)
        collection_form = CollectionForm(request.POST)
        if "save_profile" in request.POST and profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Perfil atualizado.")
            return redirect("my_account")
        if "create_collection" in request.POST and collection_form.is_valid():
            collection = collection_form.save(commit=False)
            collection.user = request.user
            collection.save()
            messages.success(request, "Colecao criada.")
            return redirect("my_account")
    else:
        profile_form = ProfileForm(instance=profile)
        collection_form = CollectionForm()

    collections = Collection.objects.filter(user=request.user).prefetch_related("items")
    alerts = AvailabilityAlert.objects.filter(user=request.user).order_by("-created_at")
    notifications_unread = Notification.objects.filter(user=request.user, is_read=False).count()

    return render(
        request,
        "accounts/my_account.html",
        {
            "profile_form": profile_form,
            "collection_form": collection_form,
            "collections": collections,
            "alerts": alerts,
            "notifications_unread": notifications_unread,
        },
    )


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

    if tab == "statuses":
        statuses = MediaStatus.objects.filter(user=request.user).order_by("-updated_at")[:50]
        titles = _resolve_media_titles(statuses)
        context["status_items"] = [_serialize_status(status, titles) for status in statuses]

    return render(request, "accounts/my_activity.html", context)


@login_required
def notifications_list(request):
    notifications = Notification.objects.filter(user=request.user).select_related("actor")
    return render(request, "accounts/notifications.html", {"notifications": notifications})


@login_required
def recommendations(request):
    return render(
        request,
        "accounts/recommendations.html",
        {"recommendations": _get_recommendations(request.user)},
    )


@login_required
def mark_notifications_read(request):
    if request.method == "POST":
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect("notifications")


@login_required
def update_media_status(request, media_type: str, tmdb_id: int):
    redirect_name = "tmdb_movie_detail" if media_type == "movie" else "tmdb_tv_detail"
    if request.method != "POST":
        return redirect(redirect_name, tmdb_id=tmdb_id)

    form = MediaStatusForm(request.POST)
    if form.is_valid():
        MediaStatus.objects.update_or_create(
            user=request.user,
            media_type=media_type,
            tmdb_id=tmdb_id,
            defaults={"status": form.cleaned_data["status"]},
        )
        messages.success(request, "Status salvo.")
    else:
        messages.error(request, "Nao foi possivel salvar o status.")
    return redirect(redirect_name, tmdb_id=tmdb_id)


@login_required
def add_to_collection(request, media_type: str, tmdb_id: int):
    redirect_name = "tmdb_movie_detail" if media_type == "movie" else "tmdb_tv_detail"
    if request.method != "POST":
        return redirect(redirect_name, tmdb_id=tmdb_id)

    form = CollectionAddItemForm(request.POST, user=request.user)
    if form.is_valid():
        collection = form.cleaned_data["collection"]
        CollectionItem.objects.get_or_create(
            collection=collection,
            media_type=media_type,
            tmdb_id=tmdb_id,
        )
        messages.success(request, "Titulo adicionado a colecao.")
    else:
        messages.error(request, "Nao foi possivel adicionar a colecao.")
    return redirect(redirect_name, tmdb_id=tmdb_id)


@login_required
def create_availability_alert(request, media_type: str, tmdb_id: int):
    redirect_name = "tmdb_movie_detail" if media_type == "movie" else "tmdb_tv_detail"
    if request.method == "POST":
        AvailabilityAlert.objects.get_or_create(
            user=request.user,
            media_type=media_type,
            tmdb_id=tmdb_id,
        )
        messages.success(request, "Alerta de disponibilidade criado.")
    return redirect(redirect_name, tmdb_id=tmdb_id)


@login_required
def remove_availability_alert(request, alert_id: int):
    alert = get_object_or_404(AvailabilityAlert, id=alert_id, user=request.user)
    if request.method == "POST":
        alert.delete()
        messages.success(request, "Alerta removido.")
    return redirect("my_account")


@login_required
def remove_collection_item(request, item_id: int):
    item = get_object_or_404(CollectionItem, id=item_id, collection__user=request.user)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Item removido da colecao.")
    return redirect("my_account")


def collection_detail(request, collection_id: int):
    collection = get_object_or_404(Collection, id=collection_id)
    if not collection.is_public and collection.user != request.user:
        return redirect("home")

    items = list(collection.items.all())
    titles = _resolve_media_titles(items)
    collection_items = [_serialize_collection_item(item, titles) for item in items]
    return render(
        request,
        "accounts/collection_detail.html",
        {"collection": collection, "collection_items": collection_items},
    )


def user_search(request):
    q = request.GET.get("q", "").strip()
    users = []
    if q:
        users = get_user_model().objects.filter(Q(username__icontains=q))[:20]
    return render(request, "accounts/user_search.html", {"q": q, "users": users})


def public_profile(request, username: str):
    profile_user = get_object_or_404(get_user_model(), username=username)
    profile, _ = Profile.objects.get_or_create(user=profile_user)

    comments_qs = Comment.objects.filter(user=profile_user).order_by("-created_at")
    ratings_qs = Rating.objects.filter(user=profile_user).order_by("-updated_at")
    favorites_qs = Favorite.objects.filter(user=profile_user).order_by("-created_at")
    statuses_qs = MediaStatus.objects.filter(user=profile_user).order_by("-updated_at")
    collections_qs = Collection.objects.filter(user=profile_user, is_public=True).prefetch_related("items")

    stats = {
        "comments_count": comments_qs.count(),
        "ratings_count": ratings_qs.count(),
        "favorites_count": favorites_qs.count(),
        "statuses_count": statuses_qs.count(),
        "collections_count": collections_qs.count(),
    }

    page_comments = int(request.GET.get("page_comments", 1) or 1)
    page_ratings = int(request.GET.get("page_ratings", 1) or 1)

    comments_page = Paginator(comments_qs, 10).get_page(page_comments)
    ratings_page = Paginator(ratings_qs, 10).get_page(page_ratings)
    favorites = list(favorites_qs[:12])
    statuses = list(statuses_qs[:12])
    collections = list(collections_qs[:12])

    title_map = _resolve_media_titles(list(comments_page) + list(ratings_page) + favorites + statuses)
    comments_items = [_serialize_comment(comment, title_map) for comment in comments_page]
    ratings_items = [_serialize_rating(rating, title_map) for rating in ratings_page]
    favorites_items = [_serialize_favorite(favorite, title_map) for favorite in favorites]
    status_items = [_serialize_status(status, title_map) for status in statuses]

    return render(
        request,
        "accounts/public_profile.html",
        {
            "profile_user": profile_user,
            "profile": profile,
            "stats": stats,
            "comments_page": comments_page,
            "ratings_page": ratings_page,
            "comments_items": comments_items,
            "ratings_items": ratings_items,
            "favorites_items": favorites_items,
            "status_items": status_items,
            "collections": collections,
        },
    )


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


def _build_media_payload(media_type: str, tmdb_id: int) -> dict:
    try:
        if media_type == "movie":
            data = get_movie_details(tmdb_id)
            return {
                "media_type": media_type,
                "tmdb_id": tmdb_id,
                "title": data.get("title") or "",
                "poster_url": data.get("poster_url", ""),
                "detail_url_name": "tmdb_movie_detail",
            }
        data = get_tv_details(tmdb_id)
        return {
            "media_type": media_type,
            "tmdb_id": tmdb_id,
            "title": data.get("name") or "",
            "poster_url": data.get("poster_url", ""),
            "detail_url_name": "tmdb_tv_detail",
        }
    except Exception:
        return {
            "media_type": media_type,
            "tmdb_id": tmdb_id,
            "title": f"TMDB {tmdb_id}",
            "poster_url": "",
            "detail_url_name": _detail_url_name(media_type),
        }


def _get_recommendations(user) -> list[dict]:
    known_pairs = set(Favorite.objects.filter(user=user).values_list("media_type", "tmdb_id"))
    known_pairs.update(MediaStatus.objects.filter(user=user).values_list("media_type", "tmdb_id"))
    known_pairs.update(Rating.objects.filter(user=user).values_list("media_type", "tmdb_id"))

    seed_ids = Favorite.objects.filter(user=user).values_list("tmdb_id", flat=True)
    similar_users = Favorite.objects.filter(tmdb_id__in=seed_ids).exclude(user=user).values_list("user_id", flat=True)

    recommendations = []
    seen = set()

    # Use a manual ranking loop to stay simple and avoid new aggregation complexity here.
    for row in list(
        Favorite.objects.filter(user_id__in=similar_users)
        .exclude(user=user)
        .values("media_type", "tmdb_id")
        .annotate(score=Count("id"))
        .order_by("-score")[:20]
    ) + list(
        Favorite.objects.values("media_type", "tmdb_id")
        .annotate(score=Count("id"))
        .order_by("-score")[:20]
    ):
        pair = (row["media_type"], row["tmdb_id"])
        if pair in known_pairs or pair in seen:
            continue
        seen.add(pair)
        payload = _build_media_payload(row["media_type"], row["tmdb_id"])
        payload["score"] = row["score"]
        recommendations.append(payload)
        if len(recommendations) >= 12:
            break

    return recommendations


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


def _serialize_status(status: MediaStatus, titles: dict[tuple[str, int], str]) -> dict:
    return {
        "media_type": status.media_type,
        "tmdb_id": status.tmdb_id,
        "title": titles.get((status.media_type, status.tmdb_id), ""),
        "status": status.get_status_display(),
        "updated_at": status.updated_at,
        "detail_url_name": _detail_url_name(status.media_type),
    }


def _serialize_collection_item(item: CollectionItem, titles: dict[tuple[str, int], str]) -> dict:
    return {
        "media_type": item.media_type,
        "tmdb_id": item.tmdb_id,
        "title": titles.get((item.media_type, item.tmdb_id), ""),
        "created_at": item.created_at,
        "detail_url_name": _detail_url_name(item.media_type),
    }
