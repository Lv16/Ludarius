from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import Notification
from comments.models import Comment
from favorites.models import Favorite
from movies.models import Movie


@override_settings(
    STORAGES={
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        }
    }
)
class CommentDomainTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(
            username="tester",
            password="secret123",
        )

    def test_local_movie_comment_uses_tmdb_id_when_movie_is_linked(self):
        movie = Movie.objects.create(title="Interstellar", tmdb_id=157336)
        self.client.login(username="tester", password="secret123")

        response = self.client.post(
            reverse("add_comment", args=[movie.id]),
            {"text": "Excelente filme"},
        )

        self.assertRedirects(response, reverse("tmdb_movie_detail", args=[157336]))
        comment = Comment.objects.get(user=self.user)
        self.assertEqual(comment.tmdb_id, 157336)
        self.assertEqual(comment.media_type, "movie")

    def test_comment_creates_notification_for_other_user_who_favorited_title(self):
        other_user = get_user_model().objects.create_user(
            username="other",
            password="secret123",
        )
        Favorite.objects.create(user=other_user, media_type="movie", tmdb_id=157336)
        self.client.login(username="tester", password="secret123")

        response = self.client.post(
            reverse("add_tmdb_movie_comment", args=[157336]),
            {"text": "Excelente filme"},
        )

        self.assertRedirects(response, reverse("tmdb_movie_detail", args=[157336]), fetch_redirect_response=False)
        self.assertTrue(
            Notification.objects.filter(
                user=other_user,
                actor=self.user,
                media_type="movie",
                tmdb_id=157336,
            ).exists()
        )
