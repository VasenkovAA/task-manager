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


@admin.register(Task)
class TaskAdmin(SimpleHistoryAdmin):
    """Административный интерфейс для задач с расширенными функциями"""

    list_display = [
        "id",
        "title_short",
        "status",
        "progress_bar",
        "priority",
        "deadline",
        "assignee_name",
        "is_overdue",
        "is_ready",
    ]
    list_display_links = ["id", "title_short"]

    def title_short(self, obj):
        """Сокращенное название для отображения в списке"""
        return obj.title[:40] + "..." if len(obj.title) > 40 else obj.title

    title_short.short_description = _("Название")

    def progress_bar(self, obj):
        """Отображение прогресса в виде полосы"""
        color = {
            "waiting": "gray",
            "progress": "blue",
            "done": "green",
            "canceled": "red",
        }.get(obj.status, "gray")
        return format_html(
            '<div style="background:lightgray; width:100px; height:20px; border:1px solid #ccc;">'
            '<div style="background:{1}; width:{0}%; height:100%;"></div>'
            "</div> <span>{0}%</span>",
            obj.progress,
            color,
        )

    progress_bar.short_description = _("Прогресс")
    progress_bar.allow_tags = True

    def assignee_name(self, obj):
        """Имя исполнителя с ссылкой на профиль"""
        if obj.assignee:
            return format_html(
                '<a href="/admin/auth/user/{0}/change/">{1}</a>',
                obj.assignee.id,
                obj.assignee.username,
            )
        return "-"

    assignee_name.short_description = _("Исполнитель")

    def is_overdue(self, obj):
        """Пометка просроченных задач"""
        return obj.is_overdue

    is_overdue.short_description = _("Просрочена")
    is_overdue.boolean = True

    def get_queryset(self, request):
        """Оптимизация запросов с предварительной загрузкой данных"""
        return (
            super()
            .get_queryset(request)
            .select_related("author", "last_editor", "assignee", "location")
            .prefetch_related("dependencies", "categories", "notifications", "tags")
            .defer("description", "time_intervals", "reminders")
        )

    list_filter = [
        "status",
        "priority",
        "risk_level",
        "is_deleted",
        "is_ready",
        "is_recurring",
        DependencyFilter,
    ]
    search_fields = ["title", "description", "assignee__username"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "deleted_at",
        "version",
        "outgoing_dependencies",
        "is_overdue",
        "progress_bar",
        "is_deleted",
    ]
    date_hierarchy = "deadline"
    filter_horizontal = ["dependencies", "categories", "notifications"]
    raw_id_fields = ["author", "last_editor", "assignee"]
    inlines = [TaskLinkInline, FileAttachmentInline]
    actions = ["mark_as_done", "mark_as_canceled", "soft_delete_tasks"]
    list_per_page = 25
    save_on_top = True

    def outgoing_dependencies(self, obj):
        """Отображение исходящих зависимостей"""
        deps = obj.dependent_tasks.all()
        if not deps:
            return "-"
        return format_html(
            "<ul>{}</ul>",
            "".join(
                [
                    f'<li><a href="/admin/tasks/task/{t.id}/change/">{t.title}</a></li>'
                    for t in deps
                ]
            ),
        )

    outgoing_dependencies.short_description = _("Исходящие зависимости")

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Фильтрация зависимостей для исключения удаленных задач"""
        if db_field.name == "dependencies":
            kwargs["queryset"] = Task.objects.filter(is_deleted=False)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def mark_as_done(self, request, queryset):
        """Действие: пометить задачи как выполненные"""
        updated = queryset.update(status="done", progress=100)
        self.message_user(request, f"{updated} задач помечены как выполненные")

    mark_as_done.short_description = _("Пометить выбранные задачи как выполненные")

    def mark_as_canceled(self, request, queryset):
        """Действие: пометить задачи как отмененные"""
        for task in queryset:
            if not task.cancel_reason:
                task.cancel_reason = _("Отменено администратором")
            task.status = "canceled"
            task.save()
        self.message_user(request, f"{queryset.count()} задач помечены как отмененные")

    mark_as_canceled.short_description = _("Пометить выбранные задачи как отмененные")

    def soft_delete_tasks(self, request, queryset):
        """Действие: мягкое удаление задач"""
        for task in queryset:
            task.delete()  # Используем кастомный метод delete модели
        self.message_user(request, f"{queryset.count()} задач помечены как удаленные")

    soft_delete_tasks.short_description = _("Мягкое удаление выбранных задач")

    def get_actions(self, request):
        """Скрытие стандартного действия удаления"""
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions

    def get_exclude(self, request, obj=None):
        """Скрытие технических полей при создании"""
        if obj is None:  # При создании новой задачи
            return ["is_deleted", "deleted_at", "history"]
        return super().get_exclude(request, obj)

    fieldsets = (
        (
            _("Основное"),
            {
                "fields": (
                    "title",
                    "description",
                    "priority",
                    "status",
                    "progress",
                    "progress_bar",  # Добавлен визуальный индикатор
                )
            },
        ),
        (
            _("Временные параметры"),
            {
                "fields": (
                    ("start_date", "end_date"),
                    "deadline",
                    ("created_at", "updated_at", "deleted_at"),
                    "is_overdue",  # Добавлен флаг просроченности
                )
            },
        ),
        (
            _("Связи"),
            {
                "fields": (
                    "dependencies",
                    "outgoing_dependencies",  # Улучшенное отображение
                    "categories",
                    "location",
                )
            },
        ),
        (
            _("Ответственные"),
            {
                "fields": (
                    "author",
                    "assignee",
                    "last_editor",
                )
            },
        ),
        (
            _("Дополнительные параметры"),
            {
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
                "classes": ("collapse",),  # Сворачиваемый раздел
            },
        ),
        (
            _("Флаги состояния"),
            {
                "fields": (
                    "is_ready",
                    "is_recurring",
                    "needs_approval",
                    "is_template",
                    "is_deleted",  # Добавлен флаг удаления
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Повторение"),
            {
                "fields": (
                    "repeat_interval",
                    "next_activation",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Системное"),
            {
                "fields": (
                    "tags",
                    "version",
                    "notifications",
                ),
                "classes": ("collapse",),
            },
        ),
    )


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
