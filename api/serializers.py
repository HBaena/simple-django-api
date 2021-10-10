from rest_framework import serializers
from .models import Property, Activity
from datetime import timedelta
from django.utils.timezone import now


class PropertySerializer(serializers.ModelSerializer):
    VALID_STATUS = {'Active', 'Inactive', 'Removed'}

    class Meta:
        model = Property
        fields = (
            'id',
            'title',
            'address',
            'description',
            'created_at',
            'updated_at',
            'disabled_at',
            'status',
        )

    def validate_status(self, status):
        if status not in self.VALID_STATUS:
            raise serializers.ValidationError(
                {
                    'error': f'{status} is an invalid status value',
                    'valid values': list(self.VALID_STATUS)
                }
            )
        return status


class ActivitySerializer(serializers.ModelSerializer):
    class PropertySerializer_(serializers.ModelSerializer):
        class Meta:
            model = Property
            fields = (
                'id',
                'title',
                'address',
            )
    VALID_STATUS = {'Active', 'Done', 'Removed'}
    property = PropertySerializer_(read_only=True)

    class Meta:
        model = Activity
        fields = ('__all__')

    def validate_updated_at(self, updated_at):
        if updated_at:
            raise serializers.ValidationError(
                'The update date cannot be defined by the user')
        return None

    def validate_created_at(self, created_at):
        if created_at:
            raise serializers.ValidationError(
                'The creation date cannot be defined by the user')
        return None

    def validate_condition(self, condition):
        if condition:
            raise serializers.ValidationError(
                'The condition cannot be defined by the user')
        return None

    def validate_status(self, status):
        if status:
            raise serializers.ValidationError(
                'The status cannot be defined by the user')
        return None

    def validate(self, data):
        property_ = data.get('property')
        if not property_:
            raise serializers.ValidationError('Property is required')

        if property_.status != 'Active':
            raise serializers.ValidationError(
                'Selected property is Inactive or Removed')

        acitivities = Activity.objects.filter(
            property=property_
        ).filter(
            schedule__range=(
                data.get('schedule') - timedelta(hours=1),
                data.get('schedule') + timedelta(hours=1),
            )
        )
        if acitivities:
            raise serializers.ValidationError(
                {
                    'error': (
                        f'There is an activity scheduled at'
                        f'{acitivities[0].schedule} and it could cross. '
                        'Remember that activities can last up to an hour.'),
                    'acitivities': acitivities.values_list()

                }
            )

        if data.get('schedule') > now():  # Add condition
            data['condition'] = 'Pending'
        else:
            data['condition'] = 'Overdue'

        # data['status'] = 'Active'  # By default takes this value
        # data['created_at'] = data['updated_at'] = now()  # By default takes this value
        # raise serializers.ValidationError('FLAG')
        return data


# ic((serializers))
