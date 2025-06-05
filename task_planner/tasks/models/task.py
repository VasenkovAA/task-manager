from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from taggit.managers import TaggableManager
from simple_history.models import HistoricalRecords
from tasks.models.task_category import TaskCategory
from tasks.models.location import Location
from tasks.models.notification_method import NotificationMethod
from tasks.models.link import Link

User = get_user_model()


class Task(models.Model):
    """
    Основная модель системы, представляющая задачу с комплексными атрибутами управления.
    
    Включает:
    - Систему статусов выполнения
    - Иерархию зависимостей между задачами
    - Категоризацию и тегирование
    - Управление временными параметрами
    - Назначение ответственных
    - Систему уведомлений
    - Историю изменений
    - Механизм мягкого удаления
    
    Статусы задачи:
        waiting: Ожидает начала выполнения
        progress: Активно выполняется
        done: Успешно завершена
        canceled: Отменена
    
    Уровни риска:
        low: Низкий риск выполнения
        medium: Средний риск
        high: Высокий риск
    """
    
    # Константы статусов и уровней риска
    STATUS_CHOICES = [
        ("waiting", "Ожидает начала"),
        ("progress", "В процессе"),
        ("done", "Завершена"),
        ("canceled", "Отменена"),
    ]

    RISK_LEVEL_CHOICES = [
        ("low", "Низкий"),
        ("medium", "Средний"),
        ("high", "Высокий"),
    ]

    # Основные атрибуты
    title = models.CharField(
        max_length=200,
        unique=True,
        error_messages={"unique": "Задача с таким названием уже существует"},
        help_text="Уникальное название задачи (макс. 200 символов)"
    )
    description = models.TextField(
        blank=True, null=True,
        help_text="Подробное описание задачи, поддерживающее форматирование"
    )
    priority = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Приоритет по 10-балльной шкале (1 - низший, 10 - высший)"
    )

    # Статус и прогресс
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="waiting",
        help_text="Текущий статус выполнения задачи"
    )
    progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Прогресс выполнения в процентах (0-100%)"
    )

    # Временные параметры
    created_at = models.DateTimeField(
        auto_now_add=True, editable=False,
        help_text="Автоматически устанавливается при создании задачи"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Автоматически обновляется при каждом сохранении"
    )
    start_date = models.DateTimeField(
        blank=True, null=True,
        help_text="Планируемая дата и время начала выполнения"
    )
    end_date = models.DateTimeField(
        blank=True, null=True,
        help_text="Планируемая дата и время завершения"
    )
    deadline = models.DateTimeField(
        blank=True, null=True,
        help_text="Крайний срок выполнения (дедлайн)"
    )
    deleted_at = models.DateTimeField(
        blank=True, null=True, editable=False,
        help_text="Заполняется автоматически при удалении задачи"
    )

    # Связи и зависимости
    dependencies = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="task_dependencies",
        help_text="Задачи, которые должны быть выполнены ДО текущей"
    )
    categories = models.ManyToManyField(
        TaskCategory, blank=True,
        help_text="Категории для классификации задач"
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Физическое место выполнения задачи"
    )

    # Ответственные
    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_tasks",
        help_text="Пользователь, создавший задачу"
    )
    last_editor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="edited_tasks",
        blank=True,
        null=True,
        help_text="Последний пользователь, внёсший изменения"
    )
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
        blank=True,
        null=True,
        help_text="Основной исполнитель задачи"
    )

    # Дополнительные параметры
    complexity = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Оценка сложности по 10-балльной шкале"
    )
    risk_level = models.CharField(
        max_length=10,
        choices=RISK_LEVEL_CHOICES,
        default="low",
        help_text="Оценка рисков при выполнении задачи"
    )

    # Флаги состояния
    is_ready = models.BooleanField(
        default=False,
        help_text="Готовность к выполнению (все зависимости выполнены)"
    )
    is_recurring = models.BooleanField(
        default=False,
        help_text="Повторяющаяся задача (например, ежедневная)"
    )
    needs_approval = models.BooleanField(
        default=False,
        help_text="Требует подтверждения завершения руководителем"
    )
    is_template = models.BooleanField(
        default=False,
        help_text="Используется как шаблон для создания новых задач"
    )
    is_deleted = models.BooleanField(
        default=False, editable=False,
        help_text="Помечена как удалённая (мягкое удаление)"
    )

    # Данные для анализа производительности
    estimated_time = models.DurationField(
        blank=True, null=True,
        help_text="Планируемая продолжительность выполнения"
    )
    actual_time = models.DurationField(
        blank=True, null=True,
        help_text="Фактическое время, затраченное на выполнение"
    )
    quality_rating = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Оценка качества выполнения по 5-балльной шкале"
    )
    version = models.IntegerField(
        default=1, editable=False,
        help_text="Версия объекта (инкрементируется при изменениях)"
    )

    # Финансовые и системные атрибуты
    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Выделенный бюджет в валюте системы"
    )
    cancel_reason = models.TextField(
        blank=True, null=True,
        help_text="Причина отмены задачи (обязателен при статусе 'canceled')"
    )

    # Специфичные поля
    time_intervals = models.JSONField(
        default=list,
        help_text="Диапазоны времени выполнения в формате JSON",
        blank=True,
        null=True,
    )
    reminders = models.JSONField(
        default=list,
        help_text="Напоминания в формате [{'time': datetime, 'method': id}]",
        blank=True,
        null=True,
    )
    repeat_interval = models.DurationField(
        blank=True, null=True,
        help_text="Интервал повторения (для периодических задач)"
    )
    next_activation = models.DateTimeField(
        blank=True, null=True,
        help_text="Дата следующего выполнения (для периодических задач)"
    )

    # Системы классификации и истории
    tags = TaggableManager(
        blank=True,
        help_text="Гибкая система тегов для категоризации задач"
    )
    history = HistoricalRecords(
        excluded_fields=["version", "is_deleted", "deleted_at"],
        inherit=True,
        help_text="Автоматическое ведение истории изменений"
    )

    # Связи с другими моделями
    notifications = models.ManyToManyField(
        NotificationMethod, blank=True,
        help_text="Методы уведомления о событиях задачи"
    )
    links = models.ManyToManyField(
        Link, through="TaskLink", blank=True,
        help_text="Связанные внешние ресурсы и документы"
    )

    def __str__(self):
        """Строковое представление задачи в формате: Название (Статус)"""
        return f"{self.title} ({self.get_status_display()})"

    def delete(self, *args, **kwargs):
        """
        Реализация мягкого удаления задачи.
        
        Вместо физического удаления из базы:
        1. Помечает задачу как удалённую (is_deleted=True)
        2. Устанавливает дату удаления (deleted_at=текущее время)
        3. Сохраняет объект
        
        Original DELETE-операции не выполняет.
        """
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    class Meta:
        """Мета-конфигурация модели задач"""
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ["-created_at"]
        indexes = [
            # Составной индекс для фильтрации по статусу и удалённым задачам
            models.Index(fields=["is_deleted", "status"]),
            
            # Индекс для быстрого поиска по дедлайну
            models.Index(fields=["deadline"]),
        ]
        
        # Дополнительные параметры
        permissions = [
            ("can_approve_task", "Может подтверждать завершение задач"),
            ("can_assign_task", "Может назначать задачи другим пользователям"),
        ]

    @property
    def outgoing_dependencies(self):
        """
        Задачи, которые зависят от текущей (обратная зависимость).
        
        Returns:
            QuerySet: Задачи, где текущая задача указана как зависимость
        """
        return self.task_dependencies.all()