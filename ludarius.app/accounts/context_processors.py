from .models import Notification


def notifications_context(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return {"notifications_unread_count": 0}
    return {
        "notifications_unread_count": Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).count()
    }
