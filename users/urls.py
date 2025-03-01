from django.urls import path
from .views import UserCreateView
from .views import ProfileDetailView, ProfileUpdateView
from django.contrib.auth import views as auth_views

app_name = 'users'
urlpatterns = [
    path('register/', UserCreateView.as_view(), name='register'),
    path('profile/', ProfileDetailView.as_view(), name='profile_detail'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='profile_edit'),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]