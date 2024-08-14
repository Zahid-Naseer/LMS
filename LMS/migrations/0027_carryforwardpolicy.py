# Generated by Django 5.0.6 on 2024-08-06 09:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LMS', '0026_alter_compansation_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='CarryForwardPolicy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('carry_forward_days', models.IntegerField()),
                ('leave_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='LMS.leavetype')),
            ],
        ),
    ]
