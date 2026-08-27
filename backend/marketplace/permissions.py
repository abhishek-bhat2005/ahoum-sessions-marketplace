from rest_framework.permissions import BasePermission
from .models import User

class IsCreator(BasePermission):
    message = "Creator enrollment is required for this action."
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.CREATOR)
