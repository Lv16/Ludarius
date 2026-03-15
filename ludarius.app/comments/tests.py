from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from comments.models import Comment
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
