from django.contrib import admin
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


@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = [field.name for field in TaskCategory._meta.fields]
    search_fields = ["name"]


@admin.register(NotificationMethod)
class NotificationMethodAdmin(admin.ModelAdmin):
    list_display = [field.name for field in NotificationMethod._meta.fields]
    search_fields = ["name"]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Location._meta.fields]
    search_fields = ["name", "address"]


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = [field.name for field in Link._meta.fields]
    readonly_fields = ["created_at"]
    date_hierarchy = "created_at"
    search_fields = ["url"]  # Добавлено для автозаполнения


class TaskLinkInline(admin.TabularInline):
    model = TaskLink
    extra = 1
    autocomplete_fields = ["link"]  # Используем автозаполнение


class FileAttachmentInline(admin.TabularInline):
    model = FileAttachment
    extra = 1


@admin.register(Task)
class TaskAdmin(SimpleHistoryAdmin):  # Используем SimpleHistoryAdmin
    list_display = [
        field.name
        for field in Task._meta.fields
        if field.name not in ["description", "history"]
    ]
    list_display += ["get_outgoing_dependencies"]

    def get_outgoing_dependencies(self, obj):
        """Возвращает список задач, зависящих от текущей."""
        return ", ".join([task.title for task in obj.task_dependencies.all()])

    get_outgoing_dependencies.short_description = "Исходящие зависимости"

    def get_queryset(self, request):
        """Оптимизация запросов к БД."""
        return super().get_queryset(request).prefetch_related("task_dependencies")

    list_filter = ["status", "priority", "risk_level"]
    search_fields = ["title", "description"]
    readonly_fields = [
        "created_at",
        "updated_at",
        "deleted_at",
        "version",
        "get_outgoing_dependencies",
    ]
    date_hierarchy = "deadline"
    filter_horizontal = ["dependencies", "categories", "notifications"]
    raw_id_fields = ["author", "last_editor", "assignee"]
    inlines = [TaskLinkInline, FileAttachmentInline]

    fieldsets = (
        (
            "Основное",
            {
                "fields": (
                    "title",
                    "description",
                    "priority",
                    "status",
                    "progress",
                )
            },
        ),
        (
            "Временные параметры",
            {
                "fields": (
                    ("start_date", "end_date"),
                    "deadline",
                    ("created_at", "updated_at", "deleted_at"),
                )
            },
        ),
        (
            "Связи",
            {
                "fields": (
                    "dependencies",
                    "get_outgoing_dependencies",
                    "categories",
                    "location",
                )
            },
        ),
        ("Ответственные", {"fields": ("author", "assignee")}),
        (
            "Дополнительные параметры",
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
                )
            },
        ),
        (
            "Флаги",
            {
                "fields": (
                    "is_ready",
                    "is_recurring",
                    "needs_approval",
                    "is_template",
                )
            },
        ),
        ("Повторение", {"fields": ("repeat_interval", "next_activation")}),
        ("Системное", {"fields": ("tags",)}),
    )


@admin.register(TaskLink)
class TaskLinkAdmin(admin.ModelAdmin):
    list_display = [field.name for field in TaskLink._meta.fields]
    autocomplete_fields = ["task", "link"]  # Исправлено
    readonly_fields = ["created_at"]
    search_fields = ["task__title", "link__url"]  # Добавлено для автозаполнения


@admin.register(FileAttachment)
class FileAttachmentAdmin(admin.ModelAdmin):
    list_display = [field.name for field in FileAttachment._meta.fields]
    readonly_fields = ["uploaded_at"]
    search_fields = ["task__title"]
