from django.urls import path
from .views import TaskListView, TaskUpdateView, TaskReportView,superadmin_dashboard,admin_dashboard
from .views import (
    create_task, edit_task, delete_task, task_report
)

urlpatterns = [
    path('tasks/', TaskListView.as_view(), name='task-list'),
    path('tasks/<int:pk>/', TaskUpdateView.as_view(), name='task-update'),
    path('tasks/<int:pk>/report/', TaskReportView.as_view(), name='task-report'),

    
    path('create-task/', create_task, name='create-task'),
    path('edit-task/<int:task_id>/', edit_task, name='edit-task'),
    path('delete-task/<int:task_id>/', delete_task, name='delete-task'),
    path('task-report/<int:task_id>/', task_report, name='task-report'),

    path('dashboard/superadmin/',superadmin_dashboard,name='superadmin-dashboard'),
    path('dashboard/admin/', admin_dashboard, name='admin-dashboard'),

]