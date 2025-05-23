from django.db import models
from tasks.models.task import Task
from tasks.models.link import Link

class TaskLink(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        help_text="Связанная задача"
    )
    link = models.ForeignKey(
        Link,
        on_delete=models.CASCADE,
        help_text="Связанная ссылка"
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Описание связи"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Дата создания связи"
    )

    class Meta:
        unique_together = ('task', 'link')
        verbose_name = 'Связь задачи со ссылкой'
        verbose_name_plural = 'Связи задач со ссылками'