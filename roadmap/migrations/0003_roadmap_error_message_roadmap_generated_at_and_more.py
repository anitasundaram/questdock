# Generated by Django 5.1.3 on 2024-11-22 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('roadmap', '0002_roadmapshare'),
    ]

    operations = [
        migrations.AddField(
            model_name='roadmap',
            name='error_message',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='roadmap',
            name='generated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='roadmap',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('generating', 'Generating'), ('generated', 'Generated'), ('failed', 'Failed')], default='pending', max_length=20),
        ),
        migrations.AlterField(
            model_name='roadmap',
            name='recommendations',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
