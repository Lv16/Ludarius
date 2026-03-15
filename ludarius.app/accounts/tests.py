from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from comments.models import Comment
from favorites.models import Favorite
from reviews.models import Rating


@override_settings(
    STORAGES={
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        }
    }
)
class AccountActivityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="profileuser",
            password="secret123",
        )
        self.client.login(username="profileuser", password="secret123")

    @patch("accounts.views.get_movie_details", return_value={"title": "Interstellar"})
    def test_my_activity_comments_tab_shows_resolved_title(self, _mock_title):
        Comment.objects.create(
            user=self.user,
            media_type="movie",
            tmdb_id=157336,
            text="Excelente",
        )

        response = self.client.get(reverse("my_activity"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Interstellar")
        self.assertContains(response, "Excelente")

    @patch("accounts.views.get_tv_details", return_value={"name": "The Bear"})
    def test_my_activity_ratings_tab_shows_resolved_title(self, _mock_title):
        Rating.objects.create(
            user=self.user,
            media_type="tv",
            tmdb_id=84773,
            score=9,
        )

        response = self.client.get(reverse("my_activity"), {"tab": "ratings"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Bear")
        self.assertContains(response, "9")

    @patch("accounts.views.get_movie_details", return_value={"title": "Interstellar"})
    def test_my_activity_favorites_tab_shows_resolved_title(self, _mock_title):
        Favorite.objects.create(
            user=self.user,
            media_type="movie",
            tmdb_id=157336,
        )

        response = self.client.get(reverse("my_activity"), {"tab": "favorites"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Interstellar")
        self.assertContains(response, "Favoritado em")

    @patch("accounts.views.get_movie_details", return_value={"title": "Interstellar"})
    def test_public_profile_shows_resolved_titles_and_favorites(self, _mock_title):
        Comment.objects.create(
            user=self.user,
            media_type="movie",
            tmdb_id=157336,
            text="Excelente",
        )
        Rating.objects.create(
            user=self.user,
            media_type="movie",
            tmdb_id=157336,
            score=10,
        )
        Favorite.objects.create(
            user=self.user,
            media_type="movie",
            tmdb_id=157336,
        )

        response = self.client.get(reverse("public_profile", args=[self.user.username]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Interstellar")
        self.assertContains(response, "10")
        self.assertContains(response, "Favoritos:")

    @patch("accounts.views.get_movie_details", return_value={"title": "Interstellar"})
    def test_title_resolution_fetches_unique_movie_once(self, mock_movie_details):
        cache.clear()
        Comment.objects.create(
            user=self.user,
            media_type="movie",
            tmdb_id=157336,
            text="Primeiro",
        )
        Rating.objects.create(
            user=self.user,
            media_type="movie",
            tmdb_id=157336,
            score=8,
        )

        self.client.get(reverse("my_activity"))
        self.client.get(reverse("my_activity"), {"tab": "ratings"})

        self.assertEqual(mock_movie_details.call_count, 1)
