from django.shortcuts import render , redirect
from ProApp.models import  UserProfile , Employee , Role
from LMS.models import LeaveBalance  , LeaveType , Compansation , CompensationSettings
from LMS.models import Notification
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required ,user_passes_test
from django.contrib.auth.models import User 
from django.shortcuts import get_object_or_404
from .forms import UserProfileForm
from django.db import IntegrityError
from django.contrib import messages
from django.utils import timezone
from django.dispatch import receiver
from datetime import date, timedelta
from django.http import HttpResponseRedirect
from ProApp.forms import CustomUserChangeForm ,  CustomEmployeeChangeForm , RoleForm , CustomRoleChangeForm 
#from .forms import UserEditForm


@login_required
def dashboard(request):
    user_profile = UserProfile.objects.get(user=request.user)
    check_and_subtract_compensation_days()  # Correct function call

    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)
    
    context = {
        'user_profile': user_profile,  # Corrected key-value assignment
        'notifications': notifications
    }

    return render(request, 'role/admin_dashboard.html', context)


def check_and_subtract_compensation_days():
    compensations = Compansation.objects.filter(status='APPROVED')
    max_days = CompensationSettings.objects.first().max_compensation_days 
    for comp in compensations:
        if comp.approved_date and timezone.now().date() >= comp.approved_date + timedelta(days=max_days):
            leave_balance = LeaveBalance.objects.get(employee=comp.employee, leave_type=comp.leave_type)
            leave_balance.remaining_days -= comp.duration
            leave_balance.save()

            # Optionally, mark this compensation as processed so it isn't checked again
            comp.status = 'PROCESSED'
            comp.save()


@login_required
def register(request):
    error_message = ''
    if request.method == 'POST':
        form = UserProfileForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            role = form.cleaned_data['role']
            employee_id = form.cleaned_data['employeeID']

            # Get the role of the requesting user
            requester_role = request.user.userprofile.role

            # Check if the requesting user is not a super admin but trying to assign a full_access or super_admin role
            if (role.full_access or role.super_admin) and not requester_role.super_admin:
                error_message = 'You do not have permission to assign this role.'
            else:
                try:
                    user = User.objects.create_user(username=username, password=password)
                    user_profile = UserProfile.objects.create(
                        user=user,
                        role=role,
                        employeeID=employee_id
                    )
                    messages.success(request, 'User registered successfully!')
                    return redirect('users')  # Redirect to success page
                except IntegrityError as e:
                    if 'username' in str(e):
                        messages.error(request, 'Username already exists. Please choose a different username.')
                    else:
                        messages.error(request, 'An error occurred during registration. Please try again later.')
                except Exception as e:
                    messages.error(request, f'An unexpected error occurred: {str(e)}')
        else:
            messages.error(request, 'Invalid form data.')

    else:
        form = UserProfileForm()

    return render(request, 'register.html', {'form': form, 'error_message': error_message})

def user_login(request):
    # Check if the user is already logged in
    if request.user.is_authenticated:
        return redirect('dashboard')  # Redirect to the dashboard if already logged in

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Redirect to the dashboard after successful login
        else:
            messages.error(request, 'Username or Password is Invalid')
            return render(request, 'login.html')

    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
def delete_user(request, user_id):
    user_to_delete = get_object_or_404(User, id=user_id)

   
    user_to_delete.delete()
    return redirect('users')

    return redirect('users')

@login_required
def delete_employee(request, employee_id):
    employee_to_delete = get_object_or_404(Employee, id=employee_id)

    if request.method == 'POST':
        employee_to_delete.delete()
        return redirect('employee')

    return redirect('employee')

@login_required
def delete_role(request, role_id):
    role_to_delete = get_object_or_404(Role, id=role_id)

    if request.method == 'POST':
        # Ensure the admin cannot delete their own account
        role_to_delete.delete()
        return redirect('role')

    return redirect('role')


@login_required
def edit_users_desc(request , user_id):
    
    user = get_object_or_404(User, id=user_id)
    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)

    return render(request, 'role/edit_users_desc.html', {'user': user , 'notifications' : notifications} )

