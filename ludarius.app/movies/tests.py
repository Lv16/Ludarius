from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from movies.models import Movie, MovieAvailability, StreamingPlatform


@override_settings(
    STORAGES={
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        }
    }
)
class MovieDomainTests(TestCase):
    def test_local_movie_detail_redirects_to_tmdb_detail_when_linked(self):
        movie = Movie.objects.create(title="Interstellar", tmdb_id=157336)

        response = self.client.get(reverse("movie_detail", args=[movie.id]))

        self.assertRedirects(response, reverse("tmdb_movie_detail", args=[movie.tmdb_id]))

    @patch("movies.views.get_movie_watch_providers")
    @patch("movies.views.get_movie_details")
    def test_tmdb_movie_detail_exposes_local_availabilities(self, mock_details, mock_providers):
        movie = Movie.objects.create(title="Interstellar", tmdb_id=157336)
        platform = StreamingPlatform.objects.create(name="Prime Video")
        MovieAvailability.objects.create(
            movie=movie,
            platform=platform,
            access_type="subscription",
            link="https://example.com/watch",
        )

        mock_details.return_value = {
            "tmdb_id": 157336,
            "title": "Interstellar",
            "original_title": "Interstellar",
            "overview": "Space travel.",
            "release_date": "2014-11-05",
            "rating": 8.7,
            "poster_url": "",
            "backdrop_url": "",
            "genres": ["Sci-Fi"],
            "runtime": 169,
        }
        mock_providers.return_value = {"link": "", "flatrate": [], "rent": [], "buy": []}

        response = self.client.get(reverse("tmdb_movie_detail", args=[157336]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Disponibilidade cadastrada no Ludarius")
        self.assertContains(response, "Prime Video")

    def test_unlinked_local_movie_detail_stays_local_only(self):
        movie = Movie.objects.create(title="Catalogo interno")

        response = self.client.get(reverse("movie_detail", args=[movie.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ainda nao foi vinculado ao catalogo TMDB")
        self.assertNotContains(response, "Adicionar comentario")
