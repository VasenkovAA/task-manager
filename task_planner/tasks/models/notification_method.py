from django.db import models
from django.core.exceptions import ValidationError
import json


class NotificationMethod(models.Model):
    """
    Модель для представления методов уведомлений.

    Attributes:
        name (CharField): Уникальное название метода
        config (JSONField): Конфигурация метода в JSON-формате
    """

    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Уникальное название метода уведомления (например: email, telegram)",
        verbose_name="Название метода",
        error_messages={"unique": "Метод уведомления с таким названием уже существует"},
    )
    config = models.JSONField(
        default=dict,
        help_text="Конфигурация метода уведомления в формате JSON",
        verbose_name="Конфигурация",
    )

    def __str__(self):
        return self.name

    def clean(self):
        """Валидация данных перед сохранением"""
        super().clean()
        # Нормализация названия
        if self.name:
            self.name = self.name.strip()

        # Проверка уникальности с учетом регистра
        if (
            NotificationMethod.objects.exclude(pk=self.pk)
            .filter(name__iexact=self.name)
            .exists()
        ):
            raise ValidationError(
                {
                    "name": "Метод уведомления с таким названием уже существует (учет регистра не производится)"
                }
            )

        # Валидация JSON-конфигурации
        try:
            json.dumps(self.config)  # Проверка сериализуемости
        except TypeError:
            raise ValidationError({"config": "Некорректный формат JSON-конфигурации"})

    class Meta:
        """
        Метаданные модели NotificationMethod.

        Attributes:
            verbose_name (str): Человекочитаемое имя в единственном числе
            verbose_name_plural (str): Человекочитаемое имя во множественном числе
            ordering (tuple): Порядок сортировки по умолчанию
        """

        verbose_name = "Метод уведомления"
        verbose_name_plural = "Методы уведомления"
        ordering = ("name",)
