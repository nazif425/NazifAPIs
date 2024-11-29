from django.db import models
from django.conf import settings
from django.utils import timezone

ACTION = (
    ("GET RECORDS", "Retrive account records"),
    ("UPDATE RECORDS", "Update account records"),
    ("ADD CONTACT", "Add Contact"),
    ("GET CONTACT", "Retrive Contact"),
    ("UPDATE CONTACT", "Update Contact"),
    ("DELETE CONTACT", "Delete Contact"),
    ("GET RATE", "Retrive Rate data"),
    ("UPDATE RATE", "Update Rate data"),
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

ORDER_STATUS = (
    ("PENDING", "Pending"),
    ("SOLD","Sold"),
    ("CANCELED", "Canceled")
)

# Create your models here.

class Device(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    device_id = models.CharField(max_length=64, blank=False)
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    phone_number = models.CharField(max_length=14, blank=False)
    password = models.CharField(max_length=255, blank=False)
    contact_number = models.CharField(max_length=14, blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return '%s %s device' % (self.first_name, self.last_name)

class OperationLog(models.Model):
    action = models.CharField(max_length=24, choices=ACTION, blank=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return '%s %s %s' % (self.first_name, self.last_name, self.action)

class Contact(models.Model):
    first_name = models.CharField(max_length=50, blank=False)
    last_name = models.CharField(max_length=50, blank=False)
    phone_number = models.CharField(max_length=14, blank=False)
    notification = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return '%s %s %s' % (self.id, self.first_name, self.last_name)
    def fullname(self):
        return '%s %s' % (self.first_name, self.last_name)

class Quantity(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    available_quantity = models.DecimalField(max_digits=9, decimal_places=2, default=0.00)
    unit = models.CharField(max_length=10, choices=UNITS, default=UNITS[0][0])
    last_modified = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return '%s %s: %s%s' % (self.first_name, self.last_name, self.available_quantity, self.unit)

class Rate(models.Model):
    quantity = models.DecimalField(max_digits=9, decimal_places=2, default=0.00)
    price = models.DecimalField(max_digits=9, decimal_places=2, default=0.00)
    unit = models.CharField(max_length=10, choices=UNITS, default=UNITS[0][0])
    currency = models.CharField(max_length=24, choices=CURRENCIES, default=CURRENCIES[0][0])
    active_rate = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return '%s / %s%s' % (self.quantity, self.price, self.unit)

class Order(models.Model):
    seller = models.ForeignKey(Device, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE)
    address = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=9, decimal_places=2, default=0.00)
    status = models.CharField(max_length=10, choices=ORDER_STATUS, default=ORDER_STATUS[0][0])
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return '%s: %s %s %s' % (self.contact.id, self.contact.firstname, self.quantity, self.status)

class Verify(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    link_code = models.CharField(max_length=6, blank=False)
    last_modified = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return '%s: %s' % (self.device.device_id, self.link_code)