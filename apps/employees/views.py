
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import role_required
from .models import Employee
from .forms import EmployeeForm


@login_required
@role_required(['SUPER_ADMIN', 'ORG_ADMIN', 'HR_ADMIN'])
def employee_list(request):
    if request.user.role == 'SUPER_ADMIN':
        employees = Employee.objects.all()
    else:
        employees = Employee.objects.filter(organization=request.user.organization)
    return render(request, 'employees/employee_list.html', {'employees': employees})


@login_required
@role_required(['SUPER_ADMIN', 'ORG_ADMIN', 'HR_ADMIN'])
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            if request.user.role != 'SUPER_ADMIN':
                employee.organization = request.user.organization
            form.save()
            messages.success(request, 'Employee created successfully')
            return redirect('employees:employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'employees/employee_form.html', {'form': form, 'action': 'Create'})


@login_required
@role_required(['SUPER_ADMIN', 'ORG_ADMIN', 'HR_ADMIN'])
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee updated successfully')
            return redirect('employees:employee_list')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'employees/employee_form.html', {'form': form, 'action': 'Edit'})


@login_required
@role_required(['SUPER_ADMIN', 'ORG_ADMIN', 'HR_ADMIN'])
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    employee.delete()
    messages.success(request, 'Employee deleted successfully')
    return redirect('employees:employee_list')