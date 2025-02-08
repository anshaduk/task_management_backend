from django.shortcuts import render,redirect,get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from . models import Task
from users.models import CustomUser
from . serializers import TaskSerializer
from django.contrib.auth.decorators import login_required
from .forms import TaskForm

class TaskListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self,request):
        tasks = Task.objects.filter(assigned_to=request.user)
        serializer = TaskSerializer(tasks,many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)

class TaskUpdateView(APIView):
    """Allows users to update task status (mark as completed)"""
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            return Response({"error": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

        if task.assigned_to != request.user:
            return Response({"error": "You are not allowed to update this task."}, status=status.HTTP_403_FORBIDDEN)

        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
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
        return render(request, '403.html', status=403)

    tasks = Task.objects.filter(assigned_to__role='user')
    return render(request, 'admin/dashboard.html', {'tasks': tasks})



def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('superadmin-dashboard')
    else:
        form = TaskForm()
    return render(request, 'tasks/create_task.html', {'form': form})

def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('superadmin-dashboard')
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