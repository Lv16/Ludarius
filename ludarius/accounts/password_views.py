from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import translation
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .throttles import LoginRateThrottle
from .throttles import PasswordResetRateThrottle
from django.shortcuts import redirect
from django.urls import reverse


class PasswordResetRequestView(APIView):
    """Request a password reset — sends an email with uid/token.

    Response is always 200 to avoid account enumeration.
    """
    permission_classes = (AllowAny,)

    throttle_classes = [PasswordResetRateThrottle]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'detail': 'email required'}, status=status.HTTP_400_BAD_REQUEST)

        User = get_user_model()
        users = User.objects.filter(email__iexact=email)
        # Always return 200 to avoid leaking whether email exists
        for user in users:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            # build a reset link — frontend will consume uid & token
            reset_path = f"/reset-password-confirm/?uid={uid}&token={token}"
            reset_url = request.build_absolute_uri(reset_path)
            subject = 'Ludarius — Password reset'

            # choose templates based on active language (LocaleMiddleware or ?lang=)
            # prefer explicit query param ?lang= over negotiated language
            req_lang = (request.GET.get('lang') or request.headers.get('Accept-Language'))
            if req_lang:
                # normalize to first 2 chars
                req_lang = req_lang.lower()[:2]
            else:
                req_lang = None

            if req_lang:
                lang = req_lang
            else:
                lang = translation.get_language() or settings.LANGUAGE_CODE

            if str(lang).startswith('en'):
                html_template = 'emails/password_reset_email_en.html'
                txt_template = 'emails/password_reset_email_en.txt'
            else:
                html_template = 'emails/password_reset_email.html'
                txt_template = 'emails/password_reset_email.txt'

            # render templates for html and plain text
            context = {'user': user, 'reset_url': reset_url}
            html_message = render_to_string(html_template, context)
            text_message = render_to_string(txt_template, context)

            email = EmailMultiAlternatives(subject, text_message, settings.DEFAULT_FROM_EMAIL, [user.email])
            email.attach_alternative(html_message, 'text/html')
            try:
                email.send(fail_silently=True)
            except Exception:
                # fail silently in dev
                pass

        return Response({'detail': 'If the email exists, a reset link was sent.'}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """Confirm password reset using uid and token and set new password."""
    permission_classes = (AllowAny,)
    def post(self, request):
        uidb64 = request.data.get('uid') or request.data.get('uidb64')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not uidb64 or not token or not new_password:
            return Response({'detail': 'uid, token and new_password required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            User = get_user_model()
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({'detail': 'Invalid uid'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({'detail': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'detail': 'Password has been reset.'}, status=status.HTTP_200_OK)

    def get(self, request):
        """Redirect to frontend UI for password reset, passing uid and token as query params."""
        uid = request.GET.get('uid') or request.GET.get('uidb64')
        token = request.GET.get('token')
        if not uid or not token:
            return Response({'detail': 'uid and token required'}, status=status.HTTP_400_BAD_REQUEST)

        frontend = getattr(settings, 'PASSWORD_RESET_FRONTEND_URL', 'http://localhost:3000/reset-password')
        # build redirect url
        redirect_url = f"{frontend}?uid={uid}&token={token}"
        return redirect(redirect_url)
