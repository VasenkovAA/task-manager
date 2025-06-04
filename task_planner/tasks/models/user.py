from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    user_settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Пользовательские настройки в формате JSON"
    )