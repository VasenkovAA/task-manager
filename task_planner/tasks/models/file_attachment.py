from django.db import models
from tasks.models.task import Task

class FileAttachment(models.Model):
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='attachments',
        help_text="Связанная задача"
    )
    file = models.FileField(
        upload_to='task_attachments/%Y/%m/%d/',
        help_text="Прикрепленный файл"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Время загрузки файла"
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Описание файла"
    )

    def __str__(self):
        return f"Вложение {self.id} для задачи {self.task.title}"

    class Meta:
        verbose_name = 'Файловое вложение'
        verbose_name_plural = 'Файловые вложения'