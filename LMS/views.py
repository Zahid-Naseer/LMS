from django.shortcuts import redirect, render, get_object_or_404 
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from .forms import LeaveRequestForm ,LeaveTypeEditForm , LeaveRequestEditForm , CompansationForm ,HolidayEditForm , LeaveAssigningForm, CompensationRequestEditForm , LeaveAllocationForm
from LMS.models import LeaveRequest, LeaveType  , Notification ,LeaveBalance , Compansation , Holiday , CarryForwardPolicy , CompensationSettings
from ProApp.models import User , UserProfile , Role
from django.contrib import messages 
from datetime import date, timedelta , datetime
import calendar
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.http import JsonResponse
from django import template
from django.conf import settings

@login_required
def apply_leave(request):
    x = ''
    error = ''
    max_compensation_days = CompensationSettings.objects.first().max_compensation_days  # Retrieve from settings

    if request.method == 'POST':
        request_type = request.POST.get('request_type')

        if request_type == 'LEAVE':
            form = LeaveRequestForm(request.user, request.POST)
            if form.is_valid():
                start_date = form.cleaned_data['from_date']
                end_date = form.cleaned_data['to_date']

                if end_date < start_date:
                    x = 'End date cannot be less than start date.'
                else:
                    leave_request = form.save(commit=False)
                    leave_request.employee = request.user
                    leave_request.duration = calculate_leave_duration(start_date, end_date)

                    leave_balance = LeaveBalance.objects.filter(employee=request.user, leave_type=leave_request.leave_type).first()

                    if leave_balance and (leave_balance.remaining_days - leave_balance.locked_days) >= leave_request.duration:
                        leave_balance.locked_days += leave_request.duration
                        leave_balance.save()
                        leave_request.save()

                        # Send email notification to admins
                        send_notification_email(request.user, leave_request, request_type)

                        return redirect('apply_leave')
                    else:
                        messages.error(request, 'Insufficient remaining days for this leave type. Please check your leave balance.')
            else:
                messages.error(request, 'Please correct the errors below.')

        elif request_type == 'COMPENSATION':
            form = CompansationForm(request.POST)
            if form.is_valid():
                compensation_date = form.cleaned_data['from_date']
                max_date = date.today() - timedelta(days=max_compensation_days)

                if compensation_date < max_date:
                    error = f"Leave Balance Request must be submitted within {max_compensation_days} days."
                else:
                    start_date = form.cleaned_data['from_date']
                    end_date = form.cleaned_data['to_date']
                    if end_date < start_date:
                        x = 'End date cannot be less than start date.'
                    else:
                        data = form.save(commit=False)
                        data.employee = request.user
                        data.duration = calculate_compensation_duration(start_date, end_date)
                        data.save()

                        # Send email notification to admins
                        send_notification_email(request.user, data, request_type)

                        return redirect('apply_leave')
            else:
                messages.error(request, 'Please correct the errors below.')

        else:
            messages.error(request, 'Please select a valid request type.')

    else:
        form = LeaveRequestForm(request.user)

    leave_type_data = LeaveBalance.objects.filter(employee=request.user).distinct()
    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)
    holidays = Holiday.objects.all().order_by('date')

    context = {
        'form': form,
        'notifications': notifications,
        'leave_balance_data': leave_type_data,
        'x': x,
        'error': error,
        'holidays': holidays,
        'request_type': request.POST.get('request_type', ''),  # Preserve request type
    }
    return render(request, 'LMS/apply_leave.html', context)   


def send_notification_email(user, request_data, request_type):
    # Get all admins with full access
    admin_profiles = UserProfile.objects.filter(role__full_access=True)
    admin_emails = [profile.employeeID.Email for profile in admin_profiles if profile.employeeID.Email]

    if not admin_emails:
        return

    # Prepare the email subject and content
    subject = f'New {request_type.title()} Request from {user.username}'
    context = {
        'user': user,
        'request_data': request_data,
        'request_type': request_type,
    }
    html_message = render_to_string('emails/request_notification.html', context)
    plain_message = strip_tags(html_message)
    from_email = 'zahid.solutions.net@gmail.com'  # The sender's email address
    reply_to = [user.email]  # Reply-to will also be the user's email

    # Create the email message
    email = EmailMultiAlternatives(
        subject=subject,
        body=plain_message,
        from_email=from_email,
        to=admin_emails,
        reply_to=reply_to
    )
    email.attach_alternative(html_message, "text/html")
    email.send()  # Send the email


