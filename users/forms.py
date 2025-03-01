from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from .models import Profile

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'country', 'address', 'phone', 'birth_date', 'profile_picture']  # Campos actualizados
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'phone': forms.TextInput(attrs={'placeholder': '+56912345678'}),  # Formato sugerido
        }

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")