from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health),
    path("auth/csrf/", views.csrf), path("auth/github/start/", views.github_start), path("auth/github/callback/", views.github_callback), path("auth/refresh/", views.refresh), path("auth/logout/", views.logout),
    path("profile/", views.profile),
    path("sessions/", views.PublicSessionList.as_view()), path("sessions/<int:pk>/", views.PublicSessionDetail.as_view()), path("sessions/<int:session_id>/book/", views.book), path("bookings/", views.MyBookings.as_view()),
    path("creator/sessions/", views.CreatorSessionList.as_view()), path("creator/sessions/<int:session_id>/", views.creator_session),
]
