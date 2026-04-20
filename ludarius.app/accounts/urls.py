from django.urls import path
from . import views

urlpatterns = [
    path("logout/", views.logout_view, name="logout"),
    path("magic-link/", views.request_magic_link, name="magic_link_request"),
    path("magic-link/sent/", views.magic_link_sent, name="magic_link_sent"),
    path("magic-login/<str:token>/", views.magic_login, name="magic_login"),
    path("my-account/", views.my_account, name="my_account"),
    path("my-activity/", views.my_activity, name="my_activity"),
    path("notifications/", views.notifications_list, name="notifications"),
    path("notifications/read/", views.mark_notifications_read, name="notifications_read"),
    path("recommendations/", views.recommendations, name="recommendations"),
    path("search/", views.user_search, name="user_search"),
    path("collections/<int:collection_id>/", views.collection_detail, name="collection_detail"),
    path("collections/items/<int:item_id>/remove/", views.remove_collection_item, name="remove_collection_item"),
    path("tmdb/<str:media_type>/<int:tmdb_id>/status/", views.update_media_status, name="update_media_status"),
    path("tmdb/<str:media_type>/<int:tmdb_id>/collection/", views.add_to_collection, name="add_to_collection"),
    path("tmdb/<str:media_type>/<int:tmdb_id>/alert/", views.create_availability_alert, name="create_availability_alert"),
    path("alerts/<int:alert_id>/remove/", views.remove_availability_alert, name="remove_availability_alert"),
    path("u/<str:username>/", views.public_profile, name="public_profile"),
]
