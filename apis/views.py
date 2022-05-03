from django.core.signing import Signer
from django.shortcuts import render, get_object_or_404
from rest_framework import generics, mixins, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from .serializers import DeviceSerializer, ContactSerializer, QuantitySerializer, RateSerializer, OperationLogSerializer
from . models import Device, Contact, Quantity, Rate, OperationLog, UNITS
import os
# Create your views here.

def authenticate(self):
    deviceId = self.request.META.get('HTTP_DEVICE_ID', self.request.GET.get('key'))
    try:
        deviceInstance = Device.objects.get(device_id=deviceId)
    except Device.DoesNotExist:
        return None
    #Response(self.responseData, status=401)
    return deviceInstance

def authenticateAndreply(self):
    obj = authenticate(self);
    if not obj:
        reply = "Could not authenticate device."
        self.responseData['reply'] = reply
    return obj;

def dataInfo(deviceInstance, quantity, rate):
    reply = "{} \n".format(deviceInstance.company_name)
    reply += "Shea nut is currently sold at the rate of {} per {} {}.\n".format(rate.price, rate.quantity, rate.unit)
    reply += "\nQuantity available: {} {}\n".format(quantity.available_quantity, quantity.unit)
    reply += "\nPrice: {} {}\n".format(str((quantity.available_quantity / rate.quantity) * rate.price), rate.currency)
    if deviceInstance.contact_number:
        reply += "To purchase or make further enquiries, call {}".format(deviceInstance.contact_number)
    return reply

class Initialize(APIView):
    def get(self, request, format=None):
        return Response({'content': 'welcome to IOT sheanut weighing device API'}, status=status.HTTP_200_OK)

class DeviceDetail(generics.RetrieveUpdateAPIView):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    
    def get_object(self):
        return authenticate(self);

class StatusView(APIView):
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
    pagination_class = LimitOffsetPagination
    
    def list(self, request):
        #page = self.paginate_queryset(queryset)
        deviceInstance = authenticate(self)
        if not deviceInstance:
            return Response(status=401)
        
        try:
            quantity = Quantity.objects.get(device=deviceInstance)
        except Quantity.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        try:
            rate = Rate.objects.get(active_rate=True)
        except Rate.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        data = {}
        data['reply'] = dataInfo(deviceInstance, quantity, rate)
        contactList = self.filter_queryset(self.get_queryset()).filter(device=deviceInstance)
        if contactList.count() == 0:
            return Response({"detail": "contact list empty"}, status=status.HTTP_404_NOT_FOUND)
        page = self.paginate_queryset(contactList)
        if page is not None:
            contacts = self.serializer_class(page, many=True).data
            data['phone_numbers'] = [contact['phone_number'] for contact in contacts] # get list of phone number from  list of contact dict
            return self.get_paginated_response(data)
        data['phone_numbers'] = contactList.values_list('phone_number', flat=True)
        return Response(data)
        #return Contact.objects.none
        #if contactList == Contact.objects.none:
        #    Response( status=status.HTTP_200_OK), status=status.HTTP_200_OK
        
    
    def perform_create(self, serializer):
        deviceId = self.request.META.get('HTTP_DEVICE_ID', self.request.GET.get('key'))
        device = get_object_or_404(Device, device_id=deviceId)
        serializer.save(device=device)

class ContactDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    
    def get_object(self):
        deviceId = self.request.META.get('HTTP_DEVICE_ID', self.request.GET.get('key'))
        return get_object_or_404(
            self.get_queryset(), 
            device__device_id=deviceId, 
            phone_number=self.kwargs['phoneNumber']
        )

