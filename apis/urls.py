from django.urls import include, path
from rest_framework.urlpatterns import format_suffix_patterns
from .views import Initialize, DeviceDetail, ContactList, ContactDetail, QuantityDetail, Rate, Status, SmsRequest

urlpatterns = [
    path('v1/initialize/', Initialize.as_view(), name='initialize'),
    path('v1/rate/', Rate.as_view(), name='rate-view'),
    path('v1/status/', Status.as_view(), name='status-view'),
    path('v1/device/', DeviceDetail.as_view(), name='device-detail'),
    path('v1/quantity/', QuantityDetail.as_view(), name='quantity-detail'),
    path('v1/smsrequest/', SmsRequest.as_view(), name='smsrequest-view'),
    path('v1/contact/', ContactList.as_view(), name='contact-list'),
    path('v1/contact/<str:phoneNumber>/', ContactDetail.as_view(), name='contact-detail')
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