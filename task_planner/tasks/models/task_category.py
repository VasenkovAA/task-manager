from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class TaskCategory(models.Model):
    """
    Модель категорий для классификации задач.

    Attributes:
        name (CharField): Уникальное название категории
        description (TextField): Описание категории (необязательное)
    """

    name = models.CharField(
        max_length=50,
        unique=True,
        error_messages={"unique": "Категория с таким названием уже существует"},
        help_text="Уникальное название категории (макс. 50 символов)",
        verbose_name="Название категории",
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Описание категории задач",
        verbose_name="Описание",
    )

    def __str__(self):
        return self.name

    def clean(self):
        """Автоматическая очистка и валидация данных перед сохранением"""
        super().clean()
        # Нормализация названия
        if self.name:
            self.name = self.name.strip()

        # Валидация уникальности с учетом регистра
        if (
            TaskCategory.objects.exclude(pk=self.pk)
            .filter(name__iexact=self.name)
            .exists()
        ):
            raise ValidationError(
                {
                    "name": _(
                        "Категория с таким названием уже существует (учет регистра не производится)"
                    )
                }
            )

    class Meta:
        """
        Метаданные модели TaskCategory.

        Attributes:
            verbose_name (str): Человекочитаемое имя в единственном числе
            verbose_name_plural (str): Человекочитаемое имя во множественном числе
            ordering (tuple): Порядок сортировки по умолчанию
        """

        verbose_name = "Категория задач"
        verbose_name_plural = "Категории задач"
        ordering = ("name",)
