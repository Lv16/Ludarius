from django.conf import settings
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import throttling
from .throttles import LoginRateThrottle


class CookieTokenObtainPairView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    throttle_classes = [LoginRateThrottle]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh = response.data.get('refresh')
        if refresh:
            response.set_cookie(
                settings.JWT_COOKIE_NAME,
                refresh,
                httponly=settings.JWT_COOKIE_HTTPONLY,
                secure=settings.JWT_COOKIE_SECURE,
                samesite=settings.JWT_COOKIE_SAMESITE,
                path=settings.JWT_COOKIE_PATH,
            )
            # don't return refresh token in JSON body
            response.data.pop('refresh', None)
        return response


class CookieTokenRefreshView(TokenRefreshView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        # prefer explicit refresh in request body, fallback to cookie
        refresh = request.data.get('refresh') or request.COOKIES.get(settings.JWT_COOKIE_NAME)
        if not refresh:
            return Response({'detail': 'Refresh token not provided.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data={'refresh': refresh})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        response = Response(data, status=status.HTTP_200_OK)

        # if rotation is enabled, set new refresh token in cookie and remove it from body
        new_refresh = data.get('refresh')
        if new_refresh:
            response.set_cookie(
                settings.JWT_COOKIE_NAME,
                new_refresh,
                httponly=settings.JWT_COOKIE_HTTPONLY,
                secure=settings.JWT_COOKIE_SECURE,
                samesite=settings.JWT_COOKIE_SAMESITE,
                path=settings.JWT_COOKIE_PATH,
            )
            data.pop('refresh', None)
            response.data = data

        return response


class LogoutAndBlacklistRefreshTokenForUserView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        # accept refresh token in body or cookie
        refresh = request.data.get('refresh') or request.COOKIES.get(settings.JWT_COOKIE_NAME)
        if not refresh:
            response = Response({'detail': 'No refresh token provided.'}, status=status.HTTP_400_BAD_REQUEST)
            response.delete_cookie(settings.JWT_COOKIE_NAME, path=settings.JWT_COOKIE_PATH)
            return response

        try:
            token = RefreshToken(refresh)
            token.blacklist()
        except Exception:
            # if blacklist not enabled or token invalid, ignore but still clear cookie
            pass

        response = Response({'detail': 'Logged out.'}, status=status.HTTP_200_OK)
        response.delete_cookie(settings.JWT_COOKIE_NAME, path=settings.JWT_COOKIE_PATH)
        return response
