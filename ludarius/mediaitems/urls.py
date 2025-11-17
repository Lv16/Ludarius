from django.urls import path
from django.http import HttpResponse


def index(request):
    return HttpResponse('Ludarius - Welcome')


urlpatterns = [
    path('', index, name='home'),
]
