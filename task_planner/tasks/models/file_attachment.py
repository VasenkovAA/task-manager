from django.db import models
from django.core.exceptions import ValidationError
from tasks.models.task import Task
import os


class FileAttachment(models.Model):
    """
    Модель для представления файловых вложений к задачам.

    Attributes:
        task (ForeignKey): Связанная задача (Task)
        file (FileField): Поле для загрузки файла
        uploaded_at (DateTimeField): Дата/время загрузки файла (автозаполнение)
        description (CharField): Описание файла (необязательное)
    """

    # Разрешенные MIME-типы
    ALLOWED_TYPES = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain",
    ]

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="attachments",
        help_text="Связанная задача",
        verbose_name="Задача",
    )
    file = models.FileField(
        upload_to="task_attachments/%Y/%m/%d/",
        help_text="Прикрепленный файл (макс. 10 МБ)",
        verbose_name="Файл",
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Время загрузки файла",
        verbose_name="Дата загрузки",
        db_index=True,
    )
    description = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Описание файла (макс. 200 символов)",
        verbose_name="Описание",
    )

    def __str__(self):
        return f"Вложение {self.id} для задачи {self.task.title}"

    def clean(self):
        """Валидация файла перед сохранением"""
        super().clean()

        if self.file:
            # Проверка размера файла (макс. 30 МБ)
            if self.file.size > 30 * 1024 * 1024:
                raise ValidationError({"file": "Размер файла превышает 30 МБ"})

            # Проверка расширения файла
            ext = os.path.splitext(self.file.name)[1].lower()
            if ext not in [
                ".pdf",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".jpg",
                ".jpeg",
                ".png",
                ".txt",
            ]:
                raise ValidationError(
                    {
                        "file": "Неподдерживаемый тип файла. Разрешены: PDF, DOC/DOCX, XLS/XLSX, JPG/PNG, TXT"
                    }
                )

    class Meta:
        """
        Метаданные модели FileAttachment.

        Attributes:
            verbose_name (str): Человекочитаемое имя в единственном числе
            verbose_name_plural (str): Человекочитаемое имя во множественном числе
            ordering (tuple): Порядок сортировки по умолчанию
        """

        verbose_name = "Файловое вложение"
        verbose_name_plural = "Файловые вложения"
        ordering = ("-uploaded_at",)
