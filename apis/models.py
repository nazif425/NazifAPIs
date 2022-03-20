from django.db import models
from django.conf import settings
from django.utils import timezone

ACTION = (
    ("DELETE RECORDS", "Delete account records"),
    ("UPDATE RECORDS", "Create account records"),
    ("SEND SMS", "Send SMS to buyers"),
    ("ADD CONTACT", "Add Contact"),
    ("RETRIEVE CONTACTS", "Retrieve contacts"),
    ("RETRIEVE ACCOUNT DETAILS", "Retrieve account details")
)

UNITS = (
    ("GRAMME","G"),
    ("KILOGRAMME","KG")
)

CURRENCIES = (
    ("NAIRA","Naira"),
    ("DOLLAR","Dollar")
)

# Create your models here.

class Device(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=30)
    date_created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return '%s device' % (self.user.get_full_name())

class OperationLog(models.Model):
    action = models.CharField(max_length=24, choices=ACTION, blank=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return '%s %s' % (self.user.get_full_name(), self.action)

class Contact(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30, blank=False)
    last_name = models.CharField(max_length=30, blank=False)
    phone_number = models.CharField(max_length=14, blank=False)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return '%s %s %s' % (self.id, self.first_name, self.last_name)

class Quantity(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    available_quantity = models.CharField(max_length=20, blank=False)
    unit = models.CharField(max_length=24, choices=UNITS, default=UNITS[0][0])
    last_modified = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return '%s: %s%s' % (self.device.user.get_full_name(), self.available_quantity, self.unit)

class Rate(models.Model):
    quantity = models.IntegerField(default=0)
    price = models.IntegerField(default=0)
    unit = models.CharField(max_length=10, choices=UNITS, default=UNITS[0][0])
    currency = models.CharField(max_length=24, choices=CURRENCIES, default=CURRENCIES[0][0])
    active_rate = models.BooleanField(default=False, null=False)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return '%s / %s%s' % (self.quantity, self.price, self.unit)