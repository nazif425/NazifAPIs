
from django.urls import path, include

def hello():
    return Response('Hi, welcome to my inventory.')

app_name = 'frontend'

urlpatterns = [
    # ...
    path('', hello)
]
""""""