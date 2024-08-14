from django.urls import path
from . import views  # Import your views here


urlpatterns = [
    path('apply/', views.apply_leave, name='apply_leave'),
    path('list/', views.leave_list, name='leave_list'),
    path('leave_deatil/<int:leave_id>', views.leave_detail, name='leave_detail'),
    path('approve_leave/<int:leave_id>/', views.approve_leave, name='approve_leave'),
    path('reject_leave/<int:leave_id>/', views.reject_leave, name='reject_leave'),

    path('approve_compansation/<int:leave_id>/', views.approve_compansation, name='approve_compansation'),
    path('reject_compansation/<int:leave_id>/', views.reject_compansation, name='reject_compansation'),

    path('pending_requests/' , views.pending_requests , name='pending_requests'),


    path('leave_types', views.leave_types, name='leave_types'),
    path('edit_leave_request/<int:leave_id>', views.edit_leave_request, name='edit_leave_request'),
    path('delete_leave/<int:leave_id>', views.delete_leave, name='delete_leave'),
    path('delete_compansation/<int:delete_compansation>', views.delete_compansation, name='delete_compansation'),
    path('delete_leave_balance/<int:leave_balance_id>' , views.delete_leave_balance , name='delete_leave_balance'),

    path('mark_notification_seen/<int:notification_id>', views.mark_notification_seen, name='mark_notification_seen'),
    path('delete_holiday/<int:holiday_id>', views.delete_holiday, name='delete_holiday'),

    path('leave_assigning', views.leave_assigning, name='leave_assigning'),
    path('reset_balances', views.reset_balances, name='reset_balances'),
    path('leave_balance', views.leave_balance, name='leave_balance'),
    path('delete_leave_type/<int:leave_type_id>', views.delete_leave_type, name='delete_leave_type'),
    path('edit_compansation_request/<int:leave_id>', views.edit_compansation_request, name='edit_compansation_request'),
    path('balance_menu/', views.balance_menu, name='balance_menu'),
    path('update_compensation_days/', views.update_compensation_days, name='update_compensation_days'),
    
    path('leave_allocation/', views.leave_allocation, name='leave_allocation'),
    path('compansation_detail/<int:compansation_id>', views.compansation_detail, name='compansation_detail'),
    path('canceled_leaves_request/<int:canceled_leaves_id>', views.canceled_leaves_request, name='canceled_leaves_request'),
    path('canceled_compansation/<int:canceled_compansation_id>/', views.canceled_compansation, name='canceled_compansation'),
    

]