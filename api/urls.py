from django.urls import include, path
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r"properties", views.PropertyViewSet)
router.register(r"activities", views.ActivityViewSet)
# router.register(r'surveys', views.ListSurveysView)
# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path(
        "activities/<int:activity_id>/survey/",
        views.SurveyViewSet.as_view({"get": "retrieve"}),
    ),
    path("surveys/", views.SurveyViewSet.as_view({"get": "list"})),
]
