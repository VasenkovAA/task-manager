from django.db import models


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
        help_text="Уникальное название категории",
    )
    description = models.TextField(
        blank=True, null=True, help_text="Описание категории задач"
    )

    def __str__(self):
        return self.name

    class Meta:
        """
        Метаданные модели TaskCategory.
        
        Attributes:
            verbose_name (str): Человекочитаемое имя в единственном числе
            verbose_name_plural (str): Человекочитаемое имя во множественном числе
        """
        verbose_name = "Категория задач"
        verbose_name_plural = "Категории задач"