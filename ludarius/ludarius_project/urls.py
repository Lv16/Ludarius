from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from accounts.token_views import (
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    LogoutAndBlacklistRefreshTokenForUserView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
    path('', include('mediaitems.urls')),
    path('api/accounts/', include('accounts.api_urls')),
    path('api/', include('mediaitems.api_urls')),
    path('accounts/', include('allauth.urls')),

    # JWT token endpoints (use cookie-based refresh storage)
    path('api/token/', CookieTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/logout/', LogoutAndBlacklistRefreshTokenForUserView.as_view(), name='token_logout'),
]
