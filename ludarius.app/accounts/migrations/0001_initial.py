import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Collection",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("is_public", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="collections", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("verb", models.CharField(max_length=80)),
                ("media_type", models.CharField(blank=True, max_length=10)),
                ("tmdb_id", models.IntegerField(blank=True, null=True)),
                ("is_read", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="sent_notifications", to=settings.AUTH_USER_MODEL)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Profile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("bio", models.CharField(blank=True, max_length=280)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="profile", to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="MediaStatus",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("media_type", models.CharField(choices=[("movie", "Filme"), ("tv", "Serie/Anime")], max_length=10)),
                ("tmdb_id", models.IntegerField()),
                ("status", models.CharField(choices=[("want", "Quero ver"), ("watching", "Assistindo"), ("watched", "Assistido"), ("dropped", "Dropado")], max_length=20)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name="CollectionItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("media_type", models.CharField(choices=[("movie", "Filme"), ("tv", "Serie/Anime")], max_length=10)),
                ("tmdb_id", models.IntegerField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("collection", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="accounts.collection")),
            ],
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(fields=["user", "is_read", "created_at"], name="accounts_no_user_id_748d7e_idx"),
        ),
        migrations.AlterUniqueTogether(name="mediastatus", unique_together={("user", "media_type", "tmdb_id")}),
        migrations.AddIndex(
            model_name="mediastatus",
            index=models.Index(fields=["user", "updated_at"], name="accounts_me_user_id_d43673_idx"),
        ),
        migrations.AddIndex(
            model_name="mediastatus",
            index=models.Index(fields=["media_type", "tmdb_id"], name="accounts_me_media_t_dbec4f_idx"),
        ),
        migrations.AddIndex(
            model_name="mediastatus",
            index=models.Index(fields=["status"], name="accounts_me_status_7bb8e2_idx"),
        ),
        migrations.AlterUniqueTogether(name="collectionitem", unique_together={("collection", "media_type", "tmdb_id")}),
        migrations.AddIndex(
            model_name="collectionitem",
            index=models.Index(fields=["media_type", "tmdb_id"], name="accounts_co_media_t_3dd94d_idx"),
        ),
    ]
