from django.db import models
from apps.accounts.models import User
from apps.organizations.models import Organization, Department, Branch, Shift


class Employee(models.Model):
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]
    STATUS_CHOICES = [
        ('probation', 'Probation'), ('confirmed', 'Confirmed'),
        ('notice', 'Notice Period'), ('relieved', 'Relieved')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20)
    
    # Personal
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    phone = models.CharField(max_length=20)
    
    # Professional
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True)
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True)
    designation = models.CharField(max_length=100)
    date_of_joining = models.DateField()
    employment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='probation')
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['organization', 'employee_id']
    
    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.employee_id})'