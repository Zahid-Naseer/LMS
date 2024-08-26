from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
# Create your models here.

class Employee(models.Model):
    Fullname = models.CharField(default="", max_length=20)
    service = models.CharField(default="" , max_length=225)         
    Email = models.EmailField(default="")
    
    def __str__(self):
        return str(self.Fullname)       
      
class Role(models.Model):   
    role_name = models.CharField(max_length=255, unique=True)
    user = models.BooleanField(default=False)
    full_access = models.BooleanField(default=False)
    super_admin = models.BooleanField(default=False)
    
    def __str__(self):
        return self.role_name    
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.ForeignKey( Role , on_delete=models.CASCADE)
    employeeID = models.OneToOneField(Employee, default="" , on_delete=models.CASCADE)
    
    #Status = models.BooleanField(default="")
    def __str__(self):
        return str(self.user)
    
