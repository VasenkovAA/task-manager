from django.db import models


class Location(models.Model):
    """
    Модель для представления географических местоположений.
    
    Attributes:
        name (CharField): Название места
        address (TextField): Полный адрес (необязательный)
        coordinates (CharField): Координаты в формате 'широта,долгота' (необязательные)
    """
    name = models.CharField(
        max_length=100, help_text="Название места выполнения задачи"
    )
    address = models.TextField(blank=True, null=True, help_text="Полный адрес места")
    coordinates = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Координаты в формате 'широта,долгота'",
    )

    def __str__(self):
        return f"{self.name} ({self.coordinates})"

    class Meta:
        """
        Метаданные модели Location.
        
        Attributes:
            verbose_name (str): Человекочитаемое имя в единственном числе
            verbose_name_plural (str): Человекочитаемое имя во множественном числе
        """
        verbose_name = "Местоположение"
        verbose_name_plural = "Местоположения"
