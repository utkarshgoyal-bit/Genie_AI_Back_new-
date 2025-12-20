from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
        ORG_ADMIN = 'ORG_ADMIN', 'Organization Admin'
        HR_ADMIN = 'HR_ADMIN', 'HR Admin'
        MANAGER = 'MANAGER', 'Manager'
        EMPLOYEE = 'EMPLOYEE', 'Employee'
    
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE, null=True, blank=True, related_name='users')
    phone = models.CharField(max_length=20, blank=True)
    is_first_login = models.BooleanField(default=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    @property
    def role_level(self):
        levels = {
            'SUPER_ADMIN': 5,
            'ORG_ADMIN': 4,
            'HR_ADMIN': 3,
            'MANAGER': 2,
            'EMPLOYEE': 1,
        }
        return levels.get(self.role, 0)
    
    def __str__(self):
        return self.email