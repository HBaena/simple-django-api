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

# from datetime import timedelta
# from datetime import datetime
from django.utils.timezone import now
from django.utils.timezone import datetime
from django.utils.timezone import timedelta

from functools import wraps
from icecream import ic


def validate_activity_exists():
    """Decorator for validating that the id received for activity is from a valid one

    Returns:
        Response: Some of these errors:
            ACTIVITY_REQUIRED
            NOT_FOUND
            CANCELLED
    """

    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            if not (pk := kwargs.get("pk")):
                return Response(
                    {"status": StatusMsg.ERROR, "error": ErrorMsg.ACTIVITY_REQUIRED}
                )
            context = {"request": kwargs.get("request")}
            activity = ActivitySerializer(
                Activity.objects.filter(pk=pk).first(), context=context
            )
            if not activity.instance:
                return Response(
                    {"status": StatusMsg.ERROR, "error": ErrorMsg.NOT_FOUND}
                )
            ic(activity.instance.status)
            if activity.instance.status == "cancelled":
                return Response(
                    {"status": StatusMsg.ERROR, "error": ErrorMsg.CANCELLED}
                )
            return fn(activity=activity, *args, **kwargs)

        return decorator

    return wrapper


def validate_empty_request():
    """Validate if the form data from the request is empty

    Returns:
        Response: EMPTY_REQUEST error
    """

    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            if not (request := kwargs.get("request")) or not request.data:
                return Response(
                    {"status": StatusMsg.ERROR, "error": ErrorMsg.EMPTY_REQUEST}
                )
            return fn(*args, **kwargs)

        return decorator

    return wrapper


def custom_retrieve(serializer, request, pk, *args, **kwargs):
    model = serializer.Meta.model
    instance = model.objects.filter(pk=pk).first()
    serializer_context = {
        "request": request,
    }
    if not instance:
        return Response(
            dict(status=StatusMsg.ERROR, error=ErrorMsg.NOT_FOUND), status=400
        )
    else:
        return Response(
            dict(
                status=StatusMsg.OK,
                data=serializer(instance, context=serializer_context).data,
            )
        )


def custom_create(serializer, request, *args, **kwargs):
    serializer_context = {
        "request": request,
    }
    instance = serializer(data=request.data, context=serializer_context)
    if instance.is_valid():
        instance.save()
        return Response(
            dict(status=StatusMsg.OK, msg=SuccessMsg.CREATED, data=instance.data),
            status=201,
        )
    else:
        return Response(
            dict(
                status=StatusMsg.ERROR, error=ErrorMsg.VALIDATION, log=instance.errors
            ),
            status=400,
        )


class CustomView(viewsets.ModelViewSet):
    """
    Customs Responses for Get, Post and Put methods
    """

    @validate_empty_request()
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

    def list(self, request):
        status = request.query_params.get("status")
        queryset = Property.objects.all().order_by("created_at")
        if status:
            queryset = queryset.filter(status=status)
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            dict(status=StatusMsg.OK, count=queryset.count(), data=serializer.data)
        )


class ActivityViewSet(CustomView):
    queryset = Activity.objects.all().order_by("created_at")
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
        if (status := request.query_params.get("status")) and status != "all":
            queryset = queryset.filter(status=status)

        if (condition := request.query_params.get("condition")) and condition != "all":
            queryset = queryset.filter(condition=condition)

        if schedule_from := request.query_params.get("schedule_from"):
            queryset = queryset.filter(
                schedule__gt=datetime.strptime(schedule_from, "%Y-%m-%dT%H:%M")
            )

        if schedule_to := request.query_params.get("schedule_to"):
            queryset = queryset.filter(
                schedule__lt=datetime.strptime(schedule_to, "%Y-%m-%dT%H:%M")
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            dict(status=StatusMsg.OK, count=queryset.count(), data=serializer.data)
        )  # super(ActivityViewSet, self).list(self, *args, **kwargs)

    @validate_empty_request()
    def create(self, request, *args, **kwargs):
        serializer_context = {
            "request": request,
        }
        data = request.data.dict()
        data["property"] = Property.objects.filter(pk=data.get("property")).first()
        instance = ActivitySerializer(data=data, context=serializer_context)
        if instance.is_valid():
            instance.save()
            return Response(
                dict(status=StatusMsg.OK, msg=SuccessMsg.CREATED, data=instance.data),
                status=201,
            )
        else:
            return Response(
                dict(
                    status=StatusMsg.ERROR,
                    error=ErrorMsg.VALIDATION,
                    log=instance.errors,
                ),
                status=400,
            )

    @validate_activity_exists()
    def destroy(self, request, pk=None, activity=None):
        activity.instance.cancel()
        return Response({"status": StatusMsg.OK, "msg": SuccessMsg.CANCELLED})

    @validate_empty_request()
    @validate_activity_exists()
    def partial_update(self, request, pk=None, activity=None):
        try:
            activity.reschedule(request.data.get("schedule"))
        except serializers.ValidationError as e:
            return Response(
                {
                    "status": StatusMsg.ERROR,
                    "error": ErrorMsg.VALIDATION,
                    "log": e.detail,
                }
            )
        return Response({"status": StatusMsg.OK, "msg": SuccessMsg.RESCHEDULE})


class SurveyViewSet(CustomView):
    queryset = Survey.objects.all().order_by("created_at")
    serializer_class = SurveySerializer
    lookup_url_kwarg = "id"

    def list(self, request):
        queryset = Survey.objects.all().order_by("created_at")
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            dict(status=StatusMsg.OK, count=queryset.count(), data=serializer.data)
        )

    @validate_activity_exists()
    def retrieve(self, request, pk, *args, **kwargs):
        # from icecream import ic
        queryset = Survey.objects.filter(activity_id=pk).first()
        if not queryset:
            return Response(
                dict(status=StatusMsg.ERROR, error=ErrorMsg.NOT_FOUND), status=400
            )
        else:
            serializer = self.get_serializer(queryset)
            return Response(dict(status=StatusMsg.OK, data=serializer.data))

    @validate_empty_request()
    @validate_activity_exists()
    def create(self, request, pk, activity):
        data = request.data
        data["activity"] = activity.instance.pk  # Or just pk

        context = {"request": request}
        survey = SurveySerializer(data=data, context=context)
        if survey.is_valid():
            survey.save()
            return Response(
                {"status": StatusMsg.OK, "msg": SuccessMsg.CREATED, "data": survey.data}
            )
        else:
            # raise serializers.ValidationError({'error': survey.errors})
            return Response(
                {
                    "status": StatusMsg.ERROR,
                    "msg": ErrorMsg.VALIDATION,
                    "log": survey.errors,
                }
            )

        return Response("hello")
