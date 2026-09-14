from rest_framework import serializers
from .models import TrajectoryFeature

class TrajectoryFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrajectoryFeature
        fields = '__all__'
        read_only_fields = fields
