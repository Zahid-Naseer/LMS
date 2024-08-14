from django.contrib import admin
from .models import LeaveRequest , LeaveType , Notification , LeaveBalance , Compansation , Holiday , CarryForwardPolicy , CompensationSettings
# Register your models here.

admin.site.register(LeaveRequest)
admin.site.register(LeaveType)
admin.site.register(Notification)
admin.site.register(LeaveBalance)
admin.site.register(Compansation)
admin.site.register(Holiday)
admin.site.register(CarryForwardPolicy)
admin.site.register(CompensationSettings)