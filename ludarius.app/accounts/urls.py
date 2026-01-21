from django.urls import path
from . import views

urlpatterns = [
    path('my-account/', views.my_acconunt, name='my_account'),
]