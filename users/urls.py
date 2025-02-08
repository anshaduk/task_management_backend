from django.urls import path
from . views import (
    CustomTokenObtainPairView,
    UserListCreateView,
    UserDetailView,
)
from .views import (
    create_user, edit_user, delete_user
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    ##JWT Authentication##
    path('token/',CustomTokenObtainPairView.as_view(),name='token_obtain_pair'),
    path('token/refresh/',TokenRefreshView.as_view(),name='token_refresh'),

    ##User Management##
    path('users/',UserListCreateView.as_view(),name='user-list-create'),
    path('users/<int:pk>/',UserDetailView.as_view(),name='user-detail'),

    path('create-user/', create_user, name='create-user'),
    path('edit-user/<int:user_id>/', edit_user, name='edit-user'),
    path('delete-user/<int:user_id>/', delete_user, name='delete-user'),
]