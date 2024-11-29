import secrets
from django.core.signing import Signer
from rest_framework import serializers
from .models import Device, Contact, Rate, Quantity, OperationLog, Rate, Order

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
        fields = ["id","first_name","last_name","phone_number","notification"]


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

class OrderSerializer(serializers.ModelSerializer):
    contact = ContactSerializer()
    class Meta:
        model = Order
        fields = ["id","seller","contact","address","quantity","status","created"]
        extra_kwargs = {
            'seller': {'required': False},
            'contact': {'required': False},
            'created': {'read_only': True}
        }
    def validate_contact(self, contact):
        contact['phone_number'] = contact['phone_number'].strip()
        if not contact.get('phone_number', None):
            raise serializers.ValidationError('Phone number field is missing.')
        if contact.get('phone_number', '')[0] != '+':
            raise serializers.ValidationError('Phone number not provided in International format.')
        return contact
    
    def create(validated_data):
        contact_data = validated_data.pop('contact')
        device_pk = validated_data.pop('seller')
        
        device = Device.objects.filter(pk=device_pk)
        
        if device.exists():
            validated_data['seller'] = device[0]        
        else:
            raise serializers.ValidationError('Invalid seller id')
        
        contact = Contact.objects.filter(phone_number=contact_data.get('phone_number'))
        
        if contact.exists():
            validated_data['contact'] = contact[0]
        else:
            contact = Contact.objects.create(**contact_data)
            validated_data['contact'] = contact
        
        return Order.objects.create(**validated_data)
