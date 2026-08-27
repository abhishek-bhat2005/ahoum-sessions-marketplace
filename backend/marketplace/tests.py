import threading
from datetime import timedelta

from django.db import connection, close_old_connections
from django.test import TransactionTestCase, TestCase, skipUnlessDBFeature
from django.urls import reverse
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken

from .models import Booking, Session, User

def auth(client, user):
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")

class BookingRulesTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user("creator", role=User.Role.CREATOR)
        self.user = User.objects.create_user("user")
        self.session = Session.objects.create(creator=self.creator, title="Test", description="Test", capacity=2, starts_at=timezone.now() + timedelta(hours=1))

    def test_duplicate_booking_rejected(self):
        from rest_framework.test import APIClient
        client = APIClient(); auth(client, self.user)
        url = f"/api/sessions/{self.session.id}/book/"
        self.assertEqual(client.post(url).status_code, 201)
        self.assertEqual(client.post(url).status_code, 409)
        self.assertEqual(Booking.objects.filter(status=Booking.Status.ACTIVE).count(), 1)

    def test_booking_after_start_rejected(self):
        from rest_framework.test import APIClient
        self.session.starts_at = timezone.now() - timedelta(seconds=1); self.session.save()
        client = APIClient(); auth(client, self.user)
        response = client.post(f"/api/sessions/{self.session.id}/book/")
        self.assertEqual(response.status_code, 400)

    def test_user_cannot_use_creator_endpoint_or_change_role(self):
        from rest_framework.test import APIClient
        client = APIClient(); auth(client, self.user)
        self.assertEqual(client.post("/api/creator/sessions/", {"title": "X"}, format="json").status_code, 403)
        self.assertEqual(client.patch("/api/profile/", {"role": "CREATOR"}, format="json").status_code, 200)
        self.user.refresh_from_db(); self.assertEqual(self.user.role, User.Role.USER)

    def test_creator_cannot_update_another_creators_session(self):
        from rest_framework.test import APIClient
        other = User.objects.create_user("other", role=User.Role.CREATOR)
        client = APIClient(); auth(client, other)
        response = client.patch(f"/api/creator/sessions/{self.session.id}/", {"title": "No"}, format="json")
        self.assertEqual(response.status_code, 409)

    def test_bad_access_token_is_unauthorized(self):
        from rest_framework.test import APIClient
        response = APIClient().get("/api/profile/", HTTP_AUTHORIZATION="Bearer invalid")
        self.assertEqual(response.status_code, 401)

@skipUnlessDBFeature("has_select_for_update")
class PostgreSQLFinalSeatConcurrencyTests(TransactionTestCase):
    """This test intentionally runs only where the DB supports row locks (PostgreSQL in CI/Compose)."""
    reset_sequences = True

    def setUp(self):
        self.creator = User.objects.create_user("creator", role=User.Role.CREATOR)
        self.first = User.objects.create_user("first")
        self.second = User.objects.create_user("second")
        self.session = Session.objects.create(creator=self.creator, title="Final seat", description="", capacity=1, starts_at=timezone.now() + timedelta(hours=1))

    def test_exactly_one_request_wins_final_seat(self):
        from rest_framework.test import APIClient
        barrier, statuses = threading.Barrier(2), []
        lock = threading.Lock()
        def attempt(user):
            close_old_connections()
            client = APIClient(); auth(client, user)
            barrier.wait(timeout=5)
            response = client.post(f"/api/sessions/{self.session.id}/book/")
            with lock: statuses.append(response.status_code)
            close_old_connections()
        threads = [threading.Thread(target=attempt, args=(user,)) for user in (self.first, self.second)]
        for thread in threads: thread.start()
        for thread in threads: thread.join(timeout=10)
        self.assertCountEqual(statuses, [201, 409])
        self.assertEqual(Booking.objects.filter(session=self.session, status=Booking.Status.ACTIVE).count(), 1)
