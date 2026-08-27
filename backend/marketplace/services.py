from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError
from .models import Booking, Session

class Conflict(APIException):
    status_code = 409
    default_code = "conflict"

def active_booking_count(session_id):
    return Booking.objects.filter(session_id=session_id, status=Booking.Status.ACTIVE).count()

@transaction.atomic
def create_booking(*, session_id, user):
    # Lock must precede every time/capacity/duplicate decision.
    session = Session.objects.select_for_update().filter(pk=session_id).first()
    if not session or session.status != Session.Status.PUBLISHED:
        raise ValidationError({"session": "This session is unavailable."})
    if session.starts_at <= timezone.now():
        raise ValidationError({"session": "Bookings close when the session starts."})
    if Booking.objects.filter(session=session, user=user, status=Booking.Status.ACTIVE).exists():
        raise Conflict("You already have an active booking for this session.")
    if active_booking_count(session.id) >= session.capacity:
        raise Conflict("This session is fully booked.")
    try:
        return Booking.objects.create(session=session, user=user)
    except IntegrityError as exc:
        # Conditional unique index is a final database backstop for duplicate active bookings.
        raise Conflict("You already have an active booking for this session.") from exc

@transaction.atomic
def update_session(*, session_id, creator, values):
    session = Session.objects.select_for_update().filter(pk=session_id).first()
    if not session:
        return None
    if session.creator_id != creator.id:
        raise Conflict("You cannot modify another creator's session.")
    if "capacity" in values and values["capacity"] < active_booking_count(session.id):
        raise ValidationError({"capacity": "Capacity cannot be lower than the active booking count."})
    for field, value in values.items():
        setattr(session, field, value)
    session.save()
    return session

@transaction.atomic
def cancel_session(*, session_id, creator):
    session = Session.objects.select_for_update().filter(pk=session_id).first()
    if not session:
        return None
    if session.creator_id != creator.id:
        raise Conflict("You cannot delete another creator's session.")
    session.status = Session.Status.CANCELLED
    session.save(update_fields=["status", "updated_at"])
    return session
