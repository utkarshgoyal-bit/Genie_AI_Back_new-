from django.urls import path
from . import views

app_name = 'organizations'

urlpatterns = [
    path('', views.organization_list, name='organization_list'),
    path('create/', views.organization_create, name='organization_create'),
    path('<int:pk>/edit/', views.organization_edit, name='organization_edit'),
    path('<int:pk>/delete/', views.organization_delete, name='organization_delete'),
    
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
]