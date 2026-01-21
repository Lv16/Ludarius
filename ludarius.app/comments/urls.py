from django.urls import path
from . import views

urlpatterns = [
    path("movie/<int:movie_id>/comment/", views.add_comment, name="add_comment"),
]
