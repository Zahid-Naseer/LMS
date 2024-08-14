from django.contrib.auth.models import User
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.test import TestCase


class LeaveType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    max_days_allowed = models.PositiveIntegerField(blank=True, null=True)
    assign_to_all = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class LeaveRequest(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    from_date = models.DateField()
    to_date = models.DateField()
    reason = models.TextField()
    duration = models.PositiveIntegerField(null=True, blank=True)  # Calculate duration on save
    status = models.CharField(max_length=20, choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Declined')], default='PENDING')
    used_date = models.DateField(default=timezone.now)


    def __str__(self):
        return f"{self.employee.username} - {self.leave_type.name} ({self.from_date} - {self.to_date})"
    

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    leave_request = models.ForeignKey(LeaveRequest, on_delete=models.CASCADE)
    is_seen = models.BooleanField(default=False)  # Flag to track if notification is seen
    created_at = models.DateTimeField(auto_now_add=True)    

class LeaveBalance(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE)
    leave_type = models.ForeignKey('LeaveType', on_delete=models.CASCADE)
    remaining_days = models.IntegerField(null=True, blank=True , default=0)  # Set to null and blank
    locked_days = models.IntegerField(default=0)
    

    def initialize_remaining_days(self):
        if self.leave_type and not self.remaining_days:
            self.remaining_days = self.leave_type.max_days_allowed
            self.save()

    class Meta:
        unique_together = ('employee', 'leave_type')        

    def __str__(self):
        return f"{self.employee.username} - {self.leave_type.name} - {self.remaining_days} days"
    

class Compansation(models.Model):
    employee = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE,  null=True)
    from_date = models.DateField( null=True)
    to_date = models.DateField( null=True)
    reason = models.TextField( null=True)
    duration = models.PositiveIntegerField(null=True, blank=True)  # Calculate duration on save
    status = models.CharField(max_length=20, choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Declined'), ('PROCESSED', 'Processed')], default='PENDING')
    used_date = models.DateField(default=timezone.now)
    approved_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"compansation for ({self.from_date} - {self.to_date}) days"
    

class Holiday(models.Model):
    name = models.CharField(max_length=50)
    date = models.DateField()

    def __str__(self):
        return f"{self.date} - {self.name}"    
    

# @receiver(post_save, sender=LeaveType)
# def assign_new_leave_type(sender, instance, created, **kwargs):
#     if created and instance.assign_to_all:
#         users = User.objects.all()
#         for user in users:
#             if not LeaveBalance.objects.filter(employee=user, leave_type=instance).exists():
#                 LeaveBalance.objects.create(  
#                     leave_type=instance,
#                     employee=user,
#                     remaining_days=instance.max_days_allowed,
#                 )    


class CarryForwardPolicy(models.Model):
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    carry_forward_days = models.IntegerField()

    def __str__(self):
        return f"{self.leave_type.name}: {self.carry_forward_days} days"
    

class CompensationSettings(models.Model):
    max_compensation_days = models.IntegerField(default=60)     
    