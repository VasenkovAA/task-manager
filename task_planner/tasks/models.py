from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from taggit.managers import TaggableManager
from simple_history.models import HistoricalRecords

User = get_user_model()

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

class NotificationMethod(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Название метода уведомления (например: email, telegram)"
    )
    config = models.JSONField(
        default=dict,
        help_text="Конфигурация метода уведомления в формате JSON"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Метод уведомления'
        verbose_name_plural = 'Методы уведомления'

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

class Link(models.Model):
    url = models.URLField(
        max_length=500,
        unique=True,
        help_text="Уникальный URL-адрес"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Дата создания ссылки"
    )

    def __str__(self):
        return self.url

    class Meta:
        verbose_name = 'Ссылка'
        verbose_name_plural = 'Ссылки'

class Task(models.Model):
    STATUS_CHOICES = [
        ('waiting', 'Ожидает начала'),
        ('progress', 'В процессе'),
        ('done', 'Завершена'),
        ('canceled', 'Отменена'),
    ]
    
    RISK_LEVEL_CHOICES = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
    ]

    # Основные атрибуты
    title = models.CharField(
        max_length=200,
        unique=True,
        error_messages={'unique': 'Задача с таким названием уже существует'},
        help_text="Уникальное название задачи"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Подробное описание задачи"
    )
    priority = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Приоритет по 10-балльной шкале"
    )
    
    # Статус и прогресс
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='waiting',
        help_text="Текущий статус выполнения задачи"
    )
    progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Прогресс выполнения в процентах"
    )
    
    # Временные параметры
    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        help_text="Дата и время создания задачи"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Дата и время последнего обновления"
    )
    start_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Планируемая дата и время начала выполнения"
    )
    end_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Планируемая дата и время завершения"
    )
    deadline = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Крайний срок выполнения задачи"
    )
    deleted_at = models.DateTimeField(
        blank=True,
        null=True,
        editable=False,
        help_text="Дата и время удаления задачи"
    )
    
    # Связи и зависимости
    dependencies = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        help_text="Задачи, от которых зависит текущая"
    )
    categories = models.ManyToManyField(
        TaskCategory,
        blank=True,
        help_text="Категории задачи"
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Место выполнения задачи"
    )
    
    # Ответственные
    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_tasks',
        help_text="Создатель задачи"
    )
    last_editor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='edited_tasks',
        blank=True,
        null=True,
        help_text="Последний пользователь, редактировавший задачу"
    )
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='assigned_tasks',
        blank=True,
        null=True,
        help_text="Ответственный исполнитель"
    )
    
    # Дополнительные параметры
    complexity = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Сложность задачи по 10-балльной шкале"
    )
    risk_level = models.CharField(
        max_length=10,
        choices=RISK_LEVEL_CHOICES,
        default='low',
        help_text="Уровень риска выполнения задачи"
    )
    
    # Флаги
    is_ready = models.BooleanField(
        default=False,
        help_text="Можно начинать выполнение"
    )
    is_recurring = models.BooleanField(
        default=False,
        help_text="Периодическая задача"
    )
    needs_approval = models.BooleanField(
        default=False,
        help_text="Требует утверждения завершения"
    )
    is_template = models.BooleanField(
        default=False,
        help_text="Использовать как шаблон"
    )
    is_deleted = models.BooleanField(
        default=False,
        editable=False,
        help_text="Флаг удаления задачи"
    )
    
    # Данные для анализа
    estimated_time = models.DurationField(
        blank=True,
        null=True,
        help_text="Планируемое время выполнения"
    )
    actual_time = models.DurationField(
        blank=True,
        null=True,
        help_text="Фактическое время выполнения"
    )
    quality_rating = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Оценка качества выполнения (1-5)"
    )
    version = models.IntegerField(
        default=1,
        editable=False,
        help_text="Версия задачи (счетчик изменений)"
    )
    
    # Дополнительные данные
    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Бюджет задачи"
    )
    cancel_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Причина отмены задачи"
    )
    
    # Специфичные поля
    time_intervals = models.JSONField(
        default=list,
        help_text="Временные интервалы выполнения задачи"
    )
    reminders = models.JSONField(
        default=list,
        help_text="Напоминания о задаче"
    )
    repeat_interval = models.DurationField(
        blank=True,
        null=True,
        help_text="Интервал повторения для периодических задач"
    )
    next_activation = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Дата следующей активации периодической задачи"
    )
    
    # Теги и история
    tags = TaggableManager(
        blank=True,
        help_text="Теги для классификации задач"
    )
    history = HistoricalRecords(
        excluded_fields=['version', 'is_deleted', 'deleted_at'],
        inherit=True,
        help_text="История изменений задачи"
    )
    
    # Связи ManyToMany
    notifications = models.ManyToManyField(
        NotificationMethod,
        blank=True,
        help_text="Способы уведомления о задаче"
    )
    links = models.ManyToManyField(
        Link,
        through='TaskLink',
        blank=True,
        help_text="Связанные URL-ссылки"
    )

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    class Meta:
        verbose_name = 'Задача'
        verbose_name_plural = 'Задачи'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_deleted', 'status']),
            models.Index(fields=['deadline']),
        ]

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