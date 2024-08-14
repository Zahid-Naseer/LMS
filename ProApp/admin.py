from django.contrib import admin
from ProApp.models import  UserProfile , Employee , Role 
# Register your models here.

admin.site.register(UserProfile)
admin.site.register(Employee)
admin.site.register(Role)