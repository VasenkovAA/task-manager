from django.db import models


class NotificationMethod(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Название метода уведомления (например: email, telegram)",
    )
    config = models.JSONField(
        default=dict, help_text="Конфигурация метода уведомления в формате JSON"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Метод уведомления"
        verbose_name_plural = "Методы уведомления"
