from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from reviews.models import Rating


@override_settings(
    STORAGES={
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        }
    }
)
class RatingFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="rater",
            password="secret123",
        )
        self.client.login(username="rater", password="secret123")

    def test_rate_movie_creates_and_updates_rating(self):
        response = self.client.post(reverse("rate_movie", args=[100]), {"score": "8"})
        self.assertRedirects(response, reverse("tmdb_movie_detail", args=[100]), fetch_redirect_response=False)

        rating = Rating.objects.get(user=self.user, media_type="movie", tmdb_id=100)
        self.assertEqual(rating.score, 8)

        cache.delete(f"rl:rating:{self.user.id}")
        self.client.post(reverse("rate_movie", args=[100]), {"score": "9"})
        rating.refresh_from_db()
        self.assertEqual(rating.score, 9)
