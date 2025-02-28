from django.db import models
from django.contrib.auth.models import User
# Create your models here.

# models.py (app: surveys)
class Survey(models.Model):
    title = models.CharField(max_length=200)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

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
