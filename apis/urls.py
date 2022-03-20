from django.urls import include, path
from .views import Initialize

urlpatterns = [
    path('', Initialize.as_view(), name='initialize')
]
