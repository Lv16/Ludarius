from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("movies", "0002_streamingplatform_remove_movie_overview_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="movie",
            name="tmdb_id",
            field=models.IntegerField(blank=True, db_index=True, null=True, unique=True),
        ),
    ]
