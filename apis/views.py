from django.core.signing import Signer
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from rest_framework import generics, mixins, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination
from .serializers import DeviceSerializer, ContactSerializer, QuantitySerializer, RateSerializer, OperationLogSerializer, OrderSerializer
from . models import Device, Contact, Quantity, Rate, OperationLog, Order, ORDER_STATUS, UNITS, Verify
from pathlib import Path
import os, environ, random
import africastalking


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
# reading .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# Configure africatalking API access
AFTK_USERNAME = env("AFTK_USERNAME", default="")
AFTK_API_KEY = env("AFTK_API_KEY", default="")

africastalking.initialize(AFTK_USERNAME, AFTK_API_KEY )
sms = africastalking.SMS

#
def get_link_code(request, *args, **kwargs):
    link_code = ''
    for i in range(0,6):
        n = random.randint(0,9)
        link_code = link_code + str(n)
    
    return JsonResponse({
        "link_code": link_code
    }, status=status.HTTP_200_OK)

#
def login_status(request, link_code):
    #data = json.loads(request.body)
    
    verifyList = Verify.objects.filter(link_code=link_code)
    if verifyList.exists():
        verifyInstance = verifyList[0]
        
        reply = "Device login successful"
        phone_number = verifyInstance.device.phone_number
        try:
            print(reply)
            response = sms.send(reply, [phone_number])
            print(response)
        except Exception as e:
            print(f'An error occured while sending sms: {e}')
        
        return JsonResponse({
            'device_id': verifyInstance.device.device_id,
            'login': True,
        }, status=status.HTTP_200_OK)

    return JsonResponse({
        'login': False,
    }, status=status.HTTP_200_OK)

def update_contacts(request):
    deviceId = request.META.get('HTTP_DEVICE_ID', request.GET.get('key'))
    print(deviceId)
    phone_number = []
    try:
        deviceInstance = Device.objects.get(device_id=deviceId)
    except Device.DoesNotExist:
        return JsonResponse({"reply": "Device unauthorized"}, status=401)
    
    reply = ''
    try:
        rate = Rate.objects.get(active_rate=True)
        reply = "Shea nut selling rate: {} per {} {}.\n".format(rate.price, rate.quantity, rate.unit)
    except Rate.DoesNotExist:
        print('failed to get rate instance')
        #return Response(self.responseData, status=status.HTTP_404_NOT_FOUND)
    #reply = dataInfo(deviceInstance, quantity, rate)
    
    if deviceInstance.company_name:
        reply += "{} \n".format(deviceInstance.company_name)
    else:
        reply += "{} {} \n".format(deviceInstance.first_name, deviceInstance.last_name)
        
    quantityList = Quantity.objects.filter(device=deviceInstance)
    if quantityList.exists():
        quantity = quantityList[0]
        reply += "Quantity available: {} {}\n".format(quantity.available_quantity, quantity.unit)
        #reply += "Price: {} {}\n".format(str(round((quantity.available_quantity / rate.quantity) * rate.price, 2)), rate.currency)
    reply += "Contact No.: {}\n\n".format(deviceInstance.phone_number)
    # reply += "\nTo make an order, reply with the following: wd makeorder <the_quantity>".format(deviceInstance.phone_number)
    
    # get and send sms to contacts
    success_counter = 0
    contactList = Contact.objects.all()
    if contactList.exists():
        for contact in contactList:
            phone_number.append(contact.phone_number)
    try:
        print(reply)
        response = sms.send(reply, phone_number)
        print(response)
        
        if response:
            for recipient in response.Recipients:
                if recipient.status == 'Success' and recipient.statusCode == 101:
                    success_counter += 1
    except Exception as e:
        print(f'An error occured while sending sms: {e}')
    
    return JsonResponse({
        "total_sent": success_counter,
        "total_contacts": len(phone_number),
    }, status=status.HTTP_200_OK)

def authenticate(self):
    deviceId = self.request.META.get('HTTP_DEVICE_ID', self.request.GET.get('key'))
    try:
        deviceInstance = Device.objects.get(device_id=deviceId)
    except Device.DoesNotExist:
        return None
    #Response(self.responseData, status=401)
    return deviceInstance

def authenticateAndreply(self):
    obj = authenticate(self)
    if not obj:
        reply = "Could not authenticate device."
        self.responseData['reply'] = reply
    return obj

