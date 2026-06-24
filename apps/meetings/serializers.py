from rest_framework import serializers
from .models import Meeting, Verification, ActionLog
from apps.youth.serializers import YouthSerializer


class MeetingSerializer(serializers.ModelSerializer):
    youth_name = serializers.CharField(source='youth.full_name', read_only=True)
    rahbar_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    status_color = serializers.CharField(source='get_status_color', read_only=True)

    class Meta:
        model = Meeting
        fields = ['id', 'rahbar', 'rahbar_name', 'youth', 'youth_name', 'date',
                  'latitude', 'longitude', 'location_address', 'photo',
                  'photo_taken_at', 'status', 'status_display', 'status_color',
                  'notes', 'impossible_reason', 'created_at']
        read_only_fields = ['rahbar', 'status', 'created_at']

    def get_rahbar_name(self, obj):
        return obj.rahbar.get_full_name() if obj.rahbar else None


class MeetingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Meeting
        fields = ['youth', 'date', 'latitude', 'longitude', 'location_address',
                  'photo', 'photo_taken_at', 'notes', 'impossible_reason']

    def create(self, validated_data):
        request = self.context['request']
        validated_data['rahbar'] = request.user
        meeting = Meeting.objects.create(**validated_data)
        if validated_data.get('impossible_reason'):
            meeting.status = 'impossible'
            meeting.save()
        return meeting


class VerificationSerializer(serializers.ModelSerializer):
    meeting_detail = MeetingSerializer(source='meeting', read_only=True)

    class Meta:
        model = Verification
        fields = ['id', 'meeting', 'meeting_detail', 'verifier', 'status',
                  'rejection_reason', 'admin_status', 'admin_notes', 'verified_at', 'created_at']
        read_only_fields = ['verifier', 'created_at', 'verified_at']


class VerifyActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    reason = serializers.CharField(required=False, allow_blank=True)
