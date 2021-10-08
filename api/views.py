from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework import serializers
from rest_framework import viewsets
from .serializers import PropertySerializer
from .models import Property


# Create your views here.

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all().order_by('created_at')
    serializer_class = PropertySerializer