def is_authenticated(request, *args, **kwargs):
    deviceId = request.META.get('HTTP_DEVICE_ID', request.GET.get('key'))
    try:
        deviceInstance = Device.objects.get(device_id=deviceId)
    except Device.DoesNotExist:
        return JsonResponse({'authenticated': False}, status=status.HTTP_200_OK)
    return JsonResponse({'authenticated': True}, status=status.HTTP_200_OK)
    

def dataInfo(deviceInstance, quantity, rate):
    pass

class Initialize(APIView):
    def get(self, request, format=None):
        return Response({'content': 'welcome to IOT sheanut weighing device API'}, status=status.HTTP_200_OK)

class DeviceDetail(generics.RetrieveUpdateAPIView):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    
    def get_object(self):
        return authenticate(self)

class StatusView(APIView):
    def get(self, request, version="v1", format=None):
        device = authenticate(self)
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
        """
        try:
            quantity = Quantity.objects.get(device=deviceInstance)
        except Quantity.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        """
        try:
            rate = Rate.objects.get(active_rate=True)
        except Rate.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        data = {}
        data['reply'] = dataInfo(deviceInstance, quantity, rate)
        contactList = self.filter_queryset(self.get_queryset()) #.filter(device=deviceInstance)
        if contactList.count() == 0:
            return Response({"detail": "Contact list empty"}, status=status.HTTP_404_NOT_FOUND)
        page = self.paginate_queryset(contactList)
        if page is not None:
            contacts = self.serializer_class(page, many=True).data
            data['phone_numbers'] = [contact['phone_number'] for contact in contacts] # get list of phone number from  list of contact dict
            data['total_results'] = len(data['phone_numbers'])
            return self.get_paginated_response(data)
        data['phone_numbers'] = contactList.values_list('phone_number', flat=True)
        data['total_results'] = len(data['phone_numbers'])
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
    sms = africastalking.SMS
    phone_number = []
    
    cmd_list = {
        'info': 'wd info',
        'register_device': 'wd regdevice <firstname> <lastname> <password>',
        'login_device': 'wd logindevice <link code> <password>',
        'add_contact': 'wd register <firstname> <lastname>',
        'admin_add_contact': 'wd register <firstname> <lastname> <phone number>',
        'order_list': 'wd order',
        'confirm_order': 'wd confirmorder <order_id>',
        'cancel_order': 'wd cancelorder <order_id>',
        'make_order': 'wd makeorder <quantity>'
    }
    responseData = {
        'reply': "Failed to complete your request. "
    }
    
    def post(self, request, *args, **kwargs):
        self.phone_number = [self.request.data.get("from", "")]
        command = self.request.data.get("text", "").lower().strip()
        
        if command and self.phone_number:
            if command.startswith("regdevice"):
                command = command.replace("regdevice", "")
                return self.registerDevice(command)
            elif command.startswith("logindevice"):
                command = command.replace("logindevice", "")
                return self.loginDevice(command)
            elif command.startswith("register"):
                command = command.replace("register", "")
                return self.addContact(command)
            elif command.startswith("info"):
                return self.getInfo()
            elif command.startswith("order"):
                return self.getOrders()
            elif command.startswith("confirmorder"):
                command = command.replace("confirmorder", "")
                return self.updateOrderStatus(action=confirm)
            elif command.startswith("cancelorder"):
                command = command.replace("cancelorder", "")
                return self.updateOrderStatus(action=cancel)
            elif command.startswith("makeorder"):
                command = command.replace("makeorder", "")
                return self.makeOrder()
            else:
                guide = '\n'.join([value for value in self.cmd_list.values()])
                try:
                    response = self.sms.send(guide, self.phone_number)
                    print(response)
                except Exception as e:
                    print(f'An error occured while sending sms: {e}')
        return Response(status=status.HTTP_200_OK)
    
    def registerDevice(self, command):
        cmd_args = command.strip().split(' ')

        if len(cmd_args) == 3:
            data = {
                "first_name": cmd_args[0].title(), 
                "last_name": cmd_args[1].title(), 
                "password": cmd_args[2],
                "phone_number": self.phone_number[0]
            }

            #check if phone number already exists
            if Device.objects.filter(phone_number=data["phone_number"]).exists():
                reply = "Sorry, the phone number %s is already registered to a device. To login send, \n %s" \
                    % (data["phone_number"], self.cmd_list.get("login_device", ""))
                try:
                    print(reply)
                    response = self.sms.send(reply, self.phone_number)
                    print(response)
                except Exception as e:
                    print(f'An error occured while sending sms: {e}')
                return Response(status=status.HTTP_200_OK)
            
            serializer = DeviceSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                reply = "Device registration successful"
                try:
                    print(reply)
                    response = self.sms.send(reply, self.phone_number)
                    print(response)
                except Exception as e:
                    print(f'An error occured while sending sms: {e}')
                return Response(status=status.HTTP_200_OK)
                
        reply = "Invalid registration command.\n" + self.cmd_list.get("register_device", "")
        try:
            print(reply)
            response = self.sms.send(reply, self.phone_number)
            print(response)
        except Exception as e:
            print(f'An error occured while sending sms: {e}')
        return Response(status=status.HTTP_200_OK)
    
    def loginDevice(self, command):
        cmd_args = command.strip().split(' ')

        if len(cmd_args) == 2:
            cmd_args = self.phone_number + cmd_args
        
        if len(cmd_args) == 3:
            data = {
                "phone_number": cmd_args[0],
                "link_code": cmd_args[1],
                "password": cmd_args[2]
            }

            print(data)
            deviceList = Device.objects.filter(phone_number=data["phone_number"])
            
            if not deviceList.exists():
                reply = "Sorry, the phone number is incorrect or not registered. Check and try again. \n %s" \
                    % (self.cmd_list.get("login_device", ""))
                try:
                    print(reply)
                    response = self.sms.send(reply, data["phone_number"])
                    print(response)
                except Exception as e:
                    print(f'An error occured while sending sms: {e}')
                return Response(status=status.HTTP_200_OK)
            
            deviceInstance = deviceList[0]
            signer = Signer()
            if signer.unsign(deviceInstance.password) != data['password']:
                reply = "Sorry, password is incorrect. Check and try again. \n %s" \
                    % (self.cmd_list.get("login_device", ""))
                try:
                    print(reply)
                    response = self.sms.send(reply, self.phone_number)
                    print(response)
                except Exception as e:
                    print(f'An error occured while sending sms: {e}')
                return Response(status=status.HTTP_200_OK)
            verifyInstance = Verify.objects.create(device=deviceInstance, link_code=data['link_code'])
            verifyInstance.save()
            print("Verify code on Device to complete login")
            return Response(status=status.HTTP_200_OK)
        
        # Invalid command
        reply = "Invalid login command.\n" + self.cmd_list.get("login_device", "")
        try:
            print(reply)
            response = self.sms.send(reply, self.phone_number)
            print(response)
        except Exception as e:
            print(f'An error occured while sending sms: {e}')
        return Response(status=status.HTTP_200_OK)
    
    def addContact(self, command, admin=False):
        cmd_args = command.strip().split(' ')
        admin = True
        
        # for registration by customer
        if len(cmd_args) == 2:
            admin = False
            cmd_args.append(self.phone_number[0])
            # cmd_args.append('0' + (self.responseData["phone_number"])[4:]) #remove +234
        
        # for customer registration by admin
        if admin == True:
            # Verify if performed by admin
            deviceList = Device.objects.filter(phone_number=self.phone_number[0])
            if not deviceList.exists():
                reply = "Sorry, the phone No. %s does not have the permission perform" \
                    "the given operation. Try again with an adminstrative number." \
                    % (self.phone_number[0])
                try:
                    print(reply)
                    response = self.sms.send(reply, self.phone_number)
                    print(response)
                except Exception as e:
                    print(f'An error occured while sending sms: {e}')
                return Response(status=status.HTTP_200_OK)
        
        if len(cmd_args) == 3:
            data = {
                "first_name": cmd_args[0].title(),
                "last_name": cmd_args[1].title(),
                "phone_number": cmd_args[2]
            }
            
            #check if phone number already exists
            contactList = Contact.objects.filter(
                phone_number=data['phone_number']
            )
            if contactList.exists():
                reply = "Phone number %s is already registered." % (data['phone_number'])
                try:
                    print(reply)
                    response = self.sms.send(reply, self.phone_number)
                    print(response)
                except Exception as e:
                    print(f'An error occured while sending sms: {e}')
                return Response(status=status.HTTP_200_OK)
            
            # Create new contact
            serializer = ContactSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                reply = "Registration successful"
                try:
                    print(reply)
                    response = self.sms.send(reply, self.phone_number)
                    print(response)
                except Exception as e:
                    print(f'An error occured while sending sms: {e}')
                return Response(status=status.HTTP_200_OK)
        
        # Invalid command
        reply = "Invalid registration command.\n %s\n%s" \
            % (self.cmd_list.get("add_contact", ""), self.cmd_list.get("add_contact", ""))
        try:
            print(reply)
            response = self.sms.send(reply, self.phone_number)
            print(response)
        except Exception as e:
            print(f'An error occured while sending sms: {e}')
        return Response(status=status.HTTP_200_OK)
    
    def getInfo(self):
        reply = ''
        try:
            rate = Rate.objects.get(active_rate=True)
            reply = "Shea nut selling rate: {} per {} {}.\n".format(rate.price, rate.quantity, rate.unit)
        except Rate.DoesNotExist:
            print('failed to get rate instance')
            #return Response(self.responseData, status=status.HTTP_404_NOT_FOUND)
        #reply = dataInfo(deviceInstance, quantity, rate)
        
        deviceList = Device.objects.all()
        
        for deviceInstance in deviceList:
            
            if deviceInstance.company_name:
                reply += "{} \n".format(deviceInstance.company_name)
            else:
                reply += "{} {} \n".format(deviceInstance.first_name, deviceInstance.last_name)
            
            quantityList = Quantity.objects.filter(device=deviceInstance)
            if quantityList.exists():
                quantity = quantityList[0]
                reply += "Quantity available: {} {}\n".format(quantity.available_quantity, quantity.unit)
                #reply += "Price: {} {}\n".format(str(round((quantity.available_quantity / rate.quantity) * rate.price, 2)), rate.currency)
            reply += "Contact No.: {}\n\n".format(deviceInstance.phone_number)
            # reply += "\nTo make an order, reply with the following: wd makeorder <the_quantity>".format(deviceInstance.phone_number)
        try:
            print(reply)
            response = self.sms.send(reply, self.phone_number)
            print(response)
        except Exception as e:
            print(f'An error occured while sending sms: {e}')
        return Response(status=status.HTTP_200_OK)
    
    def getOrders(self):
        deviceInstance = authenticateAndreply(self)
        if not deviceInstance:
            return Response(self.responseData, status=401)
        
        # verify admin
        if deviceInstance.phone_number != self.responseData["phone_number"]:
            reply = "Sorry, the phone No. %s does not have the permission perform" \
                "the given operation. Try again with an adminstrative number." \
                % (self.responseData["phone_number"])
            self.responseData['reply'] = reply
            return Response(self.responseData, status=403)
        
        try:
            rate = Rate.objects.get(active_rate=True)
        except Rate.DoesNotExist:
            return Response(self.responseData, status=status.HTTP_404_NOT_FOUND)
        
        orders = Order.objects.filter(seller=deviceInstance, status=ORDER_STATUS[0][0])
        if not orders.exists():
            reply = "No pending orders available."
            self.responseData['reply'] = reply
            return Response(self.responseData, status=status.HTTP_200_OK)
        
        reply = "Order list\n"
        for order in orders:
            reply += '{}: {}\n'.format(order.id, order.contact.fullname())
            reply += '{} {} ({} {})\n'.format(
                order.quantity,
                rate.unit,
                str(round((order.quantity / rate.quantity) * rate.price)),
                rate.currency
            )
            reply += order.contact.phone_number
            reply += "\n____"
        
        self.responseData['reply'] = reply
        self.responseData['order_list'] = True
        return Response(self.responseData, status=status.HTTP_200_OK)
    
    def updateOrderStatus(action=None):
        cmd_args = command.strip().split(' ')
        
        deviceInstance = authenticateAndreply(self)
        if not deviceInstance:
            return Response(self.responseData, status=401)
        
        # verify admin
        if deviceInstance.phone_number != self.responseData["phone_number"]:
            reply = "Sorry, the phone No. %s does not have the permission perform" \
                "the given operation. Try again with an adminstrative number." \
                % (self.responseData["phone_number"])
            self.responseData['reply'] = reply
            return Response(self.responseData, status=403)
        
        order_id = None
        if len(cmd_args) == 1:
            order_id = cmd_args[0]
        
        orders = Order.objects.filter(id=order_id) 
        if not orders.exists():
            reply = "Invalid order command.\n %s\n%s" \
                % ( self.cmd_list.get("confirm_order", ""), self.cmd_list.get("cancel_order", "")) 
            self.responseData['reply'] = reply
            return Response(self.responseData, status=status.HTTP_400_BAD_REQUEST)
        
        order = orders[0]
        # update status of order to confirm
        if action == 'confirm':
            # make substract new order from the available quantity
            try:
                quantity = Quantity.objects.get(device= deviceInstance)
            except Quantity.DoesNotExist:
                return Response(self.responseData, status=status.HTTP_404_NOT_FOUND)
            newData = float(quantity.available_quantity) - float(order.quantity)
            if newData >= 0:
                quantity.available_quantity = round(newData, 2)
                quantity.save()
                order.status = ORDER_STATUS[1][0]
            else:
                reply = 'available quantity is insufficient to complete order'
                self.responseData['reply'] = reply
                return Response(self.responseData, status=status.HTTP_400_BAD_REQUEST)
        # update status of order to cancel
        elif action == 'cancel':
            order.status = ORDER_STATUS[2][0]
        order.save()
        
        self.responseData['reply'] = "Order status successful"
        self.responseData['order_update'] = True
        return Response(self.responseData, status=status.HTTP_200_OK)
    
    def makeOrder(self):
        cmd_args = command.strip().split(' ')
        
        deviceInstance = authenticateAndreply(self)
        if not deviceInstance:
            return Response(self.responseData, status=401)
        
        # verify admin
        if deviceInstance.phone_number != self.responseData["phone_number"]:
            reply = "Sorry, the phone No. %s does not have the permission perform" \
                "the given operation. Try again with an adminstrative number." \
                % (self.responseData["phone_number"])
            self.responseData['reply'] = reply
            return Response(self.responseData, status=403)
        
        quantity = None
        if len(cmd_args) != 1:
            reply = "Invalid order command.\n %s\n%s" \
                % ( self.cmd_list.get("make_order", "")) 
            self.responseData['reply'] = reply
            return Response(self.responseData, status=status.HTTP_400_BAD_REQUEST)
        
        quantity = cmd_args[0]
        
        try:
            quantityInstance = Quantity.objects.get(device= deviceInstance)
        except Quantity.DoesNotExist:
            return Response(self.responseData, status=status.HTTP_404_NOT_FOUND)
        
        if float(quantityInstance.available_quantity) < float(quantity):
            reply = 'available quantity is insufficient to complete order'
            self.responseData['reply'] = reply
            return Response(self.responseData, status=status.HTTP_400_BAD_REQUEST)
        data = {
            'seller': deviceInstance.id,
            'contact': {
                'first_name': 'user',
                'last_name': 'user',
                'phone_number': self.responseData["phone_number"]
            },
            'quantity': str(quantity)
        }
        
        serializer = OrderSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            self.responseData['reply'] = "Request is being processed.\n" \
                "For further inquires contact %s" % (deviceInstance.phone_number)
            self.responseData['order_request'] = True
            return Response(self.responseData, status=status.HTTP_200_OK)
        return Response(self.responseData, status=status.HTTP_400_BAD_REQUEST)

class Login(APIView):
    def post(self, request, *args, **kwargs):
        
        deviceInstance = authenticate(self)
        if deviceInstance:
            return Response({'error': "Device already logged in."}, status=status.HTTP_400_BAD_REQUEST)
        
        # check if encrypt password and check if password and phone number exists in database
        signer = Signer()
        password = signer.sign(request.data.get('password', ''))
        phone_number = request.data.get('phone_number', '')
        deviceList = Device.objects.filter(phone_number=phone_number, password=password)
        
        if not deviceList.exists():
            return Response(
                {'error': "Sorry, the phone number or password incorrect"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(
            DeviceSerializer(deviceList[0]).data, 
            status=status.HTTP_200_OK
        )

class Order(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