@login_required
def update_compensation_days(request):
    if request.method == 'POST':
        max_compan_days = request.POST.get('max_com_days')
        


        # Save the max_compensation_days
        settings, created = CompensationSettings.objects.get_or_create(id=1)  # Assuming single instance
        settings.max_compensation_days = max_compan_days
        settings.save()

        return redirect('leave_types')  # Redirect to a view of your choice
    
    request.session['max_compansation_days'] = max_compan_days

    # Retrieve the current max_compensation_days
    settings, created = CompensationSettings.objects.get_or_create(id=1)
    context = {
        'max_com_days': settings.max_compensation_days
    }
    return render(request, 'LMS/leave_types.html', context)


def calculate_leave_duration(start_date, end_date):
    if not isinstance(start_date, date) or not isinstance(end_date, date):
        raise ValueError("start_date and end_date must be datetime.date objects")

    if start_date > end_date:
        raise ValueError("start_date must be before or equal to end_date")

    total_days = (end_date - start_date).days + 1  # Add 1 to include the end date

    # Combine weekend exclusion and holiday checking
    excluded_days = 0
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() in (calendar.SATURDAY, calendar.SUNDAY):
            excluded_days += 1
        # Check for holidays in the database
        holiday = Holiday.objects.filter(date=current_date).first()
        if holiday:
            excluded_days += 1
        current_date += timedelta(days=1)

    return total_days - excluded_days

def calculate_compensation_duration(start_date, end_date):
    if not isinstance(start_date, date) or not isinstance(end_date, date):
        raise ValueError("start_date and end_date must be datetime.date objects")

    if start_date > end_date:
        raise ValueError("start_date must be before or equal to end_date")

    total_days = (end_date - start_date).days + 1  # Add 1 to include the end date
    return total_days


@login_required
def leave_list(request):

    leave_requests = LeaveRequest.objects.filter(employee=request.user, status='PENDING').order_by('-used_date')
    leave_requests_historys = LeaveRequest.objects.filter(employee=request.user).order_by('-used_date')
    compansation_request = Compansation.objects.filter(employee=request.user, status='PENDING').order_by('-used_date')
    compansation_request_history = Compansation.objects.filter(employee=request.user).order_by('-used_date')


    leave_balance_menu = LeaveBalance.objects.filter(employee=request.user) \
    .select_related('leave_type') \
    .order_by('leave_type__name')

    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)

    context = {
        'leave_requests': leave_requests ,
         'notifications': notifications,
        'leave_requests_historys': leave_requests_historys,
        'compansation_request' : compansation_request,
            'compansation_request_history' : compansation_request_history,
            'leave_balance_menu':leave_balance_menu,
        }
    
    return render(request, 'LMS/leave_list.html', context)


@login_required
def approve_leave(request, leave_id):
    leave_request = get_object_or_404(LeaveRequest, pk=leave_id)
    user_profile = UserProfile.objects.get(user=leave_request.employee)
    employee = user_profile.employeeID
    if leave_request.status == 'PENDING':  # Only update if pending
        leave_balance = LeaveBalance.objects.filter(employee=leave_request.employee, leave_type=leave_request.leave_type).first()
        
        if leave_balance:
            if leave_balance.remaining_days >= leave_request.duration:
                leave_balance.remaining_days -= leave_request.duration
                leave_balance.locked_days -= leave_request.duration
                leave_request.status = 'APPROVED'
                leave_balance.save()
                leave_request.save()

                # Send approval email to the employee
                send_mail(
                    'Leave Request Approved',
                    f'Dear {employee.Fullname},\n\n'
                    f'Your leave request for {leave_request.leave_type.name} from {leave_request.from_date} to {leave_request.to_date} '
                    f'has been approved by {request.user.username}.\n\n'
                    'Best Regards,',
                    settings.DEFAULT_FROM_EMAIL,
                    [employee.Email],
                    fail_silently=False,
                )
            else:
                messages.error(request, 'Not enough remaining days to approve this request.')
                return redirect('pending_requests')
       
        leave_request.save()

        notification = Notification.objects.create(
            recipient=leave_request.employee,
            message=f"Your leave request for {leave_request.leave_type.name} from {leave_request.from_date} to {leave_request.to_date} has been {leave_request.status.lower()}",
            leave_request=leave_request,
        )

    return redirect('pending_requests')


