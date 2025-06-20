from time import timezone
from django.contrib import admin
from django.utils.html import format_html
from simple_history.admin import SimpleHistoryAdmin
from .models import (
    TaskCategory,
    NotificationMethod,
    Location,
    Link,
    Task,
    TaskLink,
    FileAttachment,
)
from django.utils.translation import gettext_lazy as _
from django import forms
from django.contrib import messages
from django.utils.html import escape
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.text import Truncator
from django.utils.safestring import mark_safe
from django.db.models import Count
from django.contrib.admin import SimpleListFilter
from django.db import models




@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    """Административный интерфейс для категорий задач"""

    list_display = ["id", "name", "description_short"]
    search_fields = ["name"]
    list_per_page = 20
    ordering = ["name"]

    def description_short(self, obj):
        """Сокращенное описание для отображения в списке"""
        return (
            obj.description[:50] + "..."
            if obj.description and len(obj.description) > 50
            else obj.description
        )

    description_short.short_description = _("Описание")

    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).only("id", "name", "description")


@admin.register(NotificationMethod)
class NotificationMethodAdmin(admin.ModelAdmin):
    """Административный интерфейс для методов уведомления"""

    list_display = ["id", "name", "config_preview"]
    search_fields = ["name"]
    list_per_page = 20
    readonly_fields = ["config_preview"]

    def config_preview(self, obj):
        """Предварительный просмотр JSON-конфигурации"""
        return format_html("<pre>{}</pre>", str(obj.config)[:100])

    config_preview.short_description = _("Конфигурация (предпросмотр)")

    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).defer("config")


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """Административный интерфейс для местоположений"""

    list_display = ["id", "name", "address_short", "coordinates"]
    search_fields = ["name", "address"]
    list_per_page = 20

    def address_short(self, obj):
        """Сокращенный адрес для отображения в списке"""
        return (
            obj.address[:50] + "..."
            if obj.address and len(obj.address) > 50
            else obj.address
        )

    address_short.short_description = _("Адрес")

    def get_queryset(self, request):
        """Оптимизация запросов"""
        return (
            super().get_queryset(request).only("id", "name", "address", "coordinates")
        )


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    """Административный интерфейс для ссылок"""

    list_display = ["id", "url_truncated", "created_at"]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"
    search_fields = ["url"]
    list_per_page = 20

    def url_truncated(self, obj):
        """Сокращенный URL для отображения в списке"""
        return obj.url[:60] + "..." if len(obj.url) > 60 else obj.url

    url_truncated.short_description = _("URL")

    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).only("id", "url", "created_at")


class TaskLinkInline(admin.TabularInline):
    """Инлайн для связи задач и ссылок"""

    model = TaskLink
    extra = 0
    autocomplete_fields = ["link"]
    verbose_name = _("Связанная ссылка")
    verbose_name_plural = _("Связанные ссылки")

    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).select_related("link")


class FileAttachmentInline(admin.TabularInline):
    """Инлайн для файловых вложений"""

    model = FileAttachment
    extra = 0
    readonly_fields = ["file_preview", "uploaded_at"]
    fields = ["file", "file_preview", "description", "uploaded_at"]
    verbose_name = _("Файловое вложение")
    verbose_name_plural = _("Файловые вложения")

    def file_preview(self, obj):
        """Предпросмотр файла"""
        if obj.file:
            return format_html(
                '<a href="{0}" target="_blank">{1}</a>',
                obj.file.url,
                obj.file.name.split("/")[-1],
            )
        return "-"

    file_preview.short_description = _("Просмотр")

    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).defer("task")


class DependencyFilter(admin.SimpleListFilter):
    """Фильтр для задач с зависимостями"""

    title = _("Зависимости")
    parameter_name = "dependencies"

    def lookups(self, request, model_admin):
        return (
            ("has_dependencies", _("С зависимостями")),
            ("no_dependencies", _("Без зависимостей")),
        )

    def queryset(self, request, queryset):
        if self.value() == "has_dependencies":
            return queryset.filter(dependencies__isnull=False).distinct()
        if self.value() == "no_dependencies":
            return queryset.filter(dependencies__isnull=True)




