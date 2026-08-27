import django.contrib.auth.models
from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):
    dependencies = [("marketplace", "0001_initial")]
    operations = [
        migrations.AlterModelManagers(name="user", managers=[("objects", django.contrib.auth.models.UserManager())]),
        migrations.AlterField(model_name="user", name="date_joined", field=models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
    ]
