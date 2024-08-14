from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, LeaveBalance, LeaveType
from ProApp.models import UserProfile

def create_leave_balances(sender, instance, created, **kwargs):
    """
    Creates LeaveBalance records for a newly created user based on LeaveTypes with assign_to_all=True.
    """
    if created:
        user_profile = instance
        user = user_profile.user
        leave_types = LeaveType.objects.filter(assign_to_all=True)
        print(f"New user created: {user.username}")  # Add print statement
        for leave_type in leave_types:
            print(f"Creating LeaveBalance for {user} - {leave_type}") 
            LeaveBalance.objects.create(
                employee=user,
                leave_type=leave_type,
                remaining_days=leave_type.max_days_allowed
            )

# Connect the signal to the post_save event for UserProfile model
post_save.connect(create_leave_balances, sender=UserProfile)


# def save(self, *args, **kwargs):
#         if not self.id:  # Check if it's a new object
#             # Create LeaveBalance records here
#             leave_types = LeaveType.objects.filter(assign_to_all=True)
#             for leave_type in leave_types:
#                 LeaveBalance.objects.create(
#                     employee=self,
#                     leave_type=leave_type,
#                     remaining_days=leave_type.max_days_allowed
#                 )
#         super().save(*args, **kwargs)