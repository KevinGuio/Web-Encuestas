# Generated by Django 5.1.6 on 2025-03-03 00:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0007_survey_is_blocked'),
    ]

    operations = [
        migrations.AddField(
            model_name='survey',
            name='block_reason',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='survey',
            name='blocked_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
