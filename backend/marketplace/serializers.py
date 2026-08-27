from django.utils import timezone
from rest_framework import serializers
from .models import Booking, Session, User

class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "display_name", "avatar_url")

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "display_name", "avatar_url", "role")
        read_only_fields = ("id", "username", "role")

class SessionSerializer(serializers.ModelSerializer):
    creator = PublicUserSerializer(read_only=True)
    active_booking_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Session
        fields = ("id", "creator", "title", "description", "starts_at", "capacity", "status", "active_booking_count", "created_at", "updated_at")
        read_only_fields = ("id", "creator", "status", "active_booking_count", "created_at", "updated_at")

    def validate_starts_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("A session must start in the future.")
        return value

class BookingSerializer(serializers.ModelSerializer):
    session = SessionSerializer(read_only=True)
    class Meta:
        model = Booking
        fields = ("id", "session", "status", "booked_at")
