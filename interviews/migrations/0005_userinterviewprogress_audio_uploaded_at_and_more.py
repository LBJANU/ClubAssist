# Generated by Django 5.0.2 on 2025-06-27 03:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interviews', '0004_alter_userinterviewprogress_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userinterviewprogress',
            name='audio_uploaded_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='userinterviewprogress',
            name='response_audio',
            field=models.FileField(blank=True, null=True, upload_to='audio_responses/'),
        ),
    ]
