from rest_framework import serializers
from rest_framework.authtoken.models import Token
from .models import CustomUser, District, Organization


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = ['id', 'name']


class OrganizationSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source='district.name', read_only=True)

    class Meta:
        model = Organization
        fields = ['id', 'name', 'district', 'district_name', 'address']


class UserSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source='district.name', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'telegram_id', 'telegram_username',
                  'role', 'district', 'district_name', 'organization', 'organization_name', 'phone']


class BotAuthSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField()
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    username = serializers.CharField(required=False, allow_blank=True)
    secret_key = serializers.CharField()