@login_required
def reject_leave(request, leave_id):
    leave_request = get_object_or_404(LeaveRequest, pk=leave_id)
    user_profile = UserProfile.objects.get(user=leave_request.employee)
    employee = user_profile.employeeID
    leave_balance = LeaveBalance.objects.filter(employee=leave_request.employee, leave_type=leave_request.leave_type).first()
    leave_balance.locked_days -= leave_request.duration
    leave_request.status = 'REJECTED'
    leave_balance.save()
    leave_request.save()

    # Send rejection email to the employee
    send_mail(
        'Leave Request Rejected',
        f'Dear {employee.Fullname},\n\n'
        f'Your leave request for {leave_request.leave_type.name} from {leave_request.from_date} to {leave_request.to_date} '
        f'has been rejected by {request.user.username}.\n\n'
        'Best Regards,',
        settings.DEFAULT_FROM_EMAIL,
        [employee.Email],
        fail_silently=False,
    )
    
    # Create notification for the employee
    notification = Notification.objects.create(
        recipient=leave_request.employee,
        message=f"Your leave request for {leave_request.leave_type.name} from {leave_request.from_date} to {leave_request.to_date} has been rejected.",
        leave_request=leave_request,
    )

    return redirect('pending_requests')


@login_required
def approve_compansation(request, leave_id):
    leave_request = get_object_or_404(Compansation, pk=leave_id)
    user_profile = UserProfile.objects.get(user=leave_request.employee)
    employee = user_profile.employeeID

    if leave_request.status == 'PENDING':
        leave_request.status = 'APPROVED'
        leave_request.approved_date = date.today()  # Set the approved date to today
        leave_request.save()

        # Get or create LeaveBalance for the employee and 'Compensation' leave type
        leave_type = leave_request.leave_type
        leave_balance, created = LeaveBalance.objects.get_or_create(
            employee=leave_request.employee,
            leave_type=leave_type
        )

        # Update remaining days based on approved compensation days
        approved_days = leave_request.duration

        if created:
            leave_balance.remaining_days = approved_days
        else:
            leave_balance.remaining_days += approved_days

        leave_balance.save()

        # Send approval email to the employee
        send_mail(
            'Compensation Request Approved',
            f'Dear {employee.Fullname},\n\n'
            f'Your compensation request for {leave_request.leave_type.name} on {leave_request.from_date} '
            f'has been approved by {request.user.username}.\n\n'
            'Best Regards,',
            settings.DEFAULT_FROM_EMAIL,
            [employee.Email],
            fail_silently=False,
        )

        return redirect('pending_requests')

    else:
        return redirect('pending_requests')


@login_required
def reject_compansation(request, leave_id):
    leave_request = get_object_or_404(Compansation, pk=leave_id)
    user_profile = UserProfile.objects.get(user=leave_request.employee)
    employee = user_profile.employeeID
    leave_request.status = 'REJECTED'
    leave_request.save()

    # Send rejection email to the employee
    send_mail(
        'Compensation Request Rejected',
        f'Dear {employee.Fullname},\n\n'
        f'Your compensation request for {leave_request.leave_type.name} on {leave_request.from_date} '
        f'has been rejected by {request.user.username}.\n\n'
        'Best Regards,',
        settings.DEFAULT_FROM_EMAIL,
        [employee.Email],
        fail_silently=False,
    )

    return redirect('pending_requests')



@login_required
def leave_detail(request , leave_id ):
    leave_request = get_object_or_404(LeaveRequest, pk=leave_id)
    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)

    context ={
        'leave_request' : leave_request,
        'notifications' : notifications,
        
    }

    return render(request , 'LMS/leave_detail.html' , context)


