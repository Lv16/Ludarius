import re
from unittest.mock import patch

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from comments.models import Comment
from accounts.models import AvailabilityAlert, Collection, CollectionItem, MediaStatus, Notification
from favorites.models import Favorite
from reviews.models import Rating


class AuthenticationSecurityTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_login_requires_verified_email(self):
        get_user_model().objects.create_user(
            username="unverified",
            email="unverified@example.com",
            password="secret123",
        )

        response = self.client.post(
            reverse("login"),
            {"username": "unverified", "password": "secret123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_allows_verified_email(self):
        user = get_user_model().objects.create_user(
            username="verified",
            email="verified@example.com",
            password="secret123",
        )
        EmailAddress.objects.create(
            user=user,
            email=user.email,
            verified=True,
            primary=True,
        )

        response = self.client.post(
            reverse("login"),
            {"username": "verified", "password": "secret123"},
        )

        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)

    def test_login_rate_limits_failed_attempts(self):
        for _ in range(5):
            self.client.post(
                reverse("login"),
                {"username": "missing", "password": "wrong"},
            )

        response = self.client.post(
            reverse("login"),
            {"username": "missing", "password": "wrong"},
        )

        errors = response.context["form"].errors["__all__"].as_data()
        self.assertEqual(errors[0].code, "too_many_attempts")

    def test_logout_requires_post(self):
        response = self.client.get(reverse("logout"))

        self.assertEqual(response.status_code, 405)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_signup_sends_confirmation_email(self):
        response = self.client.post(
            reverse("account_signup"),
            {
                "email": "newuser@example.com",
                "username": "newuser",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("account_email_verification_sent"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("newuser@example.com", mail.outbox[0].to)
        self.assertTrue(EmailAddress.objects.filter(email="newuser@example.com", verified=False).exists())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_requires_verified_email(self):
        user = get_user_model().objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password="secret123",
        )

        response = self.client.post(reverse("password_reset"), {"email": user.email})

        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)
        response = self.client.post(reverse("password_reset"), {"email": user.email})

        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_magic_link_logs_in_verified_user_once(self):
        user = get_user_model().objects.create_user(
            username="magicuser",
            email="magic@example.com",
            password="secret123",
        )
        EmailAddress.objects.create(user=user, email=user.email, verified=True, primary=True)

        response = self.client.post(reverse("magic_link_request"), {"email": user.email})

        self.assertRedirects(response, reverse("magic_link_sent"))
        self.assertEqual(len(mail.outbox), 1)
        match = re.search(r"http://testserver(?P<path>/accounts/magic-login/\S+/)", mail.outbox[0].body)
        self.assertIsNotNone(match)

        response = self.client.get(match.group("path"))

        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)

        self.client.post(reverse("logout"))
        response = self.client.get(match.group("path"))

        self.assertRedirects(response, reverse("login"), fetch_redirect_response=False)
        self.assertNotIn("_auth_user_id", self.client.session)


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
    def test_my_activity_statuses_tab_shows_resolved_title(self, _mock_title):
        MediaStatus.objects.create(
            user=self.user,
            media_type="movie",
            tmdb_id=157336,
            status=MediaStatus.Status.WATCHED,
        )

        response = self.client.get(reverse("my_activity"), {"tab": "statuses"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Interstellar")
        self.assertContains(response, "Assistido")

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

    def test_update_media_status_creates_status(self):
        response = self.client.post(
            reverse("update_media_status", args=["movie", 157336]),
            {"status": MediaStatus.Status.WANT},
        )

        self.assertRedirects(response, reverse("tmdb_movie_detail", args=[157336]), fetch_redirect_response=False)
        self.assertTrue(
            MediaStatus.objects.filter(
                user=self.user,
                media_type="movie",
                tmdb_id=157336,
                status=MediaStatus.Status.WANT,
            ).exists()
        )

    def test_add_to_collection_creates_collection_item(self):
        collection = Collection.objects.create(user=self.user, title="Favoritos sci-fi")

        response = self.client.post(
            reverse("add_to_collection", args=["movie", 157336]),
            {"collection": collection.id},
        )

        self.assertRedirects(response, reverse("tmdb_movie_detail", args=[157336]), fetch_redirect_response=False)
        self.assertTrue(
            CollectionItem.objects.filter(
                collection=collection,
                media_type="movie",
                tmdb_id=157336,
            ).exists()
        )

    def test_user_search_finds_matching_username(self):
        response = self.client.get(reverse("user_search"), {"q": "profile"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "@profileuser")

    def test_mark_notifications_read_marks_existing_notifications(self):
        from accounts.models import Notification

        Notification.objects.create(user=self.user, verb="teste")

        response = self.client.post(reverse("notifications_read"))

        self.assertRedirects(response, reverse("notifications"), fetch_redirect_response=False)
        self.assertFalse(Notification.objects.filter(user=self.user, is_read=False).exists())

    def test_my_account_saves_profile_bio(self):
        response = self.client.post(
            reverse("my_account"),
            {"bio": "Gosto de ficcao cientifica", "save_profile": "1"},
        )

        self.assertRedirects(response, reverse("my_account"), fetch_redirect_response=False)
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.bio, "Gosto de ficcao cientifica")

    def test_private_collection_detail_requires_owner(self):
        other_user = get_user_model().objects.create_user(
            username="otheruser",
            password="secret123",
        )
        collection = Collection.objects.create(user=other_user, title="Privada", is_public=False)

        response = self.client.get(reverse("collection_detail", args=[collection.id]))

        self.assertRedirects(response, reverse("home"), fetch_redirect_response=False)

    def test_create_availability_alert_creates_alert(self):
        response = self.client.post(reverse("create_availability_alert", args=["movie", 157336]))

        self.assertRedirects(response, reverse("tmdb_movie_detail", args=[157336]), fetch_redirect_response=False)
        self.assertTrue(
            AvailabilityAlert.objects.filter(
                user=self.user,
                media_type="movie",
                tmdb_id=157336,
            ).exists()
        )

    @patch(
        "accounts.views.get_movie_details",
        return_value={"title": "Arrival", "poster_url": "", "tmdb_id": 329865},
    )
    def test_recommendations_page_shows_suggested_title(self, _mock_movie_details):
        other_user = get_user_model().objects.create_user(
            username="cinefriend",
            password="secret123",
        )
        Favorite.objects.create(user=self.user, media_type="movie", tmdb_id=157336)
        Favorite.objects.create(user=other_user, media_type="movie", tmdb_id=157336)
        Favorite.objects.create(user=other_user, media_type="movie", tmdb_id=329865)

        response = self.client.get(reverse("recommendations"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Arrival")

    def test_remove_availability_alert_deletes_existing_alert(self):
        alert = AvailabilityAlert.objects.create(user=self.user, media_type="movie", tmdb_id=157336)

        response = self.client.post(reverse("remove_availability_alert", args=[alert.id]))

        self.assertRedirects(response, reverse("my_account"), fetch_redirect_response=False)
        self.assertFalse(AvailabilityAlert.objects.filter(id=alert.id).exists())

    def test_my_account_shows_created_alerts(self):
        AvailabilityAlert.objects.create(user=self.user, media_type="tv", tmdb_id=1399)

        response = self.client.get(reverse("my_account"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "tv #1399")

    def test_notification_list_shows_availability_notification(self):
        Notification.objects.create(
            user=self.user,
            verb="novo titulo disponivel em Prime Video",
            media_type="movie",
            tmdb_id=157336,
        )

        response = self.client.get(reverse("notifications"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "novo titulo disponivel em Prime Video")
