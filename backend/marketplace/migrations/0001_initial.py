import django.contrib.auth.validators
import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Q
import django.core.validators

class Migration(migrations.Migration):
    initial = True
    dependencies = [("auth", "0012_alter_user_first_name_max_length")]
    operations = [
        migrations.CreateModel(name="User", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("password", models.CharField(max_length=128, verbose_name="password")), ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
            ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
            ("username", models.CharField(error_messages={"unique": "A user with that username already exists."}, help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.", max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name="username")),
            ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")), ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
            ("email", models.EmailField(blank=True, max_length=254, verbose_name="email address")), ("is_staff", models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.", verbose_name="staff status")),
            ("is_active", models.BooleanField(default=True, help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.", verbose_name="active")),
            ("date_joined", models.DateTimeField(auto_now_add=True, verbose_name="date joined")),
            ("role", models.CharField(choices=[("USER", "User"), ("CREATOR", "Creator")], default="USER", max_length=10)), ("display_name", models.CharField(blank=True, max_length=80)), ("avatar_url", models.URLField(blank=True)),
            ("groups", models.ManyToManyField(blank=True, help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.", related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
            ("user_permissions", models.ManyToManyField(blank=True, help_text="Specific permissions for this user.", related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
        ], options={"verbose_name": "user", "verbose_name_plural": "users", "abstract": False}),
        migrations.CreateModel(name="Session", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("title", models.CharField(max_length=160)), ("description", models.TextField(max_length=3000)), ("starts_at", models.DateTimeField()), ("capacity", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])), ("status", models.CharField(choices=[("PUBLISHED", "Published"), ("CANCELLED", "Cancelled")], default="PUBLISHED", max_length=12)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("creator", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sessions", to="marketplace.user")),
        ]),
        migrations.CreateModel(name="Booking", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("status", models.CharField(choices=[("ACTIVE", "Active"), ("CANCELLED", "Cancelled")], default="ACTIVE", max_length=12)), ("booked_at", models.DateTimeField(auto_now_add=True)),
            ("session", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bookings", to="marketplace.session")), ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bookings", to="marketplace.user")),
        ]),
        migrations.AddConstraint(model_name="booking", constraint=models.UniqueConstraint(condition=Q(("status", "ACTIVE")), fields=("user", "session"), name="unique_active_booking_per_user_session")),
    ]
