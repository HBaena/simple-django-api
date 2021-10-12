from rest_framework import serializers
from .models import Property, Activity, Survey
from datetime import timedelta
from django.utils.timezone import now
from django.utils.timezone import datetime
from django.utils.timezone import make_aware
from django.utils.timezone import get_current_timezone

from icecream import ic


class PropertySerializer(serializers.ModelSerializer):
    VALID_STATUS = {"Active", "Inactive", "Removed"}

    class Meta:
        model = Property
        fields = (
            "id",
            "title",
            "address",
            "description",
            "created_at",
            "updated_at",
            "disabled_at",
            "status",
        )

    def validate_status(self, status):
        if status not in self.VALID_STATUS:
            raise serializers.ValidationError(
                {
                    "error": f"{status} is an invalid status value",
                    "valid values": list(self.VALID_STATUS),
                }
            )
        return status


class SurveySerializer(serializers.ModelSerializer):
    class Meta:
        model = Survey
        fields = ("id", "answers", "created_at", "activity")

    # def validate(self, data):
    #     data['activity_id'] = self.initial_data.get('activity_id')
    #     return data


class ActivitySerializer(serializers.ModelSerializer):
    class PropertySerializer_(serializers.ModelSerializer):
        class Meta:
            model = Property
            fields = (
                "id",
                "title",
                "address",
            )

    VALID_STATUS = {"Active", "Done", "Removed"}
    property = PropertySerializer_(read_only=True)
    survey = serializers.SerializerMethodField("get_survey")

    class Meta:
        model = Activity
        fields = (
            "id",
            "property",
            "schedule",
            "title",
            "created_at",
            "updated_at",
            "status",
            "condition",
            "survey",
        )

    def get_survey(self, obj):
        """Generate survey url linked to the current activity

        Args:
            obj (Activity): Activity created in the View (have the request object)

        Returns:
            Activity: Absolute url of the survey (/api/activity/<activity_id>/survey/)
        """
        from django.contrib.sites.shortcuts import get_current_site

        request = self.context.get("request")
        domain = get_current_site(request).domain
        survey = Survey.objects.filter(activity_id=obj.pk).first()
        if survey:
            return f"{domain}/api/activities/{obj.pk}/survey/"  # Absolute
        return None
        # return f'{request.get_full_path()}survey/'  # Relative

    def reschedule(self, schedule):
        if not schedule:
            raise serializers.ValidationError({"error": "No schedule was recieved"})
        try:
            schedule = datetime.strptime(schedule, "%Y-%m-%dT%H:%M")
        except Exception as e:
            ic(e)
            raise serializers.ValidationError({"error": "DateTime format error"})

        if make_aware(schedule, get_current_timezone()) < now():
            raise serializers.ValidationError(
                {"error": "schedule date time must be greater than now"}
            )
        acitivities = (
            Activity.objects.exclude(status="cancelled")
            .filter(property=self.instance.property)
            .filter(
                schedule__range=(
                    schedule - timedelta(hours=1),
                    schedule + timedelta(hours=1),
                )
            )
        )
        if acitivities:
            raise serializers.ValidationError(
                {
                    "error": (
                        f"There is an activity scheduled at"
                        f"{acitivities[0].schedule} and it could cross. "
                        "Remember that activities can last up to an hour."
                    ),
                    "acitivities": acitivities.values_list(),
                }
            )
        self.instance.schedule = schedule
        self.instance.updated_at = now()
        self.instance.condition = "Pending"
        self.instance.save()

    def validate_updated_at(self, updated_at):
        if updated_at:
            raise serializers.ValidationError(
                "The update date cannot be defined by the user"
            )
        return None

    def validate_created_at(self, created_at):
        if created_at:
            raise serializers.ValidationError(
                "The creation date cannot be defined by the user"
            )
        return None

    def validate_condition(self, condition):
        if condition:
            raise serializers.ValidationError(
                "The condition cannot be defined by the user"
            )
        return None

    def validate_status(self, status):
        if status:
            raise serializers.ValidationError(
                "The status cannot be defined by the user"
            )
        return None

    def validate(self, data):
        data = self.initial_data
        property_ = data.get("property")
        data["property"] = property_
        if not property_:
            raise serializers.ValidationError("Property is required")

        if property_.status != "Active":
            raise serializers.ValidationError(
                "Selected property is Inactive or Removed"
            )
        schedule = datetime.strptime(data.get("schedule"), "%Y-%m-%dT%H:%M")
        acitivities = (
            Activity.objects.exclude(status="cancelled")
            .filter(property=property_)
            .filter(
                schedule__range=(
                    schedule - timedelta(hours=1),
                    schedule + timedelta(hours=1),
                )
            )
        )
        if acitivities:
            raise serializers.ValidationError(
                {
                    "error": (
                        f"There is an activity scheduled at"
                        f"{acitivities[0].schedule} and it could cross. "
                        "Remember that activities can last up to an hour."
                    ),
                    "acitivities": acitivities.values_list(),
                }
            )

        if make_aware(schedule, get_current_timezone()) > now():  # Add condition
            data["condition"] = "Pending"
        else:
            data["condition"] = "Overdue"

        return data
