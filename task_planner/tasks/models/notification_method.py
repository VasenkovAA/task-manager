from django.db import models


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
        help_text="Название метода уведомления (например: email, telegram)",
    )
    config = models.JSONField(
        default=dict, help_text="Конфигурация метода уведомления в формате JSON"
    )

    def __str__(self):
        return self.name

    class Meta:
        """
        Метаданные модели NotificationMethod.
        
        Attributes:
            verbose_name (str): Человекочитаемое имя в единственном числе
            verbose_name_plural (str): Человекочитаемое имя во множественном числе
        """
        verbose_name = "Метод уведомления"
        verbose_name_plural = "Методы уведомления"
