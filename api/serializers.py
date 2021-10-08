from rest_framework import serializers
from .models import Property


class PropertySerializer(serializers.HyperlinkedModelSerializer):
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
