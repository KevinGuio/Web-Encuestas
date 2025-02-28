from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
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

    def __str__(self):
        return self.title
    
    pass


class Answer(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField("Respuesta", max_length=200)
    votes = models.IntegerField("Votos", default=0)  # Nuevo campo

class Comment(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    votes = models.IntegerField(default=0)
    is_reported = models.BooleanField(default=False)

class Report(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    reason = models.TextField()

class Vote(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.IntegerField()

class UserVote(models.Model):
    """Registra que un usuario ya votó en una encuesta (para evitar votos múltiples)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'survey')