@login_required
def leave_types(request):
    users = UserProfile.objects.all()
    leave_types = LeaveType.objects.all().order_by('name')
    holidays = Holiday.objects.all().order_by('date')
    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)

    leave_balances = LeaveBalance.objects.select_related('leave_type', 'employee').order_by('employee')

    if request.method == 'POST':
        # Handle leave type updates
        if 'save_leave' in request.POST:
            leave_id = request.POST['save_leave']
            leave_type = LeaveType.objects.get(pk=leave_id)
            leave_type.name = request.POST[f'leave_type_{leave_id}']
            leave_type.max_days_allowed = request.POST[f'leave_count_{leave_id}']
            leave_type.save()

        # Handle adding new leave type
        elif 'add_leave' in request.POST:
            LeaveType.objects.create(
                name=request.POST['new_leave_type'],
                max_days_allowed=request.POST['new_leave_count']
            )

        # Handle holiday updates
        elif 'save_holiday' in request.POST:
            holiday_id = request.POST['save_holiday']
            holiday = Holiday.objects.get(pk=holiday_id)
            holiday.name = request.POST[f'holiday_description_{holiday_id}']
            holiday.date = request.POST[f'holiday_date_{holiday_id}']
            holiday.save()

        # Handle adding new holiday
        elif 'add_holiday' in request.POST:
            Holiday.objects.create(
                name=request.POST['new_holiday_description'],
                date=request.POST['new_holiday_date']
            )

        return redirect('leave_types')

    # Retrieve the first CarryForwardPolicy
    first_carry_forward_policy = CarryForwardPolicy.objects.first()
    max_compansation_days = CompensationSettings.objects.first().max_compensation_days

    context = {
        'users': users,
        'leave_types': leave_types,
        'holidays': holidays,
        'notifications': notifications,
        'leave_balances': leave_balances,
        'last_additional_days': first_carry_forward_policy,
        'max_compansation_days': max_compansation_days,
    }

    return render(request, 'LMS/leave_types.html', context)



@login_required
def delete_leave(request, leave_id):
    leave_to_delete = get_object_or_404(LeaveRequest, id=leave_id)
    
    leave_to_delete.delete()
    return redirect('leave_list')  # Explicitly return redirect on success


@login_required
def delete_compansation(request, delete_compansation):
    leave_to_delete = get_object_or_404(Compansation , id=delete_compansation)

    leave_to_delete.delete()
    return redirect('pending_requests')  # Explicitly return redirect on success


@login_required
def delete_holiday(request, holiday_id):
    leave_to_delete = get_object_or_404(Holiday , id=holiday_id)

    leave_to_delete.delete()
    return redirect('leave_types')  # Explicitly return redirect on success


        

@login_required
def delete_leave_type(request, leave_type_id):
    leave_to_delete = get_object_or_404(LeaveType , id=leave_type_id)

    if request.user.userprofile.role.full_access:
        # Admin users can delete any leave request
        leave_to_delete.delete()
        return redirect('leave_types')  # Explicitly return redirect on success
    else:
        return redirect('leave_types')  # Or display an error message
    
@login_required
def delete_leave_balance(request , leave_balance_id):
    leave_to_delete = get_object_or_404(LeaveBalance , id=leave_balance_id)

    if request.user.userprofile.role.full_access:
        # Admin users can delete any leave request
        leave_to_delete.delete()
        return redirect('leave_allocation')  # Explicitly return redirect on success
    else:
        return redirect('leave_allocation')  # Or display an error message


@login_required
def edit_leave_request(request, leave_id):
    x = ''
    leave_request = get_object_or_404(LeaveRequest, id=leave_id)
    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)
    original_duration = leave_request.duration  # Store the original duration

    if request.method == 'POST':
        form = LeaveRequestEditForm(request.POST, instance=leave_request)
        if form.is_valid():
            start_date = form.cleaned_data['from_date']
            end_date = form.cleaned_data['to_date']

            if end_date < start_date:
                x = 'End date cannot be less than start date.'
            else:
                new_duration = calculate_leave_duration(start_date, end_date)
                duration_difference = new_duration - original_duration

                leave_balance = LeaveBalance.objects.filter(employee=leave_request.employee, leave_type=leave_request.leave_type).first()

                if leave_balance:
                    if (leave_balance.remaining_days - leave_balance.locked_days) + original_duration >= new_duration:
                        leave_balance.locked_days += duration_difference
                        leave_balance.save()
                        leave_request.duration = new_duration
                        leave_request.save()
                        return redirect('leave_list')  # Redirect to leave list on success
                    else:
                        messages.error(request, 'Insufficient remaining days for this leave type. Please check your leave balance.')
    else:
        form = LeaveRequestEditForm(instance=leave_request)

    context = {
        'leave_request': leave_request,
        'notifications': notifications,
        'form': form,
        'x': x,
    }

    return render(request, 'LMS/edit_leave_request.html', context)


