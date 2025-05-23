# admin.py
from django.contrib import admin
from django.utils.html import format_html
from tasks.models import (
    TaskCategory,
    NotificationMethod,
    Location,
    Link,
    Task,
    TaskLink,
    FileAttachment
)

class TaskCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'task_count')
    search_fields = ('name',)
    
    def task_count(self, obj):
        return obj.task_set.count()
    task_count.short_description = 'Количество задач'

class NotificationMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'config_preview')
    search_fields = ('name',)
    
    def config_preview(self, obj):
        return format_html('<code>{}</code>', str(obj.config)[:50])
    config_preview.short_description = 'Конфигурация'

class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'coordinates', 'address_short')
    list_filter = ('name',)
    search_fields = ('name', 'address')
    
    def address_short(self, obj):
        return obj.address[:50] + '...' if obj.address else ''
    address_short.short_description = 'Адрес'

class LinkAdmin(admin.ModelAdmin):
    list_display = ('url', 'created_at')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'

class TaskLinkInline(admin.TabularInline):
    model = TaskLink
    extra = 1
    raw_id_fields = ('task', 'link')

class FileAttachmentInline(admin.StackedInline):
    model = FileAttachment
    extra = 1
    readonly_fields = ('uploaded_at',)

class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title', 
        'status_badge', 
        'priority', 
        'author', 
        'assignee', 
        'deadline'
    )
    list_filter = ('status', 'risk_level', 'is_deleted')
    search_fields = ('title', 'description')
    filter_horizontal = ('dependencies', 'categories', 'notifications')
    inlines = [TaskLinkInline, FileAttachmentInline]
    date_hierarchy = 'deadline'
    readonly_fields = (
        'created_at', 
        'updated_at', 
        'deleted_at', 
        'version', 
        'history'
    )
    fieldsets = (
        ('Основное', {
            'fields': (
                'title', 
                'description', 
                ('priority', 'complexity'), 
                'status'
            )
        }),
        ('Временные параметры', {
            'fields': (
                ('start_date', 'end_date'), 
                'deadline', 
                'repeat_interval'
            )
        }),
        ('Ответственные', {
            'fields': ('author', 'last_editor', 'assignee')
        }),
        ('Дополнительно', {
            'fields': (
                # Убрали is_deleted из fields
                'version', 
                'created_at', 
                'updated_at', 
                'deleted_at'
            )
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'waiting': 'gray',
            'progress': 'blue',
            'done': 'green',
            'canceled': 'red'
        }
        return format_html(
            '<span style="color: white; background: {}; padding: 2px 5px; border-radius: 3px">{}</span>',
            colors[obj.status],
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'
    
    actions = ['mark_as_done', 'soft_delete']
    
    @admin.action(description='Пометить как выполненное')
    def mark_as_done(self, request, queryset):
        queryset.update(status='done', progress=100)
    
    @admin.action(description='Мягкое удаление')
    def soft_delete(self, request, queryset):
        queryset.update(is_deleted=True)

admin.site.register(TaskCategory, TaskCategoryAdmin)
admin.site.register(NotificationMethod, NotificationMethodAdmin)
admin.site.register(Location, LocationAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(TaskLink)
admin.site.register(FileAttachment)