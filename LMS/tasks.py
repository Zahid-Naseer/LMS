from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from .models import LeaveBalance, Compansation , CompensationSettings

@shared_task
def subtract_compensation_days():
    today = timezone.now()
    max_compensation_days = CompensationSettings.objects.first().max_compensation_days
    threshold_date = today - timedelta(days=max_compensation_days)

    # Get all approved compensations older than 60 days
    expired_compensations = Compansation.objects.filter(
        status='APPROVED',
        updated_at__lte=threshold_date
    )

    for comp in expired_compensations:
        leave_balance = LeaveBalance.objects.filter(
            employee=comp.employee,
            leave_type=comp.leave_type
        ).first()

        if leave_balance:
            leave_balance.remaining_days -= comp.duration
            leave_balance.save()

        # Optionally, mark compensation as processed or delete it
        comp.delete()