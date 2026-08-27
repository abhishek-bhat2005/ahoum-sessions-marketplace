import base64
import hashlib
import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Booking, Session, User
from .permissions import IsCreator
from .serializers import BookingSerializer, ProfileSerializer, SessionSerializer
from .services import cancel_session, create_booking, update_session

def annotated_sessions(queryset):
    from django.db.models import Count, Q
    return queryset.select_related("creator").annotate(active_booking_count=Count("bookings", filter=Q(bookings__status=Booking.Status.ACTIVE)))

@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def health(_request):
    return Response({"status": "ok"})

@api_view(["GET", "PATCH"])
def profile(request):
    if request.method == "PATCH":
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    return Response(ProfileSerializer(request.user).data)

class PublicSessionList(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SessionSerializer
    def get_queryset(self):
        return annotated_sessions(Session.objects.filter(status=Session.Status.PUBLISHED, starts_at__gt=timezone.now()).order_by("starts_at"))

class PublicSessionDetail(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SessionSerializer
    def get_queryset(self):
        return annotated_sessions(Session.objects.filter(status=Session.Status.PUBLISHED))

@api_view(["POST"])
def book(request, session_id):
    booking = create_booking(session_id=session_id, user=request.user)
    booking = Booking.objects.select_related("session", "session__creator").get(pk=booking.pk)
    return Response(BookingSerializer(booking).data, status=status.HTTP_201_CREATED)

class MyBookings(generics.ListAPIView):
    serializer_class = BookingSerializer
    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user).select_related("session", "session__creator").order_by("-session__starts_at")

class CreatorSessionList(generics.ListCreateAPIView):
    permission_classes = [IsCreator]
    serializer_class = SessionSerializer
    def get_queryset(self):
        return annotated_sessions(Session.objects.filter(creator=self.request.user).order_by("-starts_at"))
    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

@api_view(["GET", "PATCH", "DELETE"])
@permission_classes([IsCreator])
def creator_session(request, session_id):
    if request.method == "GET":
        session = annotated_sessions(Session.objects.filter(pk=session_id, creator=request.user)).first()
        if not session:
            raise NotFound("Session not found.")
        return Response(SessionSerializer(session).data)
    if request.method == "PATCH":
        existing = Session.objects.filter(pk=session_id).first()
        if not existing:
            raise NotFound("Session not found.")
        serializer = SessionSerializer(existing, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        mutable = {key: value for key, value in serializer.validated_data.items() if key in {"title", "description", "starts_at", "capacity"}}
        session = update_session(session_id=session_id, creator=request.user, values=mutable)
        if not session:
            raise NotFound("Session not found.")
        return Response(SessionSerializer(annotated_sessions(Session.objects.filter(pk=session.pk)).get()).data)
    session = cancel_session(session_id=session_id, creator=request.user)
    if not session:
        raise NotFound("Session not found.")
    return Response(status=status.HTTP_204_NO_CONTENT)

def set_refresh_cookie(response, refresh):
    response.set_cookie(settings.REFRESH_COOKIE_NAME, str(refresh), httponly=True, secure=settings.REFRESH_COOKIE_SECURE, samesite="Lax", path="/api/auth/")

def clear_refresh_cookie(response):
    response.delete_cookie(settings.REFRESH_COOKIE_NAME, path="/api/auth/")

@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def csrf(request):
    return Response({"csrfToken": get_token(request)})

@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def github_start(request):
    if not settings.GITHUB_CLIENT_ID:
        return Response({"detail": "GitHub OAuth is not configured."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    request.session["github_oauth"] = {"state": state, "verifier": verifier}
    request.session.modified = True
    params = {"client_id": settings.GITHUB_CLIENT_ID, "redirect_uri": settings.GITHUB_REDIRECT_URI, "state": state, "scope": "read:user user:email", "code_challenge": challenge, "code_challenge_method": "S256"}
    return Response({"authorization_url": "https://github.com/login/oauth/authorize?" + urlencode(params)})

@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def github_callback(request):
    failure = settings.OAUTH_FAILURE_URL
    received = request.query_params.get("state")
    expected = request.session.pop("github_oauth", None)
    if request.query_params.get("error"):
        return redirect(f"{failure}?{urlencode({'error': request.query_params.get('error_description', 'GitHub login was cancelled.')})}")
    if not expected or not received or not secrets.compare_digest(received, expected.get("state", "")):
        return redirect(f"{failure}?{urlencode({'error': 'Invalid or expired OAuth state. Please try again.'})}")
    try:
        token_response = requests.post("https://github.com/login/oauth/access_token", headers={"Accept": "application/json"}, data={"client_id": settings.GITHUB_CLIENT_ID, "client_secret": settings.GITHUB_CLIENT_SECRET, "code": request.query_params.get("code", ""), "redirect_uri": settings.GITHUB_REDIRECT_URI, "code_verifier": expected["verifier"]}, timeout=10)
        token_response.raise_for_status()
        github_token = token_response.json().get("access_token")
        if not github_token:
            raise ValueError("GitHub did not return an access token")
        profile_response = requests.get("https://api.github.com/user", headers={"Authorization": f"Bearer {github_token}", "Accept": "application/vnd.github+json"}, timeout=10)
        profile_response.raise_for_status()
        profile = profile_response.json()
    except (requests.RequestException, ValueError):
        return redirect(f"{failure}?{urlencode({'error': 'GitHub login failed. Please try again.'})}")
    username = profile.get("login")
    if not username:
        return redirect(f"{failure}?{urlencode({'error': 'GitHub returned no account name.'})}")
    user, _ = User.objects.get_or_create(username=username, defaults={"display_name": profile.get("name") or username, "avatar_url": profile.get("avatar_url", "")})
    refresh = RefreshToken.for_user(user)
    response = redirect(settings.OAUTH_SUCCESS_URL)
    set_refresh_cookie(response, refresh)
    return response

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@csrf_protect
def refresh(request):
    raw = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
    if not raw:
        return Response({"detail": "No refresh session."}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        token = RefreshToken(raw)
        user = User.objects.get(pk=token["user_id"])
        new_refresh = RefreshToken.for_user(user)
        token.blacklist()
        response = Response({"access": str(new_refresh.access_token), "user": ProfileSerializer(user).data})
        set_refresh_cookie(response, new_refresh)
        return response
    except (TokenError, User.DoesNotExist):
        response = Response({"detail": "Refresh session expired."}, status=status.HTTP_401_UNAUTHORIZED)
        clear_refresh_cookie(response)
        return response

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
@csrf_protect
def logout(request):
    raw = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
    if raw:
        try:
            RefreshToken(raw).blacklist()
        except TokenError:
            pass
    response = Response(status=status.HTTP_204_NO_CONTENT)
    clear_refresh_cookie(response)
    return response
