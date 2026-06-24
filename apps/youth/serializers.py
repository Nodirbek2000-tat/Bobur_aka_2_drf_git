from rest_framework import serializers
from .models import Youth


class YouthSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    rahbar_name = serializers.SerializerMethodField()
    yetakchi_name = serializers.SerializerMethodField()
    age = serializers.ReadOnlyField()
    total_meetings = serializers.ReadOnlyField()

    class Meta:
        model = Youth
        fields = ['id', 'full_name', 'birth_date', 'age', 'address', 'phone', 'category',
                  'organization', 'organization_name', 'rahbar', 'rahbar_name',
                  'yetakchi', 'yetakchi_name', 'notes', 'is_active', 'total_meetings', 'created_at']

    def get_rahbar_name(self, obj):
        return obj.rahbar.get_full_name() if obj.rahbar else None

    def get_yetakchi_name(self, obj):
        return obj.yetakchi.get_full_name() if obj.yetakchi else None
