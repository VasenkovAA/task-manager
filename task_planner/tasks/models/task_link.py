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
        Task,
        on_delete=models.CASCADE,
        help_text="Связанная задача",
        related_name="task_links",
    )
    link = models.ForeignKey(
        Link,
        on_delete=models.CASCADE,
        help_text="Связанная ссылка",
        related_name="link_tasks",
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Описание связи (макс. 200 символов)",
        verbose_name="Описание связи",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Дата автоматического создания связи",
        verbose_name="Дата создания",
        db_index=True,
    )

    def __str__(self):
        return f"{self.task} ↔ {self.link}"

    class Meta:
        """
        Метаданные модели TaskLink.

        Attributes:
            unique_together (tuple): Комбинированная уникальность полей
            verbose_name (str): Человекочитаемое имя в единственном числе
            verbose_name_plural (str): Человекочитаемое имя во множественном числе
            indexes (list): Дополнительные индексы
            ordering (tuple): Порядок сортировки по умолчанию
        """

        unique_together = ("task", "link")
        verbose_name = "Связь задачи со ссылкой"
        verbose_name_plural = "Связи задач со ссылками"
        indexes = [
            models.Index(fields=["created_at"]),
        ]
        ordering = ("-created_at",)
