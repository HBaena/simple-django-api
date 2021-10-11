# from django.shortcuts import render
from django.contrib.auth.models import User, Group
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.response import Response
# from rest_framework.views import APIView
# from rest_framework.decorators import api_view
from .serializers import PropertySerializer, ActivitySerializer, SurveySerializer
from .models import Property, Activity, Survey
from .responses import ErrorMsg, StatusMsg, SuccessMsg
# from icecream import ic
# from datetime import timedelta
# from datetime import datetime
from django.utils.timezone import now
from django.utils.timezone import datetime
from django.utils.timezone import timedelta
# from functools import wraps


def custom_retrieve(serializer, request, pk, *args, **kwargs):
    model = serializer.Meta.model
    instance = model.objects.filter(pk=pk).first()
    serializer_context = {
        'request': request,
    }
    if not instance:
        return Response(
            dict(status=StatusMsg.ERROR, error=ErrorMsg.NOT_FOUND), status=400
        )
    else:
        return Response(dict(status=StatusMsg.OK, data=serializer(instance, context=serializer_context).data))


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
            dict(status=StatusMsg.ERROR,
                 error=ErrorMsg.VALIDATION, log=instance.errors),
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
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class PropertyViewSet(CustomView):
    queryset = Property.objects.all().order_by('created_at')
    serializer_class = PropertySerializer

    def list(self, request):
        status = request.query_params.get('status')
        queryset = Property.objects.all().order_by('created_at')
        if status:
            queryset = queryset.filter(status=status)
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            dict(status=StatusMsg.OK, count=queryset.count(), data=serializer.data)
        )


class ActivityViewSet(CustomView):
    queryset = Activity.objects.all().order_by('created_at')
    serializer_class = ActivitySerializer

    # def retrieve(self, request, pk):

    # build_absolute_uri(obj.survey)

    def list(self, request, *args, **kwargs):
        queryset = Activity.objects.all()
        if not request.query_params:
            queryset = queryset.filter(
                schedule__range=(
                    now() - timedelta(days=7),
                    now() + timedelta(days=7),
                )
            )
        if (status := request.query_params.get('status')) and status != 'all':
            queryset = queryset.filter(status=status)

        if (condition := request.query_params.get('condition')) and condition != 'all':
            queryset = queryset.filter(condition=condition)

        if (schedule_from := request.query_params.get('schedule_from')):
            queryset = queryset.filter(
                schedule__gt=datetime.strptime(schedule_from, '%Y-%m-%dT%H:%M'))

        if (schedule_to := request.query_params.get('schedule_to')):
            queryset = queryset.filter(
                schedule__lt=datetime.strptime(schedule_to, '%Y-%m-%dT%H:%M'))

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            dict(status=StatusMsg.OK, count=queryset.count(), data=serializer.data)
        )        # super(ActivityViewSet, self).list(self, *args, **kwargs)


class SurveyViewSet(CustomView):
    queryset = Survey.objects.all().order_by('created_at')
    serializer_class = SurveySerializer
    lookup_url_kwarg = 'id'

    def list(self, request):
        queryset = Survey.objects.all().order_by('created_at')
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            dict(status=StatusMsg.OK, count=queryset.count(), data=serializer.data)
        )

    def retrieve(self, request, activity_id, *args, **kwargs):
        # from icecream import ic
        # ic(request)
        queryset = Survey.objects.filter(activity_id=activity_id).first()
        if not queryset:
            return Response(
                dict(status=StatusMsg.ERROR, error=ErrorMsg.NOT_FOUND), status=400
            )
        else:
            serializer = self.get_serializer(queryset)
            return Response(dict(status=StatusMsg.OK, data=serializer.data))
