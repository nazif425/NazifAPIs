"""NazifAPIs URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView, TemplateView
from wagtail import urls as wagtail_urls 
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

""" """
urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html')),
    path('index.html', TemplateView.as_view(template_name='index.html')),
    path('productgrid.html', TemplateView.as_view(template_name='productgrid.html')),
    path('account.html', TemplateView.as_view(template_name='account.html')),
    path('profile.html', TemplateView.as_view(template_name='profile.html')),
    path('order.html', TemplateView.as_view(template_name='order.html')),
    path('login.html', TemplateView.as_view(template_name='login.html')),
    path('api/', include('apis.urls')),
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
#    path('rest-auth/', include('rest_auth.urls')),
#    path('rest-auth/registration/', include('rest_auth.registration.urls')),
    path('salesapi/', include('shop.urls')),
    path('cms/', include(wagtailadmin_urls)),
    path('documents/', include(wagtaildocs_urls)),
    path('pages/', include(wagtail_urls)),
    path('frontend', include('frontend.urls', namespace='frontend')),
] 

#urlpatterns = static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
#urlpatterns += staticfiles_urlpatterns()
urlpatterns +=  [
    re_path(r'^(?!/static/.*)(?P<path>.*\..*)$', RedirectView.as_view(url='/static/%(path)s')),
]
#urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
