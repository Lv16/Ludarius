from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import AvailabilityAlert, Notification
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

    def test_provider_list_shows_platforms_with_catalog_totals(self):
        movie = Movie.objects.create(title="Interstellar", tmdb_id=157336)
        platform = StreamingPlatform.objects.create(name="Prime Video")
        MovieAvailability.objects.create(
            movie=movie,
            platform=platform,
            access_type="subscription",
            link="https://example.com/watch",
        )

        response = self.client.get(reverse("provider_list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Prime Video")

    def test_provider_detail_filters_by_access_type(self):
        movie = Movie.objects.create(title="Interstellar", tmdb_id=157336)
        platform = StreamingPlatform.objects.create(name="Prime Video")
        MovieAvailability.objects.create(
            movie=movie,
            platform=platform,
            access_type="subscription",
            link="https://example.com/subscription",
        )
        MovieAvailability.objects.create(
            movie=movie,
            platform=platform,
            access_type="rent",
            link="https://example.com/rent",
        )

        response = self.client.get(reverse("provider_detail", args=[platform.id]), {"access_type": "rent"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Aluguel")
        self.assertContains(response, "https://example.com/rent")
        self.assertNotContains(response, "https://example.com/subscription")

    def test_new_movie_availability_creates_notification_for_matching_alert(self):
        user = get_user_model().objects.create_user(username="alertuser", password="secret123")
        movie = Movie.objects.create(title="Interstellar", tmdb_id=157336)
        platform = StreamingPlatform.objects.create(name="Prime Video")
        AvailabilityAlert.objects.create(user=user, media_type="movie", tmdb_id=157336)

        MovieAvailability.objects.create(
            movie=movie,
            platform=platform,
            access_type="subscription",
            link="https://example.com/watch",
        )

        self.assertTrue(
            Notification.objects.filter(
                user=user,
                media_type="movie",
                tmdb_id=157336,
                verb="novo titulo disponivel em Prime Video",
            ).exists()
        )
