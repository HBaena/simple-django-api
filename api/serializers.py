from rest_framework import serializers
from .models import Property


class PropertySerializer(serializers.HyperlinkedModelSerializer):
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
            'status')

    def validate_status(self, status):
        if status not in self.VALID_STATUS:
            raise serializers.ValidationError(f"Status need to be one of ({self.VALID_STATUS})")
        return status