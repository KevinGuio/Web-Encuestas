from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

# Create your models here.
User = get_user_model()
# models.py (app: surveys)
class Survey(models.Model):
    CATEGORY_CHOICES = [
        ('GEN', 'General'),
        ('TEC', 'Tecnología'),
        ('EDU', 'Educación'),
        ('POL', 'Política'),
    ]
    
    title = models.CharField("Título", max_length=200)
    description = models.TextField("Descripción")
    category = models.CharField("Categoría", max_length=3, choices=CATEGORY_CHOICES)
    deadline = models.DateTimeField("Tiempo límite")
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_blocked = models.BooleanField(default=False)
    block_reason = models.TextField(blank=True, null=True)  # Nuevo campo
    blocked_at = models.DateTimeField(blank=True, null=True)  # Nuevo campo
    
    @property
    def total_votes(self):
        return sum(answer.votes for answer in self.answers.all())
    
    def is_expired(self):
        return timezone.now() > self.deadline

    def can_be_blocked(self):
        return not self.is_expired
    def __str__(self):
        return self.title
    
    def get_average_rating(self):
        return self.ratings.aggregate(Avg('stars'))['stars__avg'] or 0.0
    
    def get_rating_stars(self):
        avg = self.get_average_rating()
        full = int(avg)
        half = 1 if (avg - full) >= 0.5 else 0
        return {
            'full': range(full),       # Convertir a rango iterable
            'half': range(half),       # Convertir a rango iterable
            'empty': range(5 - full - half)
        }
    
    pass


class Answer(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField("Respuesta", max_length=200)
    votes = models.IntegerField("Votos", default=0)  # Nuevo campo


class UserVote(models.Model):
    """Registra que un usuario ya votó en una encuesta (para evitar votos múltiples)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'survey')

class Rating(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stars = models.IntegerField(choices=[(i, '★' * i) for i in range(1, 6)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('survey', 'user')

class Comment(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='liked_comments',
        blank=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comentario de {self.user.username}"
    
    def total_likes(self):
        return self.likes.count()
    
    def can_delete(self, user):
        return user == self.user or user.is_staff


class Report(models.Model):
    # Contenido reportado (puede ser Survey o Comment)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Reporte de {self.reporter} - {self.content_object}"
