# Generated by Django 4.2.15 on 2024-10-17 06:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('PropertyApp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Property',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('location_latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('location_longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('property_type', models.CharField(choices=[('apartment', 'Apartment'), ('house', 'House'), ('office', 'Office'), ('rooms', 'Rooms')], max_length=50)),
                ('status', models.CharField(choices=[('sold', 'Sold'), ('rented', 'Rented'), ('vacant', 'Vacant')], default='vacant', max_length=50)),
                ('image', models.ImageField(blank=True, null=True, upload_to='property_images/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
