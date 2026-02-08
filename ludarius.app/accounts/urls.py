from django.urls import path
from . import views

urlpatterns = [
    path("logout/", views.logout_view, name="logout"),
    path("my-account/", views.my_account, name="my_account"),
    path("my-activity/", views.my_activity, name="my_activity"),
    path("u/<str:username>/", views.public_profile, name="public_profile"),
]
