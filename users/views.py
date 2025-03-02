from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import UpdateView, DetailView, CreateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from .models import Profile, User  # Cambiar CustomUser por User
from .forms import ProfileUpdateForm, CustomUserCreationForm  # Asegurar que el formulario use el nuevo modelo
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .models import User  # Asegúrate de importar tu modelo User

# Mantener igual - funciona con Profile
class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'users/profile_detail.html'
    context_object_name = 'profile'

    def get_object(self):
        return self.request.user.profile

# Mantener igual - funciona con Profile
class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileUpdateForm
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('users:profile_detail')

    def get_object(self):
        return self.request.user.profile

# Actualizar el formulario para usar User
class UserCreateView(CreateView):
    form_class = CustomUserCreationForm  # Asegurar que este formulario use el modelo User
    template_name = 'users/register.html'
    success_url = reverse_lazy('login')

# Actualizar todas las referencias de CustomUser a User
@staff_member_required
def user_management(request):
    users = User.objects.all().exclude(is_superuser=True)  # Cambiar CustomUser por User
    return render(request, 'users/user_management.html', {'users': users})

# Añade estos imports
from django.views.decorators.csrf import csrf_protect
import json

@staff_member_required
@require_POST
def suspend_user(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    
    try:
        data = json.loads(request.body)
        duration = int(data.get('duration', 1))
        user.is_suspended = True
        user.suspension_reason = data.get('reason', 'Sin motivo especificado')
        user.suspension_end = timezone.now() + timezone.timedelta(days=duration)
        user.save()
        
        return JsonResponse({
            'success': True,
            'new_end': user.suspension_end.strftime('%Y-%m-%dT%H:%M:%S')  # Formato ISO
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@staff_member_required
@require_POST
def delete_user(request, user_id):
    try:
        user = get_object_or_404(User, pk=user_id)
        user.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


class CustomLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        
        # Verificar suspensión
        if user.is_suspended and user.suspension_end > timezone.now():
            messages.error(
                self.request,
                f"⛔ Cuenta suspendida hasta {user.suspension_end.strftime('%d/%m/%Y %H:%M')}\n"
                f"Motivo: {user.suspension_reason}"
            )
            return self.form_invalid(form)
            
        return super().form_valid(form)