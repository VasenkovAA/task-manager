from django.db import models
from django.core.exceptions import ValidationError
import re


class Location(models.Model):
    """
    Модель для представления географических местоположений.

    Attributes:
        name (CharField): Название места
        address (TextField): Полный адрес (необязательный)
        coordinates (CharField): Координаты в формате 'широта,долгота' (необязательные)
    """

    name = models.CharField(
        max_length=100,
        help_text="Название места выполнения задачи",
        verbose_name="Название места",
        db_index=True,
    )
    address = models.TextField(
        blank=True, null=True, help_text="Полный адрес места", verbose_name="Адрес"
    )
    coordinates = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Координаты в формате 'широта,долгота'",
        verbose_name="Координаты",
    )

    def __str__(self):
        return f"{self.name} ({self.coordinates})" if self.coordinates else self.name

    def clean(self):
        """Валидация координат перед сохранением"""
        super().clean()
        if self.coordinates:
            # Проверка формата координат
            pattern = r"^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$"
            if not re.match(pattern, self.coordinates.strip()):
                raise ValidationError(
                    {
                        "coordinates": "Некорректный формат координат. Используйте формат: широта,долгота"
                    }
                )

            # Разделение и проверка диапазонов
            try:
                lat, lon = map(float, self.coordinates.split(","))
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    raise ValueError
            except ValueError:
                raise ValidationError(
                    {
                        "coordinates": "Недопустимые значения координат. Широта: -90..90, Долгота: -180..180"
                    }
                )

    class Meta:
        """
        Метаданные модели Location.

        Attributes:
            verbose_name (str): Человекочитаемое имя в единственном числе
            verbose_name_plural (str): Человекочитаемое имя во множественном числе
            ordering (tuple): Порядок сортировки по умолчанию
        """

        verbose_name = "Местоположение"
        verbose_name_plural = "Местоположения"
        ordering = ("name",)
