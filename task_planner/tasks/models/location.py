from django.db import models

class Location(models.Model):
    name = models.CharField(
        max_length=100,
        help_text="Название места выполнения задачи"
    )
    address = models.TextField(
        blank=True,
        null=True,
        help_text="Полный адрес места"
    )
    coordinates = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Координаты в формате 'широта,долгота'"
    )

    def __str__(self):
        return f"{self.name} ({self.coordinates})"

    class Meta:
        verbose_name = 'Местоположение'
        verbose_name_plural = 'Местоположения'