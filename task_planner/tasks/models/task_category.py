from django.db import models

class TaskCategory(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        error_messages={'unique': 'Категория с таким названием уже существует'},
        help_text="Уникальное название категории"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Описание категории задач"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория задач'
        verbose_name_plural = 'Категории задач'