class DependencyFilter(SimpleListFilter):
    """Фильтр по наличию зависимостей"""
    title = _('Зависимости')
    parameter_name = 'dependencies'

    def lookups(self, request, model_admin):
        return (
            ('with_deps', _('С зависимостями')),
            ('without_deps', _('Без зависимостей')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'with_deps':
            return queryset.annotate(dep_count=Count('dependencies')).filter(dep_count__gt=0)
        if self.value() == 'without_deps':
            return queryset.annotate(dep_count=Count('dependencies')).filter(dep_count=0)
        return queryset


class ProgressFilter(SimpleListFilter):
    """Фильтр по прогрессу выполнения"""
    title = _('Прогресс выполнения')
    parameter_name = 'progress'

    def lookups(self, request, model_admin):
        return (
            ('0-25', _('0-25%')),
            ('25-50', _('25-50%')),
            ('50-75', _('50-75%')),
            ('75-100', _('75-100%')),
            ('100', _('100% (Завершено)')),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == '0-25':
            return queryset.filter(progress__range=(0, 25))
        if value == '25-50':
            return queryset.filter(progress__range=(25, 50))
        if value == '50-75':
            return queryset.filter(progress__range=(50, 75))
        if value == '75-100':
            return queryset.filter(progress__range=(75, 100))
        if value == '100':
            return queryset.filter(progress=100)
        return queryset


class TaskLinkInline(admin.TabularInline):
    """Инлайн для связанных ссылок"""
    model = TaskLink
    extra = 1
    fields = ['link', 'description']
    verbose_name = _("Связанная ссылка")
    verbose_name_plural = _("Связанные ссылки")


class FileAttachmentInline(admin.TabularInline):
    """Инлайн для прикрепленных файлов"""
    model = FileAttachment
    extra = 1
    fields = ['file', 'description']
    verbose_name = _("Прикрепленный файл")
    verbose_name_plural = _("Прикрепленные файлы")





class DependencyFilter(SimpleListFilter):
    """Фильтр по наличию зависимостей"""
    title = _('Зависимости')
    parameter_name = 'dependencies'

    def lookups(self, request, model_admin):
        return (
            ('with_deps', _('С зависимостями')),
            ('without_deps', _('Без зависимостей')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'with_deps':
            return queryset.annotate(dep_count=Count('dependencies')).filter(dep_count__gt=0)
        if self.value() == 'without_deps':
            return queryset.annotate(dep_count=Count('dependencies')).filter(dep_count=0)
        return queryset


class ProgressFilter(SimpleListFilter):
    """Фильтр по прогрессу выполнения"""
    title = _('Прогресс выполнения')
    parameter_name = 'progress'

    def lookups(self, request, model_admin):
        return (
            ('0-25', _('0-25%')),
            ('25-50', _('25-50%')),
            ('50-75', _('50-75%')),
            ('75-100', _('75-100%')),
            ('100', _('100% (Завершено)')),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == '0-25':
            return queryset.filter(progress__range=(0, 25))
        if value == '25-50':
            return queryset.filter(progress__range=(25, 50))
        if value == '50-75':
            return queryset.filter(progress__range=(50, 75))
        if value == '75-100':
            return queryset.filter(progress__range=(75, 100))
        if value == '100':
            return queryset.filter(progress=100)
        return queryset


class TaskLinkInline(admin.TabularInline):
    """Инлайн для связанных ссылок"""
    model = TaskLink
    extra = 1
    fields = ['link', 'description']
    verbose_name = _("Связанная ссылка")
    verbose_name_plural = _("Связанные ссылки")


class FileAttachmentInline(admin.TabularInline):
    """Инлайн для прикрепленных файлов"""
    model = FileAttachment
    extra = 1
    fields = ['file', 'description']
    verbose_name = _("Прикрепленный файл")
    verbose_name_plural = _("Прикрепленные файлы")


@admin.register(Task)
class TaskAdmin(SimpleHistoryAdmin):
    """Административный интерфейс для управления задачами"""
    # Конфигурация отображения списка задач
    list_display = [
        "id", "title_short", "status_badge", "progress_bar",
        "priority", "formatted_deadline", "assignee_name",
        "is_overdue_icon", "is_ready_icon", "dependencies_count"
    ]
    list_display_links = ["id", "title_short"]
    list_filter = [
        "status", "priority", "risk_level", "is_deleted",
        "is_ready", "is_recurring", DependencyFilter, ProgressFilter,
        ("categories", admin.RelatedOnlyFieldListFilter),
        ("tags", admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        "title", "description", "assignee__username", 
        "assignee__email", "tags__name", "categories__name"
    ]
    readonly_fields = [
        "created_at", "updated_at", "deleted_at", "version",
        "outgoing_dependencies", "is_overdue", "progress_bar",
        "is_deleted", "status_history"
    ]
    date_hierarchy = "deadline"
    filter_horizontal = ["dependencies", "categories", "notifications"]
    raw_id_fields = ["author", "last_editor", "assignee", "location"]
    inlines = [TaskLinkInline, FileAttachmentInline]
    actions = [
        "mark_as_done", "mark_as_canceled", 
        "soft_delete_tasks", "hard_delete_tasks"
    ]
    list_per_page = 25
    list_select_related = ["assignee"]
    save_on_top = True
    autocomplete_fields = ["tags"]
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 4, 'cols': 80})},
    }

    # Группировка полей в интерфейсе редактирования
    fieldsets = (
        (_("Основная информация"), {
            "fields": (
                "title",
                "description",
                "status",
                "progress",
                "progress_bar",
                "dependencies",
                "outgoing_dependencies",
            )
        }),
        (_("Категории и метаданные"), {
            "fields": ("priority", "categories", "location", "tags"),
            "classes": ("collapse",),
        }),
        (_("Ответственные лица"), {
            "fields": ("author", "assignee", "last_editor")
        }),
        (_("Временные параметры"), {
            "fields": (
                ("start_date", "end_date"),
                "deadline",
                ("created_at", "updated_at", "deleted_at"),
                "is_overdue",
            )
        }),
        (_("Дополнительные параметры"), {
            "fields": (
                "complexity",
                "risk_level",
                "estimated_time",
                "actual_time",
                "budget",
                "quality_rating",
                "time_intervals",
                "reminders",
            ),
            "classes": ("collapse",),
        }),
        (_("Флаги состояния"), {
            "fields": (
                "is_ready",
                "is_recurring",
                "needs_approval",
                "is_template",
                "is_deleted",
            ),
            "classes": ("collapse",),
        }),
        (_("Повторение и уведомления"), {
            "fields": ("repeat_interval", "next_activation", "notifications"),
            "classes": ("collapse",),
        }),
        (_("Системная информация"), {
            "fields": ("version", "cancel_reason", "status_history"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description=_("Название"))
    def title_short(self, obj):
        """Сокращает название задачи для отображения в списке"""
        return Truncator(obj.title).chars(40)

    @admin.display(description=_("Статус"))
    def status_badge(self, obj):
        """Отображает статус в виде цветного бейджа"""
        status_colors = {
            "waiting": "grey",
            "progress": "blue",
            "done": "green",
            "canceled": "red",
            "pending_approval": "orange",
        }
        color = status_colors.get(obj.status, "grey")
        return format_html(
            '<span style="display:inline-block; padding:2px 8px; '
            'border-radius:12px; background:{}; color:white">{}</span>',
            color, obj.get_status_display()
        )

    @admin.display(description=_("Прогресс"))
    def progress_bar(self, obj):
        """Визуализирует прогресс выполнения в виде цветной полосы"""
        color = {
            "waiting": "#9e9e9e",
            "progress": "#2196f3",
            "done": "#4caf50",
            "canceled": "#f44336",
        }.get(obj.status, "#9e9e9e")

        return format_html(
            '<div class="progress-container" style="display:inline-block; width:100px; '
            'background:#f5f5f5; height:20px; border:1px solid #ddd; margin-right:10px; '
            'vertical-align:middle">'
            '<div class="progress-bar" style="background:{}; width:{}%; height:100%;"></div>'
            '</div>'
            '<span style="vertical-align:middle">{}%</span>',
            color, obj.progress, obj.progress
        )

    @admin.display(description=_("Исполнитель"))
    def assignee_name(self, obj):
        """Отображает имя исполнителя с ссылкой на его профиль"""
        if not obj.assignee:
            return "-"
        url = reverse('admin:auth_user_change', args=[obj.assignee.id])
        return format_html('<a href="{}">{}</a>', url, obj.assignee.get_full_name() or obj.assignee.username)

    @admin.display(description=_("Просрочена"), boolean=True)
    def is_overdue_icon(self, obj):
        """Иконка просроченной задачи"""
        return obj.is_overdue

    @admin.display(description=_("Готова"), boolean=True)
    def is_ready_icon(self, obj):
        """Иконка готовности задачи"""
        return obj.is_ready

    @admin.display(description=_("Дедлайн"), ordering="deadline")
    def formatted_deadline(self, obj):
        """Форматированное отображение дедлайна"""
        if not obj.deadline:
            return "-"
        return obj.deadline.strftime("%d.%m.%Y %H:%M")

    @admin.display(description=_("Зависимости"))
    def dependencies_count(self, obj):
        """Количество зависимостей с ссылками"""
        count = obj.dependencies.count()
        if not count:
            return "-"
        
        url = (
            reverse('admin:tasks_task_changelist') 
            + f'?id__in={",".join(str(t.id) for t in obj.dependencies.all())}'
        )
        return format_html('<a href="{}">{} зависимостей</a>', url, count)

    @admin.display(description=_("История статусов"))
    def status_history(self, obj):
        """История изменений статусов задачи"""
        history = obj.history.order_by('-history_date').values_list('status', 'history_date')
        if not history:
            return "-"
            
        items = []
        for status, date in history[:5]:  # Последние 5 изменений
            items.append(f"<li>{date.strftime('%d.%m.%Y %H:%M')} - {status}</li>")
        
        return format_html("<ul>{}</ul>", mark_safe("".join(items)))

    @admin.display(description=_("Исходящие зависимости"))
    def outgoing_dependencies(self, obj):
        """Список задач, зависящих от текущей"""
        if not obj.pk:
            return "-"
            
        deps = obj.dependent_tasks.all()
        if not deps:
            return "-"
        
        items = []
        for t in deps:
            url = reverse('admin:tasks_task_change', args=[t.id])
            title = escape(Truncator(t.title).chars(30))
            items.append(f'<li><a href="{url}">{title}</a></li>')
        
        return format_html("<ul>{}</ul>", mark_safe("".join(items)))

    def get_queryset(self, request):
        """Оптимизированный запрос для админки"""
        qs = super().get_queryset(request)
        return qs.select_related(
            "author", "last_editor", "assignee", "location"
        ).prefetch_related(
            "dependencies", "categories", "notifications", "tags", "dependent_tasks"
        ).annotate(
            dependencies_count=Count('dependencies')
        ).defer(
            "description", "time_intervals", "reminders", "cancel_reason"
        )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Фильтрация зависимостей"""
        if db_field.name == "dependencies":
            # Исключаем удаленные задачи и текущую задачу
            exclude_id = request.resolver_match.kwargs.get('object_id')
            qs = Task.objects.filter(is_deleted=False)
            if exclude_id:
                qs = qs.exclude(id=exclude_id)
            kwargs["queryset"] = qs
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        """Динамически определяем поля только для чтения"""
        fields = list(super().get_readonly_fields(request, obj))
        if not obj:  # Для новых объектов
            fields = [f for f in fields if f != "outgoing_dependencies"]
        return fields

    def get_exclude(self, request, obj=None):
        """Скрываем технические поля при создании"""
        if obj is None:
            return ["is_deleted", "deleted_at", "version"]
        return super().get_exclude(request, obj)

    # Действия администратора
    @admin.action(description=_("Пометить как выполненные"))
    def mark_as_done(self, request, queryset):
        """Помечает задачи как выполненные"""
        tasks = list(queryset)
        for task in tasks:
            task.status = "done"
            task.progress = 100
            if not task.end_date:
                task.end_date = timezone.now()
        
        Task.objects.bulk_update(tasks, ['status', 'progress', 'end_date'])
        self.message_user(
            request, 
            f"Помечено как выполненные: {len(tasks)} задач", 
            messages.SUCCESS
        )

    @admin.action(description=_("Пометить как отмененные"))
    def mark_as_canceled(self, request, queryset):
        """Помечает задачи как отмененные"""
        tasks = list(queryset)
        for task in tasks:
            if not task.cancel_reason:
                task.cancel_reason = _("Отменено администратором")
            task.status = "canceled"
        
        Task.objects.bulk_update(tasks, ['status', 'cancel_reason'])
        self.message_user(
            request, 
            f"Помечено как отмененные: {len(tasks)} задач", 
            messages.SUCCESS
        )

    @admin.action(description=_("Мягкое удаление"))
    def soft_delete_tasks(self, request, queryset):
        """Мягкое удаление задач"""
        count = 0
        for task in queryset:
            task.delete()  # Использует кастомный метод delete модели
            count += 1
        self.message_user(
            request, 
            f"Мягко удалено: {count} задач", 
            messages.WARNING
        )

    @admin.action(description=_("Полное удаление"))
    def hard_delete_tasks(self, request, queryset):
        """Полное удаление из БД"""
        if not request.user.is_superuser:
            self.message_user(
                request, 
                "Только суперпользователи могут полностью удалять задачи", 
                messages.ERROR
            )
            return

        count = 0
        for task in queryset:
            task.hard_delete()
            count += 1
            
        self.message_user(
            request, 
            f"Полностью удалено: {count} задач", 
            messages.SUCCESS
        )

    def save_model(self, request, obj, form, change):
        """Обработка сохранения модели"""
        if not change:  # Новая задача
            obj.author = request.user
            if not obj.start_date and obj.status == "progress":
                obj.start_date = timezone.now()
        
        obj.last_editor = request.user
        
        # Автоматическая коррекция прогресса
        if obj.status == "done" and obj.progress < 100:
            obj.progress = 100
            if not obj.end_date:
                obj.end_date = timezone.now()
        
        super().save_model(request, obj, form, change)

    def get_actions(self, request):
        """Удаляем стандартное действие удаления"""
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions

    class Media:
        """Кастомные стили для админки"""
        css = {
            'all': (
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
                'admin/css/task_admin.css',
            )
        }
    def get_fieldsets(self, request, obj=None):
        """Динамически формируем fieldsets в зависимости от типа операции (создание/редактирование)"""
        base_fieldsets = [
            (_("Основная информация"), {
                "fields": (
                    "title",
                    "description",
                    "status",
                    "progress",
                    "progress_bar",
                    "dependencies",
                ) + (("outgoing_dependencies",) if obj else ())  # Только для существующих объектов
            }),
            (_("Категории и метаданные"), {
                "fields": ("priority", "categories", "location", "tags"),
                "classes": ("collapse",),
            }),
            (_("Ответственные лица"), {
                "fields": ("author", "assignee", "last_editor")
            }),
            (_("Временные параметры"), {
                "fields": (
                    ("start_date", "end_date"),
                    "deadline",
                    ("created_at", "updated_at", "deleted_at"),
                    "is_overdue",
                )
            }),
            (_("Дополнительные параметры"), {
                "fields": (
                    "complexity",
                    "risk_level",
                    "estimated_time",
                    "actual_time",
                    "budget",
                    "quality_rating",
                    "time_intervals",
                    "reminders",
                ),
                "classes": ("collapse",),
            }),
            (_("Флаги состояния"), {
                "fields": (
                    "is_ready",
                    "is_recurring",
                    "needs_approval",
                    "is_template",
                    "is_deleted",
                ),
                "classes": ("collapse",),
            }),
            (_("Повторение и уведомления"), {
                "fields": ("repeat_interval", "next_activation", "notifications"),
                "classes": ("collapse",),
            }),
            (_("Системная информация"), {
                "fields": ("version", "cancel_reason", "status_history"),
                "classes": ("collapse",),
            }),
        ]
        
        # Для новых объектов скрываем дополнительные системные поля
        if not obj:
            base_fieldsets = [
                (_("Основная информация"), {
                    "fields": (
                        "title",
                        "description",
                        "status",
                        "progress",
                        "dependencies",
                    )
                }),
                (_("Категории и метаданные"), {
                    "fields": ("priority", "categories", "location", "tags"),
                    "classes": ("collapse",),
                }),
                (_("Ответственные лица"), {
                    "fields": ("assignee",)  # Автор установится автоматически
                }),
                (_("Временные параметры"), {
                    "fields": (
                        ("start_date", "end_date"),
                        "deadline",
                    )
                }),
                (_("Дополнительные параметры"), {
                    "fields": (
                        "complexity",
                        "risk_level",
                        "estimated_time",
                        "budget",
                    ),
                    "classes": ("collapse",),
                }),
                (_("Флаги состояния"), {
                    "fields": (
                        "is_ready",
                        "is_recurring",
                        "needs_approval",
                        "is_template",
                    ),
                    "classes": ("collapse",),
                }),
                (_("Повторение и уведомления"), {
                    "fields": ("repeat_interval", "next_activation", "notifications"),
                    "classes": ("collapse",),
                }),
            ]
        return base_fieldsets

    def get_readonly_fields(self, request, obj=None):
        """Динамически определяем поля только для чтения"""
        readonly = list(super().get_readonly_fields(request, obj))
        
        # Для новых объектов
        if not obj:
            readonly = []
        # Для существующих объектов
        else:
            readonly += [
                "created_at", "updated_at", "deleted_at", "version",
                "outgoing_dependencies", "is_overdue", "progress_bar",
                "is_deleted", "status_history", "author", "last_editor"
            ]
        
        return readonly





@admin.register(TaskLink)
class TaskLinkAdmin(admin.ModelAdmin):
    """Административный интерфейс для связи задач и ссылок"""

    list_display = ["id", "task_title", "link_url", "created_at"]
    autocomplete_fields = ["task", "link"]
    readonly_fields = ["created_at"]
    search_fields = ["task__title", "link__url"]
    list_per_page = 30
    list_select_related = ["task", "link"]

    def task_title(self, obj):
        """Название задачи со ссылкой"""
        return format_html(
            '<a href="/admin/tasks/task/{0}/change/">{1}</a>',
            obj.task.id,
            obj.task.title[:50] + "..." if len(obj.task.title) > 50 else obj.task.title,
        )

    task_title.short_description = _("Задача")

    def link_url(self, obj):
        """URL ссылки со ссылкой"""
        return format_html(
            '<a href="{0}" target="_blank">{1}</a>',
            obj.link.url,
            obj.link.url[:60] + "..." if len(obj.link.url) > 60 else obj.link.url,
        )

    link_url.short_description = _("Ссылка")

    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).select_related("task", "link")


@admin.register(FileAttachment)
class FileAttachmentAdmin(admin.ModelAdmin):
    """Административный интерфейс для файловых вложений"""

    list_display = ["id", "task_title", "file_preview", "uploaded_at"]
    readonly_fields = ["uploaded_at", "file_preview"]
    search_fields = ["task__title"]
    list_per_page = 30
    list_select_related = ["task"]

    def task_title(self, obj):
        """Название задачи со ссылкой"""
        return format_html(
            '<a href="/admin/tasks/task/{0}/change/">{1}</a>',
            obj.task.id,
            obj.task.title[:50] + "..." if len(obj.task.title) > 50 else obj.task.title,
        )

    task_title.short_description = _("Задача")

    def file_preview(self, obj):
        """Предпросмотр файла со ссылкой на скачивание"""
        if obj.file:
            return format_html(
                '<a href="{0}" target="_blank" download>{1}</a>',
                obj.file.url,
                obj.file.name.split("/")[-1],
            )
        return "-"

    file_preview.short_description = _("Файл")

    def get_queryset(self, request):
        """Оптимизация запросов"""
        return super().get_queryset(request).select_related("task")
