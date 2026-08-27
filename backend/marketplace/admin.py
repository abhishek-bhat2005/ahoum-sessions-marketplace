from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Booking, Session, User

@admin.register(User)
class AhoumUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("Marketplace", {"fields": ("role", "display_name", "avatar_url")}),)
    list_display = ("username", "email", "role", "is_staff")

admin.site.register(Session)
admin.site.register(Booking)
