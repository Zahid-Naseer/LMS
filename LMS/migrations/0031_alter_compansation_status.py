# Generated by Django 5.0.6 on 2024-08-13 07:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LMS', '0030_compansation_approved_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='compansation',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Declined'), ('PROCESSED', 'Processed')], default='PENDING', max_length=20),
        ),
    ]
