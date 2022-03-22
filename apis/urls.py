from django.urls import include, path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import Initialize

urlpatterns = [
    path('', Initialize.as_view(), name='initialize')
]

urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json'])