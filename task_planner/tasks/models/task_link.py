from django.db import models
from tasks.models.task import Task
from tasks.models.link import Link


class TaskLink(models.Model):
    """
    Промежуточная модель для связи задач и ссылок.
    
    Attributes:
        task (ForeignKey): Связанная задача
        link (ForeignKey): Связанная ссылка
        description (CharField): Описание связи (необязательное)
        created_at (DateTimeField): Дата создания связи (автозаполнение)
    """
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, help_text="Связанная задача"
    )
    link = models.ForeignKey(
        Link, on_delete=models.CASCADE, help_text="Связанная ссылка"
    )
    description = models.CharField(
        max_length=200, blank=True, null=True, help_text="Описание связи"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Дата создания связи"
    )

    class Meta:
        """
        Метаданные модели TaskLink.
        
        Attributes:
            unique_together (tuple): Комбинированная уникальность полей
            verbose_name (str): Человекочитаемое имя в единственном числе
            verbose_name_plural (str): Человекочитаемое имя во множественном числе
        """
        unique_together = ("task", "link")
        verbose_name = "Связь задачи со ссылкой"
        verbose_name_plural = "Связи задач со ссылками"
