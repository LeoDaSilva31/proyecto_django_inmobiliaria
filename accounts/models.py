# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    dni = models.CharField(max_length=15, unique=True, blank=True, null=True)

    def __str__(self):
        return self.username or f"User {self.pk}"
