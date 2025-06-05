from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
import json

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
    """
    Модель расширения профиля пользователя.

    Хранит дополнительные настройки пользователя,
    в частности - параметры отображения графиков.

    Attributes:
        user (OneToOneField): Связь с моделью User
        graph_settings (JSONField): Настройки графиков в JSON-формате
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
        help_text="Связанный аккаунт пользователя",
    )
    graph_settings = models.JSONField(
        default=DEFAULT_GRAPH_SETTINGS,
        blank=True,
        verbose_name="Настройки графиков",
        help_text="Параметры отображения диаграмм в JSON-формате",
    )

    def __str__(self):
        return f"Профиль {self.user.username}"

    def clean(self):
        """Валидация JSON-структуры настроек"""
        super().clean()
        try:
            # Проверка возможности сериализации
            json.dumps(self.graph_settings)
        except TypeError:
            raise ValidationError({"graph_settings": "Некорректный формат JSON-данных"})

    class Meta:
        """
        Метаданные модели UserProfile.
        """

        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"


# Оптимизированные сигналы
@receiver(post_save, sender=User)
def handle_user_profile(sender, instance, created, **kwargs):
    """
    Автоматическое создание/обновление профиля пользователя
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)
    else:
        # Безопасное обновление существующего профиля
        if hasattr(instance, "profile"):
            instance.profile.save()
