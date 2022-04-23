from django.core.signing import Signer
from django.shortcuts import render, get_object_or_404
from rest_framework import generics, mixins, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from .serializers import DeviceSerializer, ContactSerializer, QuantitySerializer, RateSerializer, OperationLogSerializer
from . models import Device, Contact, Quantity, Rate, OperationLog
import os
# Create your views here.

def authenticate(self):
    deviceId = self.request.META.get('HTTP_DEVICE_ID')
    try:
        deviceInstance = Device.objects.get(device_id=deviceId)
    except Device.DoesNotExist:
        return None
    #Response(self.responseData, status=401)
    return deviceInstance

def authenticateAndreply(self):
    obj = authenticateDevice(self);
    if not obj:
        reply = "Could not authenticate device."
        self.responseData['reply'] += reply
    return obj;
        
class Initialize(APIView):
    def get(self, request, format=None):
        return Response({'content': 'welcome to IOT sheanut weighing device API'}, status=status.HTTP_200_OK)

class DeviceDetail(generics.RetrieveUpdateAPIView):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    
    def get_object(self):
        return authenticate(self);

class Status(APIView):
    def get(self, request, version="v1", format=None):
        device = authenticate(self);
        if not device:
            Response(status=401)
        quantityInstance = get_object_or_404(Quantity, device=device)
        quantitySerializer = QuantitySerializer(quantityInstance)
        
        rateInstance = get_object_or_404(Rate, active_rate=True)
        rateSerializer = RateSerializer(rateInstance)
        return Response({
            'quantity': quantitySerializer.data,
            'rate': rateSerializer.data
        }, status=status.HTTP_200_OK)

