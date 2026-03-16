import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_rename_indexes"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AvailabilityAlert",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("media_type", models.CharField(choices=[("movie", "Filme"), ("tv", "Serie/Anime")], max_length=10)),
                ("tmdb_id", models.IntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="availability_alerts", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AlterUniqueTogether(name="availabilityalert", unique_together={("user", "media_type", "tmdb_id")}),
        migrations.AddIndex(
            model_name="availabilityalert",
            index=models.Index(fields=["media_type", "tmdb_id"], name="accounts_av_media_t_4bcf99_idx"),
        ),
    ]
