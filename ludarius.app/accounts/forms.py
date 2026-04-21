import hashlib

from allauth.account.models import EmailAddress
from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import AvailabilityAlert, Collection, MediaStatus, Profile


LOGIN_ATTEMPT_LIMIT = 5
LOGIN_ATTEMPT_TIMEOUT = 60 * 15


def _client_ip(request) -> str:
    if request is None:
        return "unknown"
    return request.META.get("REMOTE_ADDR") or "unknown"


def _login_attempt_cache_key(request, username: str) -> str:
    raw_key = f"{_client_ip(request)}:{(username or '').strip().lower()}"
    digest = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return f"login-attempts:{digest}"


class RateLimitedVerifiedEmailAuthenticationForm(AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        "too_many_attempts": _(
            "Muitas tentativas de login. Aguarde alguns minutos e tente novamente."
        ),
        "email_not_verified": _("Confirme seu e-mail antes de entrar."),
    }

    def clean(self):
        username = self.cleaned_data.get("username", "")
        cache_key = _login_attempt_cache_key(self.request, username)

        if cache.get(cache_key, 0) >= LOGIN_ATTEMPT_LIMIT:
            raise ValidationError(
                self.error_messages["too_many_attempts"],
                code="too_many_attempts",
            )

        try:
            cleaned_data = super().clean()
        except ValidationError:
            attempts = cache.get(cache_key, 0) + 1
            cache.set(cache_key, attempts, LOGIN_ATTEMPT_TIMEOUT)
            raise

        cache.delete(cache_key)
        return cleaned_data

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)

        if not EmailAddress.objects.filter(user=user, verified=True).exists():
            raise ValidationError(
                self.error_messages["email_not_verified"],
                code="email_not_verified",
            )


class MagicLinkRequestForm(forms.Form):
    email = forms.EmailField(label="E-mail")


class EmailConfirmationResendForm(forms.Form):
    email = forms.EmailField(label="E-mail")


class VerifiedEmailPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        for user in super().get_users(email):
            if EmailAddress.objects.filter(user=user, email__iexact=email, verified=True).exists():
                yield user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["bio"]


class MediaStatusForm(forms.Form):
    status = forms.ChoiceField(choices=MediaStatus.Status.choices, label="Status")


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ["title", "description", "is_public"]


class CollectionAddItemForm(forms.Form):
    collection = forms.ModelChoiceField(queryset=Collection.objects.none(), label="Colecao")

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["collection"].queryset = Collection.objects.filter(user=user).order_by("-created_at")


class AvailabilityAlertForm(forms.ModelForm):
    class Meta:
        model = AvailabilityAlert
        fields = []
