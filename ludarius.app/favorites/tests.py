from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from favorites.models import Favorite


@override_settings(
    STORAGES={
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        }
    }
)
class FavoriteFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="favoriter",
            password="secret123",
        )
        self.client.login(username="favoriter", password="secret123")

    def test_toggle_favorite_movie_creates_and_removes_favorite(self):
        response = self.client.post(reverse("favorite_movie", args=[200]))
        self.assertRedirects(response, reverse("tmdb_movie_detail", args=[200]), fetch_redirect_response=False)
        self.assertTrue(Favorite.objects.filter(user=self.user, media_type="movie", tmdb_id=200).exists())

        self.client.post(reverse("favorite_movie", args=[200]))
        self.assertFalse(Favorite.objects.filter(user=self.user, media_type="movie", tmdb_id=200).exists())
