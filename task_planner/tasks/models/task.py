from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.exceptions import ValidationError
from taggit.managers import TaggableManager
from simple_history.models import HistoricalRecords
from tasks.models.task_category import TaskCategory
from tasks.models.location import Location
from tasks.models.notification_method import NotificationMethod
from tasks.models.link import Link
import json

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
        help_text="Уникальное название задачи (макс. 200 символов)",
        verbose_name="Название задачи",
        db_index=True  # Индекс для частого поиска по названию
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Подробное описание задачи, поддерживающее форматирование",
        verbose_name="Описание задачи"
    )
    priority = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Приоритет по 10-балльной шкале (1 - низший, 10 - высший)",
        verbose_name="Приоритет"
    )

    # Статус и прогресс
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="waiting",
        help_text="Текущий статус выполнения задачи",
        verbose_name="Статус"
    )
    progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Прогресс выполнения в процентах (0-100%)",
        verbose_name="Прогресс выполнения"
    )

    # Временные параметры
    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        help_text="Автоматически устанавливается при создании задачи",
        verbose_name="Дата создания",
        db_index=True  # Индекс для сортировки
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Автоматически обновляется при каждом сохранении",
        verbose_name="Дата обновления"
    )
    start_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Планируемая дата и время начала выполнения",
        verbose_name="Дата начала"
    )
    end_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Планируемая дата и время завершения",
        verbose_name="Дата завершения"
    )
    deadline = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Крайний срок выполнения (дедлайн)",
        verbose_name="Дедлайн",
        db_index=True  # Индекс для частых проверок дедлайнов
    )
    deleted_at = models.DateTimeField(
        blank=True,
        null=True,
        editable=False,
        help_text="Заполняется автоматически при удалении задачи",
        verbose_name="Дата удаления"
    )

    # Связи и зависимости
    dependencies = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="dependent_tasks",
        help_text="Задачи, которые должны быть выполнены ДО текущей",
        verbose_name="Зависимости"
    )
    categories = models.ManyToManyField(
        TaskCategory,
        blank=True,
        help_text="Категории для классификации задач",
        verbose_name="Категории",
        related_name="tasks"
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Физическое место выполнения задачи",
        verbose_name="Местоположение"
    )

    # Ответственные
    author = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="created_tasks",
        help_text="Пользователь, создавший задачу",
        verbose_name="Автор"
    )
    last_editor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="edited_tasks",
        blank=True,
        null=True,
        help_text="Последний пользователь, внёсший изменения",
        verbose_name="Последний редактор"
    )
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
        blank=True,
        null=True,
        help_text="Основной исполнитель задачи",
        verbose_name="Исполнитель"
    )

    # Дополнительные параметры
    complexity = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Оценка сложности по 10-балльной шкале",
        verbose_name="Сложность"
    )
    risk_level = models.CharField(
        max_length=10,
        choices=RISK_LEVEL_CHOICES,
        default="low",
        help_text="Оценка рисков при выполнении задачи",
        verbose_name="Уровень риска"
    )

    # Флаги состояния
    is_ready = models.BooleanField(
        default=False,
        help_text="Готовность к выполнению (все зависимости выполнены)",
        verbose_name="Готова к выполнению"
    )
    is_recurring = models.BooleanField(
        default=False,
        help_text="Повторяющаяся задача (например, ежедневная)",
        verbose_name="Повторяющаяся"
    )
    needs_approval = models.BooleanField(
        default=False,
        help_text="Требует подтверждения завершения руководителем",
        verbose_name="Требует подтверждения"
    )
    is_template = models.BooleanField(
        default=False,
        help_text="Используется как шаблон для создания новых задач",
        verbose_name="Шаблон"
    )
    is_deleted = models.BooleanField(
        default=False,
        editable=False,
        help_text="Помечена как удалённая (мягкое удаление)",
        verbose_name="Удалена"
    )

    # Данные для анализа производительности
    estimated_time = models.DurationField(
        blank=True,
        null=True,
        help_text="Планируемая продолжительность выполнения",
        verbose_name="Оценка времени"
    )
    actual_time = models.DurationField(
        blank=True,
        null=True,
        help_text="Фактическое время, затраченное на выполнение",
        verbose_name="Фактическое время"
    )
    quality_rating = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Оценка качества выполнения по 5-балльной шкале",
        verbose_name="Оценка качества"
    )
    version = models.IntegerField(
        default=1,
        editable=False,
        help_text="Версия объекта (инкрементируется при изменениях)",
        verbose_name="Версия"
    )

    # Финансовые и системные атрибуты
    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Выделенный бюджет в валюте системы",
        verbose_name="Бюджет"
    )
    cancel_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Причина отмены задачи (обязателен при статусе 'canceled')",
        verbose_name="Причина отмены"
    )

    # Специфичные поля
    time_intervals = models.JSONField(
        default=list,
        help_text="Диапазоны времени выполнения в формате JSON",
        blank=True,
        null=True,
        verbose_name="Временные интервалы"
    )
    reminders = models.JSONField(
        default=list,
        help_text="Напоминания в формате [{'time': datetime, 'method': id}]",
        blank=True,
        null=True,
        verbose_name="Напоминания"
    )
    repeat_interval = models.DurationField(
        blank=True,
        null=True,
        help_text="Интервал повторения (для периодических задач)",
        verbose_name="Интервал повторения"
    )
    next_activation = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Дата следующего выполнения (для периодических задач)",
        verbose_name="Следующая активация"
    )

    # Системы классификации и истории
    tags = TaggableManager(
        blank=True,
        help_text="Гибкая система тегов для категоризации задач",
        verbose_name="Теги"
    )
    history = HistoricalRecords(
        excluded_fields=["version", "is_deleted", "deleted_at"],
        inherit=True,
        help_text="Автоматическое ведение истории изменений",
        verbose_name="История изменений"
    )

    # Связи с другими моделями
    notifications = models.ManyToManyField(
        NotificationMethod,
        blank=True,
        help_text="Методы уведомления о событиях задачи",
        verbose_name="Методы уведомления",
        related_name="tasks"
    )
    links = models.ManyToManyField(
        Link,
        through="TaskLink",
        blank=True,
        help_text="Связанные внешние ресурсы и документы",
        verbose_name="Ссылки"
    )

    def __str__(self):
        """Строковое представление задачи в формате: Название (Статус)"""
        return f"{self.title} ({self.get_status_display()})"

    def clean(self):
        """Расширенная валидация перед сохранением"""
        super().clean()
        
        # Валидация временных интервалов
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError(
                {"end_date": "Дата завершения не может быть раньше даты начала"}
            )
            
        if self.deadline and self.deadline < timezone.now() and not self.is_deleted:
            raise ValidationError(
                {"deadline": "Дедлайн не может быть в прошлом для активной задачи"}
            )
            
        # Проверка причины отмены
        if self.status == "canceled" and not self.cancel_reason:
            raise ValidationError(
                {"cancel_reason": "Требуется указать причину отмены задачи"}
            )
            
        # Валидация JSON-полей
        for field in ["reminders", "time_intervals"]:
            value = getattr(self, field)
            if value:
                try:
                    if not isinstance(value, list):
                        raise ValidationError(
                            {field: "Значение должно быть списком"}
                        )
                    json.dumps(value)  # Проверка сериализуемости
                except (TypeError, ValueError):
                    raise ValidationError(
                        {field: "Некорректный JSON-формат"}
                    )

        # Проверка прогресса при завершении
        if self.status == "done" and self.progress < 100:
            raise ValidationError(
                {"progress": "Прогресс должен быть 100% для завершенной задачи"}
            )

    def delete(self, *args, **kwargs):
        """
        Реализация мягкого удаления задачи.
        
        Вместо физического удаления из базы:
        1. Помечает задачу как удалённую (is_deleted=True)
        2. Устанавливает дату удаления (deleted_at=текущее время)
        3. Сохраняет объект
        
        Original DELETE-операции не выполняет.
        """
        if not self.is_deleted:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.status = "canceled"  # Автоматическая отмена при удалении
            self.save()

    def restore(self):
        """Восстановление мягко удаленной задачи"""
        if self.is_deleted:
            self.is_deleted = False
            self.deleted_at = None
            self.status = "waiting"  # Сброс статуса при восстановлении
            self.save()

    @property
    def is_overdue(self):
        """Проверка, просрочена ли задача"""
        if self.deadline and not self.is_deleted:
            return timezone.now() > self.deadline and self.status != "done"
        return False

    @property
    def outgoing_dependencies(self):
        """
        Задачи, которые зависят от текущей (обратная зависимость).
        
        Returns:
            QuerySet: Задачи, где текущая задача указана как зависимость
        """
        return self.dependent_tasks.all()

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
            
            # Дополнительные индексы для частых запросов
            models.Index(fields=["priority"]),
            models.Index(fields=["assignee"]),
            models.Index(fields=["is_ready"]),
        ]
        
        # Дополнительные параметры
        permissions = [
            ("can_approve_task", "Может подтверждать завершение задач"),
            ("can_assign_task", "Может назначать задачи другим пользователям"),
            ("can_restore_task", "Может восстанавливать удаленные задачи"),
        ]