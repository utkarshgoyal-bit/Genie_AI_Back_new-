
from django import forms
from .models import Employee


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['employee_id', 'first_name', 'last_name', 'date_of_birth', 'gender',
                  'phone', 'department', 'branch', 'shift', 'designation', 
                  'date_of_joining', 'employment_status']
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}),
            'first_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}),
            'department': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}),
            'branch': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}),
            'shift': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}),
            'designation': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}),
            'date_of_joining': forms.DateInput(attrs={'class': 'w-full px-4 py-2 border rounded-lg', 'type': 'date'}),
            'employment_status': forms.Select(attrs={'class': 'w-full px-4 py-2 border rounded-lg'}),
        }
