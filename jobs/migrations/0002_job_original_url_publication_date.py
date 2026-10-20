from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("jobs", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="job",
            name="original_url",
            field=models.URLField(),
        ),
        migrations.AddField(
            model_name="job",
            name="publication_date",
            field=models.DateTimeField(),
        ),
    ]
