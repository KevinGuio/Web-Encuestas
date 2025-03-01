from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.conf import settings

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
    
    @property
    def total_votes(self):
        return sum(answer.votes for answer in self.answers.all())

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