@login_required
def users(request):
    users_with_role = User.objects.filter(userprofile__role__isnull=False)
    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)
    context = {
        'users' : users_with_role,
        'notifications' : notifications,
    }
    return render(request , 'users.html' , context)

@login_required
def users_desc(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user_profile = user.userprofile  # Assuming there is a related user profile model
    error_message = ''

    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user_profile)
        if form.is_valid():
            username = form.cleaned_data['username']
            role = form.cleaned_data['role']  # Assuming the form has a role field
            
            # Get the role of the requesting user
            requester_role = request.user.userprofile.role

            # Check if the requesting user is trying to assign an admin or super_admin role without proper permissions
            if (role.full_access or role.super_admin) and not requester_role.super_admin:
                error_message =  'You do not have permission to assign this role.'
            else:
                if username:
                    user.username = username
                    user.save()

                # Update the user's role
                user_profile.role = role
                user_profile.save()

              
                return redirect('users')  # Redirect to a list of users or another appropriate page
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserChangeForm(instance=user_profile)


   

    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)
    context = {
        'user': user,
        'form': form,
        'notifications': notifications, 
        'error_message':error_message,
    }
    return render(request, 'role/users_desc.html', context)


@login_required
def employee(request ):
    employees = Employee.objects.all()
    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)
    
    context = {
        'employees' : employees,
        'notifications': notifications,
    }
    
    return render(request , 'employee.html' , context)


def employee_register(request):
    if request.method == 'POST':
        Fullname = request.POST['Fullname']
        service = request.POST['Service']
        Email = request.POST['Email']

        try:
            # Try to create a new Employee
            user_profile = Employee(Fullname=Fullname, service=service, Email=Email)
            user_profile.save()
        except IntegrityError:
            # Handle the case where the employeeID already exists
            error_message = "EmployeeID already in use. Please choose a different one."
            return render(request, 'employee_register.html', {'error_message': error_message})
        
        

        return redirect('employee_register')  # Redirect to the dashboard or any other page
    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)

    context ={
        'notifications': notifications,
    }
    return render(request, 'employee_register.html' , context )


def edit_employee_desc(request , employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)

    return render(request , 'edit_employee_desc.html' , {  'employee': employee , 'notifications' : notifications})   

@login_required
def employee_desc(request , employee_id):
    
    employee = get_object_or_404(Employee, id=employee_id)

    if request.method == 'POST':
        form = CustomEmployeeChangeForm(request.POST, instance=employee)


        if form.is_valid():  
            form.save()
            return redirect('employee')
    else:
        form = CustomEmployeeChangeForm()
    
    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)
    context= {
        'employee' : employee,    
        'form' : form,
        'notifications' : notifications,
    }
    return render(request , 'employee_desc.html' , context) 

@login_required
def new_role(request):
    if request.method == 'POST':
        form = RoleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('role')
    else:
        form = RoleForm()
    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)    
    return render(request , 'new_role.html' , {'form' : form , 'notifications' : notifications})

@login_required
def new_role_edit(request, role_id):
    role = get_object_or_404(Role, id=role_id)

    if request.method == 'POST':
        form = CustomRoleChangeForm(request.POST, instance=role)
        if form.is_valid():
            form.save()
    else:
        form = CustomRoleChangeForm(instance=role)
    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)    

    return render(request, 'new_role_edit.html', {'form': form, 'role': role , 'notifications': notifications})

@login_required
def new_role_desc(request , role_id):
    role = get_object_or_404(Role, id=role_id)
    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)
    context = {
        'role' : role,
        'notifications' : notifications,
    }
    
    return render(request , 'new_role_desc.html' , context)


@login_required
def role(request):
    roles = Role.objects.all()
    users = User.objects.all()
    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)
    context = {
        'roles' : roles,
        'users' : users,
        'notifications' : notifications,
    }
    return render(request , 'role.html' , context)


@login_required
def profile(request):
    notifications = Notification.objects.filter(recipient=request.user, is_seen=False)
    context={
        'notifications': notifications,
    }
    return render(request , 'profile.html', context )