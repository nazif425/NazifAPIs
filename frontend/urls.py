
from django.urls import path, include
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

app_name = 'frontend'

urlpatterns = [
    # ...
    path('', include(wagtail_urls))
]
