from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    # Campos originales de User
    phone = models.CharField(max_length=20, blank=True)
    
    # Campos de CustomUser
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.TextField(blank=True, null=True)
    suspension_end = models.DateTimeField(blank=True, null=True)
    
    # Relaciones corregidas para evitar conflictos
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        related_name="custom_user_groups",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        related_name="custom_user_permissions",
        related_query_name="user",
    )

    def suspension_status(self):
        if self.is_suspended and self.suspension_end > timezone.now():
            return f"Suspendido hasta {self.suspension_end.strftime('%d/%m/%Y %H:%M')}"
        return "Activo"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    country = models.CharField("País", max_length=100, blank=True)  # Cambiado de location
    address = models.CharField("Dirección", max_length=255, blank=True)  # Nuevo campo
    phone = models.CharField("Teléfono", max_length=20, blank=True)  # Nuevo campo
    birth_date = models.DateField("Fecha de nacimiento", null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"


