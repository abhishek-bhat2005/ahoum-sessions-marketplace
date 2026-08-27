from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

class User(AbstractUser):
    class Role(models.TextChoices):
        USER = "USER", "User"
        CREATOR = "CREATOR", "Creator"
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    display_name = models.CharField(max_length=80, blank=True)
    avatar_url = models.URLField(blank=True)

class Session(models.Model):
    class Status(models.TextChoices):
        PUBLISHED = "PUBLISHED", "Published"
        CANCELLED = "CANCELLED", "Cancelled"
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sessions")
    title = models.CharField(max_length=160)
    description = models.TextField(max_length=3000)
    starts_at = models.DateTimeField()
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PUBLISHED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Booking(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        CANCELLED = "CANCELLED", "Cancelled"
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="bookings")
    session = models.ForeignKey(Session, on_delete=models.PROTECT, related_name="bookings")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE)
    booked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "session"], condition=Q(status="ACTIVE"), name="unique_active_booking_per_user_session")]
