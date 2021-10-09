# from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework.decorators import api_view
from .serializers import PropertySerializer
from .models import Property
from .responses import ErrorMsg, StatusMsg, SuccessMsg
from icecream import ic
# from functools import wraps


def custom_retrieve(serializer, request, pk, *args, **kwargs):
    model = serializer.Meta.model
    instance = model.objects.filter(pk=pk).first()
    if not instance:
        return Response(
            dict(status=StatusMsg.ERROR, error=ErrorMsg.NOT_FOUND), status=400
        )
    else:
        return Response(dict(status=StatusMsg.OK, data=serializer(instance).data))


def custom_create(serializer, request, *args, **kwargs):
    instance = serializer(data=request.data)
    if instance.is_valid():
        instance.save()
        return Response(
            dict(status=StatusMsg.OK, msg=SuccessMsg.CREATED, data=instance.data),
            status=201,
        )
    else:
        return Response(
            dict(status=StatusMsg.OK, error=ErrorMsg.VALIDATION, log=instance.errors),
            status=400,
        )


class CustomView(viewsets.ModelViewSet):
    """
        Customs Responses for Get, Post and Put methods
    """
    def create(self, request):
        return custom_create(self.serializer_class, request)

    def retrieve(self, request, pk):
        return custom_retrieve(self.serializer_class, request, pk)


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "email", "groups"]


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ["url", "name"]


class PropertyViewSet(CustomView):
    queryset = Property.objects.all().order_by("created_at")
    serializer_class = PropertySerializer
    VALID_STATUS = {"Active", "Inactive", "Removed"}

    def list(self, request):
        status = request.query_params.get("status")
        queryset = Property.objects.all().filter()
        if not status:
            data = queryset.all().order_by("created_at")
        else:
            data = queryset.filter(status=status)
        return Response(
            dict(status=StatusMsg.OK, count=len(data), data=data.values_list())
        )

    def partial_update(self, request, pk):
        ic(request)
        return Response()


# ic(PropertySerializer.Meta.model)