class QuantityView(APIView):
    queryset = Quantity.objects.all()
    serializer_class = QuantitySerializer
    
    def get_object(self):
        deviceId = self.request.META.get('HTTP_DEVICE_ID', self.request.GET.get('key'))
        return get_object_or_404(
            self.queryset, 
            device__device_id=deviceId
        )
    
    def get(self, request):
        serializer = self.serializer_class(self.get_object())
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        instance = self.get_object()
        data = {
            "available_quantity": request.data.get("available_quantity", 0.00),
            "unit": request.data.get("unit", UNITS[0][0])
        }
        newData = float(data["available_quantity"]) + float(instance.available_quantity)
        data["available_quantity"] = str(round(newData, 2))
        updateSerializer = self.serializer_class(instance, data=data)
        if updateSerializer.is_valid(): 
            updateSerializer.save()
            return Response(updateSerializer.data, status=status.HTTP_200_OK)
        return Response(updateSerializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        instance = self.get_object()
        instance.available_quantity = 0.00
        instance.save()
        return Response(status=204)

#  
class RateView(generics.CreateAPIView, generics.RetrieveAPIView):
    queryset = Rate.objects.all()
    serializer_class = RateSerializer
    
    def get_object(self):
        return get_object_or_404(self.queryset, active_rate=True)
    
    def perform_create(self, serializer):
        rateList = Rate.objects.filter(active_rate=True)
        if rateList.exists():
            rateInstance = rateList[0]
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
                return Response(self.responseData, status=status.HTTP_404_NOT_FOUND)
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
            
            if Device.objects.filter(phone_number=data["phone_number"]).exists():
                reply = "Sorry, the phone number %s is already registered to a device. To login send, \n %s" \
                    % (data["phone_number"], self.cmd_list.get("login_device", ""))
                self.responseData['reply'] = reply
                return Response(self.responseData, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = DeviceSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
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
            deviceList = Device.objects.filter(phone_number=data["phone_number"], password=password)
            if not deviceList.exists():
                reply = "Sorry, the phone number or password incorrect %s. Try login again. \n %s" \
                    % (self.cmd_list.get("login_device", ""))
                self.responseData['reply'] = reply
                return Response(self.responseData, status=status.HTTP_400_BAD_REQUEST)
                
            self.responseData['reply'] = "device login successful"
            self.responseData['data'] = DeviceSerializer(deviceList[0]).data
            return Response(self.responseData, status=status.HTTP_200_OK)
        reply = "Invalid device login command.\n" + self.cmd_list.get("login_device", "")
        self.responseData['reply'] = reply
        return Response(self.responseData, status=status.HTTP_400_BAD_REQUEST)

    def addContact(self, command, admin=False):
        cmd_args = command.strip().split(' ')
        deviceInstance = authenticateAndreply(self)
        if not deviceInstance:
            return Response(self.responseData, status=401)
        
        if len(cmd_args) == 2: # for customer register by customer
            cmd_args.append('0' + (self.responseData["phone_number"])[4:]) #remove +234
        elif len(cmd_args) == 4 and admin == True: # for customer register by admin 
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
            data['device'] = deviceInstance.pk
            
            #check if phone number already exists
            contactList = Contact.objects.filter(
                phone_number=data['phone_number'],
                device=deviceInstance
            )
            if contactList.exists():
                reply = "Phone number %s is already registered." % (data['phone_number'])
                self.responseData['reply'] = reply
                return Response(self.responseData, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = ContactSerializer(data=data)
            if serializer.is_valid():
                
                serializer.save()
                self.responseData['reply'] = "Registration successful"
                return Response(self.responseData, status=status.HTTP_201_CREATED)
            print(serializer.errors)
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
            quantity = Quantity.objects.get(device= deviceInstance)
        except Quantity.DoesNotExist:
            return Response(self.responseData, status=status.HTTP_404_NOT_FOUND)
        
        
        try:
            rate = Rate.objects.get(active_rate=True)
        except Rate.DoesNotExist:
            return Response(self.responseData, status=status.HTTP_404_NOT_FOUND)
        
        self.responseData['reply'] = dataInfo(deviceInstance, quantity, rate)
        
        return Response(self.responseData, status=status.HTTP_200_OK)
    