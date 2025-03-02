from django.urls import path
from .views import UserCreateView
from .views import ProfileDetailView, ProfileUpdateView
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'
urlpatterns = [
    path('register/', UserCreateView.as_view(), name='register'),
    path('profile/', ProfileDetailView.as_view(), name='profile_detail'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile_edit'),
    path('logout/', auth_views.LogoutView.as_view(), name="logout"),
    path('', views.user_management, name='user_management'),
    path('suspend/<int:user_id>/', views.suspend_user, name='suspend_user'),
    path('delete/<int:user_id>/', views.delete_user, name='delete_user'),
]