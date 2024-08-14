from django import forms
from .models import LeaveRequest, LeaveType , Compansation , Holiday , LeaveBalance

class LeaveRequestForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['leave_type'].queryset = LeaveType.objects.filter(leavebalance__employee=user)

    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'from_date', 'to_date', 'reason']

class LeaveRequestEditForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'from_date', 'to_date', 'reason']  # Allow editing status only

class CompensationRequestEditForm(forms.ModelForm):
    class Meta:
        model = Compansation
        fields = ['leave_type', 'from_date', 'to_date', 'reason']  # Allow editing status only        

class LeaveTypeEditForm(forms.ModelForm):
    class Meta:
        model = LeaveType
        fields = '__all__'  # Allow editing all fields for LeaveType

class CompansationForm(forms.ModelForm):
    class Meta:
        model = Compansation
        fields = ['leave_type', 'from_date', 'to_date', 'reason'] # Allow editing all fields for LeaveType        


class HolidayEditForm(forms.ModelForm):
    class Meta: 
        model = Holiday
        fields = '__all__'


class LeaveAssigningForm(forms.ModelForm):
    class Meta:
        model = LeaveBalance
        fields = '__all__'        


class LeaveAllocationForm(forms.ModelForm):
    class Meta:
        model = LeaveBalance
        fields = ['employee' , 'leave_type' , 'remaining_days']      
