from django.urls import path
from .api_views import MediaItemListCreateAPIView

urlpatterns = [
    path('mediaitems/', MediaItemListCreateAPIView.as_view(), name='api-mediaitem-list'),
]
