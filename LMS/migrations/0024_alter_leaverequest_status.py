# Generated by Django 5.0.6 on 2024-08-04 20:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LMS', '0023_alter_leavebalance_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='leaverequest',
            name='status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Desclined')], default='PENDING', max_length=20),
        ),
    ]