class ContactList(generics.ListCreateAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        device = authenticate(self);
        if not device:
            return Contact.objects.none
        queryset = self.queryset.filter(device=device)
        page = self.paginate_queryset(queryset)
        if page is not None:
            return page
        return queryset
    
    def perform_create(self, serializer):
        deviceId = self.request.META.get('HTTP_DEVICE_ID')
        device = get_object_or_404(Device, device_id=deviceId)
        serializer.save(device=device)

class ContactDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    
    def get_object(self):
        deviceId = self.request.META.get('HTTP_DEVICE_ID')
        return get_object_or_404(
            self.get_queryset(), 
            device__device_id=deviceId, 
            phone_number=self.kwargs['phoneNumber']
        )

class QuantityDetail(generics.RetrieveUpdateAPIView):
    queryset = Quantity.objects.all()
    serializer_class = QuantitySerializer
    
    def get_object(self):
        deviceId = self.request.META.get('HTTP_DEVICE_ID')
        return get_object_or_404(
            self.get_queryset(), 
            device__device_id=deviceId
        )
#generics.CreateAPIView, 
class Rate(generics.RetrieveAPIView):
    queryset = Rate.objects.all()
    serializer_class = RateSerializer
    
    def get_object(self):
        return get_object_or_404(Rate, active_rate=True)
    
    def perform_create(self, serializer):
        rateInstance = self.get_object()
        rateInstance.active_rate = False
        rateInstance.save()
        serializer.save()

class SmsRequest(APIView):
    cmd_list = {
        'register_device': 'wdadmin regdevice <firstname> <lastname> <phone number> <password>',
        'login_device': 'wdadmin logindevice <phone number> <password>',
        'add_contact': 'wd register <firstname> <lastname>',
        'admin_add_contact': 'wdadmin register <firstname> <lastname> <phone number> <password>'
    }
    responseData = {
        'reply': "Failed to complete your request. "
    }
    
    def post(self, request, *args, **kwargs):
        number = self.request.data.get("phone_number", "")
        self.responseData['phone_number'] = number
        command = self.request.data.get("message", "").lower().strip()
        
        if command and number:
            if command.startswith("wdadmin regdevice"):
                command = command.replace("wdadmin regdevice", "")
                return self.registerDevice(command)
            elif command.startswith("wdadmin logindevice"):
                command = command.replace("wdadmin logindevice", "")
                return self.loginDevice(command)
            elif command.startswith("wd register"):
                command = command.replace("wd register", "")
                return self.addContact(command)
            elif command.startswith("wdadmin register"):
                command = command.replace("wdadmin register", "")
                return self.addContact(command, admin=True)
            elif command.startswith("wd info"):
                return self.getInfo()
            else:
                self.responseData['reply'] = '\n'.join([value for value in self.cmd_list.values()])
                return Response(self.responseData, status=status.HTTP_404_OK)
        return Response(self.responseData, status=status.HTTP_400_BAD_REQUEST)
    
    def registerDevice(self, command):
        cmd_args = command.strip().split(' ')
        if len(cmd_args) == 4:
            keys = ["first_name", "last_name", "phone_number", "password"]
            data = {}
            for index, value in enumerate(cmd_args):
                data[keys[index]] = value
            data["first_name"] = data["first_name"].title()
            data["last_name"] = data["last_name"].title()
            #check if phone number already exists
            instance = Device.objects.get(phone_number=data["phone_number"])
            if instance:
                reply = "Sorry, the phone number %s is already registered to a device. To login send, \n %s" \
                    % (data["phone_number"], self.cmd_list.get("login_device", ""))
                self.responseData['reply'] = reply
                return Response(self.responseData, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = DeviceSerializer(data=data)
            if serializer.is_valid():
                instance = Device.objects.get(phone_number=data["phone_number"])
                self.responseData['reply'] = "device registration successful"
                self.responseData['data'] = DeviceSerializer(instance).data
                return Response(self.responseData, status=status.HTTP_201_CREATED)
        reply = "Invalid device registration command.\n" + self.cmd_list.get("register_device", "")
        self.responseData['reply'] = reply
        return Response(self.responseData, status=status.HTTP_400_BAD_REQUEST)
    
    def loginDevice(self, command):
        cmd_args = command.strip().split(' ')
        if len(cmd_args) == 2:
            keys = ["phone_number", "password"]
            data = {}
            
            # extract phone number and password from list cmd_args into data dict 
            for index, value in enumerate(cmd_args):
                data[keys[index]] = value
            
            # check if encrypt password and check if password and phone number exists in database
            signer = Signer()
            password = signer.sign(data['password'])
            instance = Device.objects.get(phone_number=data["phone_number"], password=password)
            if not instance:
                reply = "Sorry, the phone number or password incorrect %s. Try login again. \n %s" \
                    % (self.cmd_list.get("login_device", ""))
                self.responseData['reply'] = reply
                return Response(self.responseData, status=status.HTTP_400_BAD_REQUEST)
            
            self.responseData['reply'] = "device login successful"
            self.responseData['data'] = DeviceSerializer(instance).data
            return Response(self.responseData, status=status.HTTP_201_CREATED)
        reply = "Invalid device login command.\n" + self.cmd_list.get("login_device", "")
        self.responseData['reply'] = reply
        return Response(self.responseData, status=status.HTTP_400_BAD_REQUEST)

    def addContact(self, command, admin=False):
        cmd_args = command.strip().split(' ')
        deviceInstance = authenticateAndreply(self)
        if not deviceInstance:
            return Response(self.responseData, status=401)
        
        if len(cmd_args) == 2:
            cmd_args.append(self.responseData["phone_number"])
        elif len(cmd_args) == 4 and admin == True:
            # validate admin password
            adminPassword = cmd_args.pop() # get last element from list which is the password
            signer = Signer()
            password = signer.unsign(deviceInstance.password)
            if password != adminPassword:
                self.responseData['reply'] = "Password incorrect"
                return Response(self.responseData, status=status.HTTP_400_BAD_REQUEST)
            
        if len(cmd_args) == 3:
            keys = ["first_name", "last_name", "phone_number"]
            data = {}
            for index, value in enumerate(cmd_args):
                data[keys[index]] = value.title()
            data['notification'] = True
            data['device'] = deviceInstance
            
            #check if phone number already exists
            try:
                instance = Contact.objects.get(
                    phone_number=data['phone_number'],
                    device=deviceInstance
                )
            except Contact.DoesNotExist:
                reply = "Phone number %s is already registered." % (self.responseData["phone_number"])
                self.responseData['reply'] = reply
                return Response(self.responseData, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = ContactSerializer(data=data)
            if serializer.is_valid():
                self.responseData['reply'] = "Registration successful"
                return Response(self.responseData, status=status.HTTP_201_CREATED)
        reply = "Invalid registration command.\n %s\n%s" \
            % (self.cmd_list.get("add_contact", ""), self.cmd_list.get("admin_add_contact", "")) 
        self.responseData['reply'] = reply
        return Response(self.responseData, status=status.HTTP_400_BAD_REQUEST)
    
    def getInfo(self):
        # validate device id
        deviceInstance = authenticateAndreply(self)
        if not deviceInstance:
            return Response(self.responseData, status=401)
        
        try:
            quantityInstance = Quantity.objects.get(device=deviceId)
        except Quantity.DoesNotExist:
            return Response(self.responseData, status=status.HTTP_404_OK)
        
        quantity = QuantitySerializer(quantityInstance).data
        
        try:
            rateInstance = Rate.objects.get(active_rate=True)
        except Rate.DoesNotExist:
            return Response(self.responseData, status=status.HTTP_404_OK)
        
        rate = RateSerializer(rateInstance).data
        
        reply = "%s\n" % (deviceInstance.company_name)
        reply += "Shea nut is currently sold at the rate of %s per %s %s.\n" % (rate.price, rate.quantity, rate.unit)
        reply += "\nQuantity available: %s %s\n" % (quantity.available_quantity, quantity.unit)
        reply += "\nPrice: %s %s\n" % (str((quantity.available_quantity / rate.quantity) * rate.price), rate.currency)
        reply += "To purchase or make further enquiries, call %s" % (deviceInstance.contact_number)
        self.responseData['reply'] = reply
        
        return Response(self.responseData, status=status.HTTP_200_OK)
    