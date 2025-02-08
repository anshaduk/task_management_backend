from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import CustomUser
from .serializers import UserSerializer, UserUpdateSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer

from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages

from . forms import UserForm
from django.core.mail import send_mail
from django.conf import settings


# Custom JWT Token View
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


# User List and Create View
class UserListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        if request.user.is_superadmin:
            users = CustomUser.objects.all()
        elif request.user.is_admin:
            users = CustomUser.objects.exclude(role='superadmin')
        else:
            users = CustomUser.objects.filter(id=request.user.id)
        
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):

        if not request.user.is_superadmin:
            return Response(
                {"error": "Only superadmins can create users"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = UserSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        
        if self.request.user.is_superadmin:
            return user
        elif self.request.user.is_admin and user.role != 'superadmin':
            return user
        elif self.request.user.id == user.id:
            return user
        return None

    def get(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response(
                {"error": "You don't have permission to view this user"},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = UserSerializer(user)
        return Response(serializer.data)

    def put(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response(
                {"error": "You don't have permission to modify this user"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = UserUpdateSerializer(
            user,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            updated_user = serializer.save()
            return Response(UserSerializer(updated_user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        user = self.get_object(pk)
        if not user:
            return Response(
                {"error": "You don't have permission to delete this user"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Only superadmins can delete superadmin users
        if user.role == 'superadmin' and not request.user.is_superadmin:
            return Response(
                {"error": "Only superadmins can delete superadmin users"},
                status=status.HTTP_403_FORBIDDEN
            )
            
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

##create user##    
def create_user(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Send email notification with username and password
            subject = "Your Account Details - Task Management"
            message = f"""
            Hello {user.username},

            Your account has been successfully created.

            Here are your login credentials:

            **Username:** {user.username}  
            **Password:** {form.cleaned_data['password']}  

            Please log in and change your password immediately for security.

            Regards,  
            Task Management Team
            """
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [user.email]

            try:
                send_mail(subject, message, from_email, recipient_list, fail_silently=False)
                messages.success(request, "User created successfully, and email sent with credentials.")
            except Exception as e:
                messages.error(request, f"User created, but email failed: {e}")

            return redirect('superadmin-dashboard')
    else:
        form = UserForm()

    return render(request, 'users/create_user.html', {'form': form})


def edit_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('superadmin-dashboard')
    else:
        form = UserForm(instance=user)
    return render(request, 'users/edit_user.html', {'form': form})

def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('superadmin-dashboard')
    return render(request, 'users/confirm_delete.html', {'object': user})


    
##Login##

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            print(f"User: {user.username}, is_admin: {user.is_admin}, is_staff: {user.is_staff}")
            if user.is_superadmin:
                return redirect('superadmin-dashboard')
            elif user.is_admin:
                return redirect('admin-dashboard')
            else:
                return redirect('task-list')  
        else:
            messages.error(request, "Invalid username or password.")
    
    return render(request, 'login.html')


##Logout##
def logout_view(request):
    logout(request)
    return redirect('login')
