from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model


class RegisterAPIView(APIView):
    """Registro básico de usuário (username + password + email)."""
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email', '')
        if not username or not password:
            return Response({'detail': 'username and password required'}, status=status.HTTP_400_BAD_REQUEST)
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            return Response({'detail': 'username exists'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=username, email=email, password=password)
        return Response({'id': user.id, 'username': user.username}, status=status.HTTP_201_CREATED)
