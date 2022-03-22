from django.shortcuts import render
from rest_framework import generics, mixins, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
# Create your views here.

class Initialize(APIView):
    def get(self, request, verstion="v1", format="json"):
        return Response({'content': 'welcome to IOT sheanut weighing device API'}, status=status.HTTP_200_OK)