@login_required
def edit_compansation_request(request , leave_id):
    error = ""
    x = ""
    max_compensation_days = 60
    leave_request = get_object_or_404(Compansation , id=leave_id)    
    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)
    if request.method == 'POST':
        form = CompensationRequestEditForm(request.POST, instance=leave_request)
        if form.is_valid():
            compensation_date = form.cleaned_data['from_date']
            max_date = date.today() - timedelta(days=max_compensation_days)

            if compensation_date < max_date:
                error = f"Leave Balance Request must be submitted with in {max_compensation_days} days"
            else:
                start_date = form.cleaned_data['from_date']
                end_date = form.cleaned_data['to_date']
                if end_date < start_date:
                    x ='End date can not be less than start date.'
                else:
                    data = form.save(commit=False)
                    data.employee = request.user
                    data.duration = calculate_compensation_duration(start_date, end_date)
                        
                    data.save()
                    return redirect('leave_list')  # Redirect to compensation list on success
    else:
        form = CompensationRequestEditForm(instance=leave_request) 
  
    context = {
        'leave_request' : leave_request,
        'notifications' : notifications,
        'form' : form,
        'x': x,
        'error' : error,
    }

    return render(request , 'LMS/edit_compansation_request.html' , context)


@login_required
def mark_notification_seen(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id)
    if notification.recipient == request.user:
        notification.is_seen = True
        notification.save()
        return redirect('leave_list' )
    




@login_required
def reset_balances(request):
    if request.method == 'POST':
        leave_type_id = request.POST.get('leave_type')
        additional_days = int(request.POST.get('additional_days'))

        # Check if there is already a CarryForwardPolicy record
        carry_forward_policy = CarryForwardPolicy.objects.first()

        if carry_forward_policy:
            # Update the existing record
            carry_forward_policy.leave_type_id = leave_type_id
            carry_forward_policy.carry_forward_days = additional_days
            carry_forward_policy.save()
        else:
            # Create a new record if none exists
            CarryForwardPolicy.objects.create(
                leave_type_id=leave_type_id,
                carry_forward_days=additional_days
            )

        # Handle resetting balances (this part remains unchanged)
        selected_leave_type = get_object_or_404(LeaveType, id=leave_type_id)
        selected_max_days_allowed = selected_leave_type.max_days_allowed

        all_leave_types = LeaveType.objects.all()

        for leave_type in all_leave_types:
            existing_balances = LeaveBalance.objects.filter(leave_type=leave_type)
            for balance in existing_balances:
                balance.remaining_days = leave_type.max_days_allowed
                if leave_type.id == int(leave_type_id):
                    if balance.remaining_days < additional_days:
                        balance.remaining_days += additional_days
                    else:
                        balance.remaining_days = additional_days + leave_type.max_days_allowed
                balance.save()

        return redirect('leave_types')

    leave_types = LeaveType.objects.all()

    # Retrieve the first CarryForwardPolicy
    first_carry_forward_policy = CarryForwardPolicy.objects.first()

    return render(request, 'LMS/leave_types.html', {'leave_types': leave_types, 'last_additional_days': first_carry_forward_policy})


@login_required
def leave_assigning(request):
    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)

    if request.method == 'POST':
        form = LeaveAssigningForm(request.POST)
        if form.is_valid():
            assigned_leave = form.save(commit=False)  # Don't save yet

            # Check for existing LeaveBalance for the assigned employee and leave type
            leave_balance = LeaveBalance.objects.filter(
                employee=assigned_leave.employee, leave_type=assigned_leave.leave_type
            ).first()

            if leave_balance:
                # If LeaveBalance exists, update remaining days
                leave_balance.remaining_days += assigned_leave.remaining_days
                leave_balance.save()
            else:
                assigned_leave.save()

             # Save the assigned leave record after potential balance update
            return redirect('apply_leave')  # Redirect to apply leave view for potential usage
    else:
        form = LeaveAssigningForm()

    context = {
        'form': form,
        'notifications': notifications,
    }

    return render(request, 'LMS/leave_assigning.html', context)



@login_required
def leave_balance(request):

    leave_balance = LeaveBalance.objects.all()
    

    context={
        'leave_balance' : leave_balance,
    }
    return render(request, 'LMS/leave_balance.html' , context)


