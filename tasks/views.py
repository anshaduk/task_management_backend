from django.shortcuts import render,redirect,get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework import status
from . models import Task
from users.models import CustomUser
from . serializers import TaskSerializer
from django.contrib.auth.decorators import login_required,user_passes_test
from .forms import TaskForm
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden


class TaskListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        tasks = Task.objects.filter(assigned_to=request.user)
        serializer = TaskSerializer(tasks,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

class TaskUpdateView(APIView):
    """Allows users to update task status (mark as completed)"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        print("Request Data:", request.data)
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            return Response({"error": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

        if task.assigned_to != request.user:
            return Response({"error": "You are not allowed to update this task."}, status=status.HTTP_403_FORBIDDEN)

        
        if request.data.get('status') == 'completed':
            if 'completion_report' not in request.data or 'worked_hours' not in request.data:
                return Response(
                    {"error": "completion_report and worked_hours are required when marking task as completed."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        
        serializer = TaskSerializer(
            task,
            data=request.data,
            partial=True,
            context={'request': request}  
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        print("Serializer Errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

 
class TaskReportView(APIView):
    """Admins & SuperAdmins can view task completion reports"""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            return Response({"error": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role not in ['admin', 'superadmin']:
            return Response({"error": "Permission denied. Only Admins & SuperAdmins can view reports."}, status=status.HTTP_403_FORBIDDEN)

        if task.status != 'completed':
            return Response({"error": "Completion report is only available for completed tasks."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "title": task.title,
            "status": task.status,
            "completion_report": task.completion_report,
            "worked_hours": task.worked_hours
        }, status=status.HTTP_200_OK)
    


###SuperAdmin Dashboard View###
@login_required
def superadmin_dashboard(request):
    if not request.user.is_superadmin:
        return render(request, '403.html', status=403)

    users = CustomUser.objects.all()
    tasks = Task.objects.all()
    return render(request, 'superadmin/dashboard.html', {'users': users, 'tasks': tasks})



###Admin Dashboard View###
@login_required
def admin_dashboard(request):
    
    if not request.user.is_admin:
        raise PermissionDenied("You don't have permission to access this page.")
    

    tasks = Task.objects.all()  
    
    context = {
        'tasks': tasks,
        'user_count': CustomUser.objects.filter(role='user').count(),
        'pending_tasks': tasks.filter(status='pending').count(),
        'completed_tasks': tasks.filter(status='completed').count(),
    }
    
    return render(request, 'admin/dashboard.html', context)



def is_superadmin_or_admin(user):
    """Check if user is a superadmin or admin"""
    return user.role in ['superadmin', 'admin']

@login_required
@user_passes_test(is_superadmin_or_admin)
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            
            
            if request.user.role == 'superadmin':
                return redirect('superadmin-dashboard')
            else:
                return redirect('admin-dashboard')
    else:
        form = TaskForm()
    
    return render(request, 'tasks/create_task.html', {'form': form})


@login_required
@user_passes_test(is_superadmin_or_admin)
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    user = request.user

    
    if user.role != 'superadmin' and task.created_by != user:
        return HttpResponseForbidden("You don't have permission to edit this task.")

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            
            if user.role == 'superadmin':
                return redirect('superadmin-dashboard')
            else:
                return redirect('admin-dashboard')
    else:
        form = TaskForm(instance=task)
    
    return render(request, 'tasks/edit_task.html', {'form': form})


def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        task.delete()
        return redirect('superadmin-dashboard')
    return render(request, 'tasks/confirm_delete.html', {'object': task})



def task_report(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    return render(request, 'tasks/task_report.html', {'task': task})