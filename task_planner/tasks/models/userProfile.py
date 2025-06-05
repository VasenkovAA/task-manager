# models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

DEFAULT_GRAPH_SETTINGS = {
    "taskBackground": "#FFFFFF",
    "borderColors": {
        "done": "#4CAF50",
        "waiting": "#FFEB3B",
        "canceled": "#9E9E9E",
        "progress": "#2196F3",
    },
    "deadlineIndicator": True,
    "showProgressBar": True,
    "showDependencyProgress": True,
    "showStatus": True,
}


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    graph_settings = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


# Сигналы для автоматического создания профиля при создании пользователя
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
