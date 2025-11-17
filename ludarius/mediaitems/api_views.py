from rest_framework import generics, permissions
from .models import MediaItem
from .serializers import MediaItemSerializer


class MediaItemListCreateAPIView(generics.ListCreateAPIView):
    queryset = MediaItem.objects.all().order_by('-created_at')
    serializer_class = MediaItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
