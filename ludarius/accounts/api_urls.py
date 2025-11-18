from django.urls import path
from .api_views import RegisterAPIView
from .password_views import PasswordResetRequestView, PasswordResetConfirmView

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='api-register'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='api-password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='api-password-reset-confirm'),
]
