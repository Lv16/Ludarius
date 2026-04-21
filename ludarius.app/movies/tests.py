from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import AvailabilityAlert, MediaStatus, Notification
from comments.models import Comment
from favorites.models import Favorite
from movies.models import Movie, MovieAvailability, StreamingPlatform
from reviews.models import Rating


@override_settings(
    STORAGES={
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        }
    }
)
class MovieDomainTests(TestCase):
    def setUp(self):
        cache.clear()

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

    @patch("movies.views.search_multi")
    def test_home_search_filters_results_by_media_type_and_keeps_pagination(self, mock_search):
        mock_search.return_value = {
            "results": [
                {
                    "media_type": "movie",
                    "tmdb_id": 603,
                    "title": "Matrix",
                    "date": "1999-03-30",
                    "rating": 8.2,
                    "poster_url": "",
                },
                {
                    "media_type": "tv",
                    "tmdb_id": 1396,
                    "title": "Breaking Bad",
                    "date": "2008-01-20",
                    "rating": 9.4,
                    "poster_url": "",
                },
            ],
            "page": 2,
            "total_pages": 3,
        }

        response = self.client.get(reverse("home"), {"q": "matrix", "type": "movie", "page": "2"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["q"], "matrix")
        self.assertEqual(response.context["page"], 2)
        self.assertTrue(response.context["has_prev"])
        self.assertTrue(response.context["has_next"])
        self.assertEqual([item["title"] for item in response.context["results"]], ["Matrix"])
        mock_search.assert_called_once_with("matrix", page=2)

    @patch("movies.views.get_trending_tv")
    @patch("movies.views.get_trending_movies")
    def test_home_trending_feed_sorts_by_rating_and_filters_type(self, mock_movies, mock_tv):
        mock_movies.return_value = [
            {
                "tmdb_id": 157336,
                "title": "Interstellar",
                "release_date": "2014-11-05",
                "rating": 8.7,
                "poster_url": "",
            },
            {
                "tmdb_id": 603,
                "title": "Matrix",
                "release_date": "1999-03-30",
                "rating": 8.1,
                "poster_url": "",
            },
        ]
        mock_tv.return_value = [
            {
                "tmdb_id": 1396,
                "name": "Breaking Bad",
                "first_air_date": "2008-01-20",
                "rating": 9.4,
                "poster_url": "",
            }
        ]

        response = self.client.get(reverse("home"))
        movie_response = self.client.get(reverse("home"), {"type": "movie"})

        self.assertEqual(response.context["trending_feed"][0]["title"], "Breaking Bad")
        self.assertEqual([item["media_type"] for item in movie_response.context["trending_feed"]], ["movie", "movie"])

    @patch("movies.views.get_trending_tv", side_effect=Exception("tmdb unavailable"))
    @patch("movies.views.get_trending_movies", side_effect=Exception("tmdb unavailable"))
    def test_home_handles_trending_api_failures(self, _mock_movies, _mock_tv):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["trending_feed"], [])
        self.assertContains(response, "Nao foi possivel carregar o feed em alta agora.")

    @patch("movies.views.search_multi")
    def test_search_suggestions_returns_json_results_and_no_store_header(self, mock_search):
        mock_search.return_value = {
            "results": [
                {
                    "media_type": "movie",
                    "tmdb_id": 603,
                    "title": "Matrix",
                    "date": "1999-03-30",
                },
                {
                    "media_type": "tv",
                    "tmdb_id": 1396,
                    "title": "Breaking Bad",
                    "date": "2008-01-20",
                },
                {
                    "media_type": "movie",
                    "tmdb_id": None,
                    "title": "Invalid",
                    "date": "",
                },
            ]
        }

        response = self.client.get(reverse("search_suggestions"), {"q": "mat"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(
            response.json()["results"],
            [
                {
                    "title": "Matrix",
                    "label": "Filme",
                    "date": "1999-03-30",
                    "url": "/tmdb/movie/603/",
                },
                {
                    "title": "Breaking Bad",
                    "label": "Serie/Anime",
                    "date": "2008-01-20",
                    "url": "/tmdb/tv/1396/",
                },
            ],
        )

    @patch("movies.views.get_popular_tv", side_effect=Exception("tmdb unavailable"))
    @patch("movies.views.get_popular_movies", side_effect=Exception("tmdb unavailable"))
    def test_search_suggestions_falls_back_and_respects_type_filter(self, _mock_movies, _mock_tv):
        response = self.client.get(reverse("search_suggestions"), {"type": "tv"})
        results = response.json()["results"]

        self.assertEqual(response.status_code, 200)
        self.assertTrue(results)
        self.assertTrue(all(item["label"] == "Serie/Anime" for item in results))
        self.assertIn("Breaking Bad", [item["title"] for item in results])

    @patch("movies.views._build_media_card")
    @patch("movies.views.get_top_rated_tv", return_value=[{"tmdb_id": 1396, "name": "Breaking Bad"}])
    @patch("movies.views.get_top_rated_movies", return_value=[{"tmdb_id": 603, "title": "Matrix"}])
    @patch("movies.views.get_popular_tv", return_value=[{"tmdb_id": 66732, "name": "Stranger Things"}])
    @patch("movies.views.get_popular_movies", return_value=[{"tmdb_id": 157336, "title": "Interstellar"}])
    def test_explore_shows_tmdb_sections_and_internal_rankings(
        self,
        _mock_popular_movies,
        _mock_popular_tv,
        _mock_top_movies,
        _mock_top_tv,
        mock_media_card,
    ):
        user = get_user_model().objects.create_user(username="rankinguser")
        Favorite.objects.create(user=user, media_type="movie", tmdb_id=157336)
        Comment.objects.create(user=user, media_type="tv", tmdb_id=1396, text="Excelente")
        Rating.objects.create(user=user, media_type="movie", tmdb_id=603, score=10)
        MediaStatus.objects.create(user=user, media_type="tv", tmdb_id=66732, status=MediaStatus.Status.WANT)

        mock_media_card.side_effect = lambda media_type, tmdb_id: {
            "media_type": media_type,
            "tmdb_id": tmdb_id,
            "title": f"{media_type}-{tmdb_id}",
            "date": "",
            "poster_url": "",
        }

        response = self.client.get(reverse("explore"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["popular_movies"][0]["title"], "Interstellar")
        self.assertEqual(response.context["popular_tv"][0]["name"], "Stranger Things")
        self.assertEqual(response.context["top_movies"][0]["title"], "Matrix")
        self.assertEqual(response.context["top_tv"][0]["name"], "Breaking Bad")
        self.assertEqual(response.context["most_favorited"][0]["title"], "movie-157336")
        self.assertEqual(response.context["most_commented"][0]["title"], "tv-1396")
        self.assertEqual(response.context["top_rated"][0]["title"], "movie-603")
        self.assertEqual(response.context["most_wanted"][0]["title"], "tv-66732")

    @patch("movies.views.get_tv_watch_providers")
    @patch("movies.views.get_tv_details")
    def test_tmdb_tv_detail_exposes_authenticated_user_state_and_social_summary(self, mock_details, mock_providers):
        user = get_user_model().objects.create_user(username="tvuser")
        self.client.force_login(user)
        Favorite.objects.create(user=user, media_type="tv", tmdb_id=1396)
        Comment.objects.create(user=user, media_type="tv", tmdb_id=1396, text="Gosto muito")
        Rating.objects.create(user=user, media_type="tv", tmdb_id=1396, score=9)
        MediaStatus.objects.create(user=user, media_type="tv", tmdb_id=1396, status=MediaStatus.Status.WATCHING)
        AvailabilityAlert.objects.create(user=user, media_type="tv", tmdb_id=1396)

        mock_details.return_value = {
            "tmdb_id": 1396,
            "name": "Breaking Bad",
            "original_name": "Breaking Bad",
            "overview": "A chemistry teacher turns to crime.",
            "first_air_date": "2008-01-20",
            "last_air_date": "2013-09-29",
            "status": "Ended",
            "number_of_seasons": 5,
            "number_of_episodes": 62,
            "genres": ["Drama"],
            "rating": 9.4,
            "poster_url": "",
        }
        mock_providers.return_value = {
            "link": "https://example.com/providers",
            "flatrate": [{"name": "Netflix"}],
            "rent": [],
            "buy": [],
        }

        response = self.client.get(reverse("tmdb_tv_detail", args=[1396]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Breaking Bad")
        self.assertContains(response, "Netflix")
        self.assertContains(response, "Gosto muito")
        self.assertContains(response, "Sua nota atual: <strong>9</strong>", html=True)
        self.assertContains(response, "Seu status atual: <strong>Assistindo</strong>", html=True)
        self.assertContains(response, "Alerta de disponibilidade ativo para este titulo.")
        self.assertEqual(response.context["favorite_count"], 1)
        self.assertEqual(response.context["comment_count"], 1)
        self.assertEqual(response.context["status_counts"], {"watching": 1})

    def test_tmdb_image_proxy_rejects_invalid_size(self):
        response = self.client.get(reverse("tmdb_image_proxy", args=["bad", "poster.jpg"]))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b"invalid_size")

    @patch("movies.views.requests.get")
    def test_tmdb_image_proxy_returns_remote_image_with_cache_header(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.headers = {"Content-Type": "image/png"}
        mock_get.return_value.content = b"image-bytes"

        response = self.client.get(reverse("tmdb_image_proxy", args=["w500", "poster.png"]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertEqual(response["Cache-Control"], "public, max-age=86400")
        self.assertEqual(response.content, b"image-bytes")
        mock_get.assert_called_once_with(
            "https://image.tmdb.org/t/p/w500/poster.png",
            stream=True,
            timeout=8,
        )
