from rest_framework import serializers
from .models import Tweet, DailySummary, Ping, PingReply
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='profile.get_role_display', read_only=True)
    role_id = serializers.CharField(source='profile.role', read_only=True)
    current_status = serializers.CharField(source='profile.current_status', read_only=True)
    last_status_update = serializers.DateTimeField(source='profile.last_status_update', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'role_id', 'current_status', 'last_status_update')

class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Tweet
        fields = ('id', 'user', 'content', 'created_at')

class DailySummarySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = DailySummary
        fields = ('id', 'user', 'target_date', 'summary_type', 'content', 'created_at')

class PingReplySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = PingReply
        fields = ('id', 'ping', 'user', 'reply', 'created_at')

class PingSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    replies = PingReplySerializer(many=True, read_only=True)
    expires_in_seconds = serializers.SerializerMethodField()

    class Meta:
        model = Ping
        fields = ('id', 'sender', 'question', 'created_at', 'expires_at', 'replies', 'expires_in_seconds')

    def get_expires_in_seconds(self, obj):
        from django.utils import timezone
        diff = obj.expires_at - timezone.now()
        return max(0, int(diff.total_seconds()))
