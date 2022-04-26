import secrets
from django.core.signing import Signer
from rest_framework import serializers
from .models import Device, Contact, Rate, Quantity, OperationLog, Rate

class DeviceSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Device
        fields = ["device_id", "first_name", "last_name", "phone_number", "password"]
        read_only_fields = ["device_id"]
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def validate_phone_number(self, value):
        value = value.strip()
        if value:
            if Device.objects.filter(phone_number=value).exists():
                raise serializers.ValidationError('An account with this phone number already exists')
        return value
    
    def validate_password(self, value):
        value = value.strip()
        if value:
            signer = Signer()
            value = signer.sign(value)
        return value
    
    def create(self, validated_data):
        deviceInstance = super(DeviceSerializer, self).create(validated_data)
        deviceInstance.device_id = secrets.token_urlsafe(32)
        deviceInstance.save()
        quantityInstance = Quantity.objects.create(device=deviceInstance)
        quantityInstance.save()
        return deviceInstance

class ContactSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Contact
        fields = ["device","first_name","last_name","phone_number","notification"]
        extra_kwargs = {
            'device': {'required': False}
        }

class QuantitySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Quantity
        fields = ["available_quantity","unit"]

class RateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Rate
        fields = ["quantity","price","unit","currency","active_rate"]

class OperationLogSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = OperationLog
        fields = ["action","device"]