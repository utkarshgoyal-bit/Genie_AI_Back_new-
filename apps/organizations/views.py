from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.decorators import role_required
from .models import Organization, Department, Branch, Shift
from .forms import OrganizationForm, DepartmentForm, BranchForm, ShiftForm


@login_required
@role_required(['SUPER_ADMIN'])
def organization_list(request):
    organizations = Organization.objects.all()
    return render(request, 'organizations/organization_list.html', {'organizations': organizations})


@login_required
@role_required(['SUPER_ADMIN'])
def organization_create(request):
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Organization created successfully')
            return redirect('organizations:organization_list')
    else:
        form = OrganizationForm()
    return render(request, 'organizations/organization_form.html', {'form': form, 'action': 'Create'})


@login_required
@role_required(['SUPER_ADMIN'])
def organization_edit(request, pk):
    organization = get_object_or_404(Organization, pk=pk)
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES, instance=organization)
        if form.is_valid():
            form.save()
            messages.success(request, 'Organization updated successfully')
            return redirect('organizations:organization_list')
    else:
        form = OrganizationForm(instance=organization)
    return render(request, 'organizations/organization_form.html', {'form': form, 'action': 'Edit'})


@login_required
@role_required(['SUPER_ADMIN'])
def organization_delete(request, pk):
    organization = get_object_or_404(Organization, pk=pk)
    organization.delete()
    messages.success(request, 'Organization deleted successfully')
    return redirect('organizations:organization_list')


@login_required
@role_required(['SUPER_ADMIN', 'ORG_ADMIN'])
def department_list(request):
    if request.user.role == 'SUPER_ADMIN':
        departments = Department.objects.all()
    else:
        departments = Department.objects.filter(organization=request.user.organization)
    return render(request, 'organizations/department_list.html', {'departments': departments})


@login_required
@role_required(['SUPER_ADMIN', 'ORG_ADMIN'])
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save(commit=False)
            if request.user.role != 'SUPER_ADMIN':
                department.organization = request.user.organization
            form.save()
            messages.success(request, 'Department created successfully')
            return redirect('organizations:department_list')
    else:
        form = DepartmentForm()
    return render(request, 'organizations/department_form.html', {'form': form, 'action': 'Create'})


@login_required
@role_required(['SUPER_ADMIN', 'ORG_ADMIN'])
def department_edit(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department updated successfully')
            return redirect('organizations:department_list')
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'organizations/department_form.html', {'form': form, 'action': 'Edit'})


@login_required
@role_required(['SUPER_ADMIN', 'ORG_ADMIN'])
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    department.delete()
    messages.success(request, 'Department deleted successfully')
    return redirect('organizations:department_list')