@login_required
def balance_menu(request):
    leave_balance_menu = LeaveBalance.objects.filter(employee=request.user) \
    .select_related('leave_type') \
    .order_by('leave_type__name')
   
    context = {
        'leave_balance_menu' : leave_balance_menu,
        
    }
    return render(request, 'LMS/balance_menu.html' , context)



@login_required
def compansation_detail(request , compansation_id):
    leave_request = get_object_or_404(Compansation, pk=compansation_id)
    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)

    context ={
        'leave_request' : leave_request,
        'notifications' : notifications,
    }


    return render(request , 'LMS/compansation_detail.html' , context) 



@login_required
def leave_allocation(request):
    users = UserProfile.objects.all()
    leave_types = LeaveType.objects.all()
    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)

    if request.method == 'POST':
        form = LeaveAllocationForm(request.POST)
        if form.is_valid():
            allocated_leave = form.save(commit=False)

            # Check for existing allocation before saving
            existing_allocation = LeaveBalance.objects.filter(
                employee=allocated_leave.employee,
                leave_type=allocated_leave.leave_type,
            ).first()

            if existing_allocation:
                # Handle duplicate allocation error
                form.add_error(None, 'This employee already has this leave type assigned.')
            else:
                # Assign the leave type and save the allocation
                leave_type = allocated_leave.leave_type
                allocated_leave.remaining_days = leave_type.max_days_allowed
                allocated_leave.save()

               
                return redirect('leave_allocation')  # Redirect to the same view after successful allocation
        else:
            # Handle form validation errors
            messages.error(request, 'Please correct the errors below.')
    else:
        form = LeaveAllocationForm()

    leave_balances = LeaveBalance.objects.select_related('leave_type', 'employee').order_by('employee')

    context = {
        'users': users,
        'leave_types': leave_types,
        'form': form,
        'notifications': notifications,
        'leave_balances': leave_balances,
    }

    return render(request, 'LMS/leave_allocation.html', context)


@login_required
def canceled_leaves_request(request, canceled_leaves_id):
    try:
        canceled_leave = LeaveRequest.objects.get(id=canceled_leaves_id)
        canceled_leave.status = 'Canceled'
        leave_request = get_object_or_404(LeaveRequest, id=canceled_leaves_id)
        leave_balance = LeaveBalance.objects.filter(employee=leave_request.employee, leave_type=leave_request.leave_type).first()
        leave_balance.locked_days -= leave_request.duration
        leave_balance.save()
        leave_request.save()
        canceled_leave.save()
        return redirect('leave_list')
    except LeaveRequest.DoesNotExist:
        # Handle the case where the leave request ID is not found
        message = 'Leave request with ID {} not found.'.format(canceled_leaves_id)
        context = {'error_message': message}
        return render(request, 'LMS/leave_list.html', context)
    

    

@login_required
def canceled_compansation(request, canceled_compansation_id):
    try:
        canceled_leave = Compansation.objects.get(id=canceled_compansation_id)
        canceled_leave.status = 'CANCELED'
        canceled_leave.save()
        return redirect('leave_list')
    except Compansation.DoesNotExist:
        # Handle the case where the leave request ID is not found
        message = f'Leave request with ID {canceled_compansation_id} not found.'
        context = {'error_message': message}
        return render(request, 'LMS/leave_list.html', context)
    
@login_required
def pending_requests(request):
   
    leave_requests = LeaveRequest.objects.filter(status='PENDING').order_by('-used_date')
    leave_requests_historys = LeaveRequest.objects.all().order_by('-used_date')  # Assuming a used_date field
    compansation_request = Compansation.objects.filter(status='PENDING').order_by('-used_date')  # Assuming a created_at field
    compansation_request_history = Compansation.objects.all().order_by('-used_date')


    leave_balance_menu = LeaveBalance.objects.filter(employee=request.user) \
    .select_related('leave_type') \
    .order_by('leave_type__name')

    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)

    context = {
        'leave_requests': leave_requests ,
         'notifications': notifications,
        'leave_requests_historys': leave_requests_historys,
        'compansation_request' : compansation_request,
            'compansation_request_history' : compansation_request_history,
            'leave_balance_menu':leave_balance_menu,
        }
    return render(request , 'LMS/pending_requests.html' ,context)

