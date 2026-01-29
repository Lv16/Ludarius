from django.urls import path
from . import views

urlpatterns = [
    path("my-account/", views.my_account, name="my_account"),
    path("my-activity/", views.my_activity, name="my_activity"),
]
