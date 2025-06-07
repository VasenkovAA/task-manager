from django.db import models
from django.core.exceptions import ValidationError


class Link(models.Model):
    """
    Модель для представления URL-ссылок.

    Attributes:
        url (URLField): Уникальный URL-адрес
        created_at (DateTimeField): Дата создания ссылки (автозаполнение)
    """

    url = models.URLField(
        max_length=500,
        unique=True,
        help_text="Уникальный URL-адрес",
        verbose_name="URL",
        error_messages={"unique": "Ссылка с таким URL уже существует"},
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Дата создания ссылки",
        verbose_name="Дата создания",
        db_index=True,
    )

    def __str__(self):
        return self.url

    def clean(self):
        """Нормализация URL перед сохранением"""
        super().clean()
        if self.url:
            # Удаление пробелов и приведение к нижнему регистру
            self.url = self.url.strip().lower()

            # Проверка на минимальную длину URL
            if len(self.url) < 10:
                raise ValidationError(
                    {"url": "URL слишком короткий (мин. 10 символов)"}
                )

    class Meta:
        """
        Метаданные модели Link.

        Attributes:
            verbose_name (str): Человекочитаемое имя в единственном числе
            verbose_name_plural (str): Человекочитаемое имя во множественном числе
            ordering (tuple): Порядок сортировки по умолчанию
        """

        verbose_name = "Ссылка"
        verbose_name_plural = "Ссылки"
        ordering = ("-created_at",)
