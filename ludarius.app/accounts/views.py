from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from comments.models import Comment
from django.core.cache import cache
from django.core.paginator import Paginator
from reviews.models import Rating
from movies.services.tmdb import get_movie_details, get_tv_details
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth import logout

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
        qs = (
            Comment.objects
            .filter(user=request.user)
            .order_by("-created_at")
        )
        page_obj = Paginator(qs, 10).get_page(page)
        
        items = []
        for c in page_obj:
            items.append({
                "id": c.id,
                "media_type": c.media_type,
                "tmdb_id": c.tmdb_id,
                "title": _get_media_title(c.media_type, c.tmdb_id),
                "text": c.text,
                "created_at": c.created_at,
                "detail_url_name": "tmdb_movie_detail" if c.media_type == "movie" else "tmdb_tv_detail",
            })
            
        context["comments"] = items
        context["page_obj"] = page_obj

    if tab == "ratings":
        ratings = (
            Rating.objects
            .filter(user=request.user)
            .order_by("-updated_at")[:50]
        )

        items = []
        for r in ratings:
            items.append({
                "media_type": r.media_type,
                "tmdb_id": r.tmdb_id,
                "score": r.score,
                "updated_at": r.updated_at,
                "detail_url_name": "tmdb_movie_detail" if r.media_type == "movie" else "tmdb_tv_detail",
            })

        context["ratings_items"] = items
    
    return render(request, 'accounts/my_activity.html', context)


def _get_media_title(media_type: str, tmdb_id: int) -> str:
    if not tmdb_id:
        return ""

    cache_key = f"tmdb:title:{media_type}:{tmdb_id}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    title = ""
    try:
        if media_type == "movie":
            data = get_movie_details(tmdb_id)
            title = data.get("title") or ""
        elif media_type == "tv":
            data = get_tv_details(tmdb_id)
            title = data.get("name") or ""
    except Exception:
        title = ""

    cache.set(cache_key, title, 60 * 60 * 6)  # 6 horas
    return title

User = get_user_model()

def public_profile(request, username: str): 
    profile_user = get_object_or_404(User, username=username)
    
    comments_qs = Comment.objects.filter(user=profile_user).order_by("-created_at")
    ratings_qs = Rating.objects.filter(user=profile_user).order_by("-updated_at")
    
    stats = {
        "comments_count": comments_qs.count(),
        "ratings_count": ratings_qs.count(),
    }

    page_comments = int(request.GET.get("page_comments", 1) or 1)
    page_ratings = int(request.GET.get("page_ratings", 1) or 1)

    comments_page = Paginator(comments_qs, 10).get_page(page_comments)
    ratings_page = Paginator(ratings_qs, 10).get_page(page_ratings)

    return render(request, "accounts/public_profile.html", {
        "profile_user": profile_user,
        "stats": stats,
        "comments_page": comments_page,
        "ratings_page": ratings_page,
    })
