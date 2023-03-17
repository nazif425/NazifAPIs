from django.urls import include, path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import Initialize, DeviceDetail, ContactList, ContactDetail, QuantityView, RateView, StatusView, SmsRequest, Login, is_authenticated

urlpatterns = [
    path('v1/initialize/', Initialize.as_view(), name='initialize'),
    path('v1/rate/', RateView.as_view(), name='rate-view'),
    path('v1/status/', StatusView.as_view(), name='status-view'),
    path('v1/device/', DeviceDetail.as_view(), name='device-detail'),
    path('v1/quantity/', QuantityView.as_view(), name='quantity-view'),
    path('v1/smsrequest/', SmsRequest.as_view(), name='smsrequest-view'),
    path('v1/contact/', ContactList.as_view(), name='contact-list'),
    path('v1/contact/<str:phoneNumber>/', ContactDetail.as_view(), name='contact-detail'),
    path('v1/login/', Login.as_view(), name='login'),
    path('v1/is_authenticated/', is_authenticated, name='is_authenticated'),
    path('v1/order/', ContactList.as_view(), name='order-list'),
]

"""
urlpatterns = [
    
    path('v1/request/', RateView.as_view(), name='rate-view'),
    path('v1/device/', DeviceCreate.as_view(), name='device-create'),
    ,
    
    path('v1/device/<str:deviceId>/quantity/', QuantityDetail.as_view(), name='quantity-detail'),
    
]
"""
#urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json'])