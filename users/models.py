from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    
    # Solución: Agrega related_name únicos
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="custom_user_groups",  # Nombre único
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_permissions",  # Nombre único
        related_query_name="user",
    )

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField('Biografía', blank=True, max_length=500)
    location = models.CharField('Ubicación', max_length=100, blank=True)
    birth_date = models.DateField('Fecha de nacimiento', null=True, blank=True)
    profile_picture = models.ImageField('Foto de perfil', upload_to='profile_pics/', blank=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"