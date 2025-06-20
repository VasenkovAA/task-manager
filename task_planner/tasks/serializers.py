from rest_framework import serializers

from tasks.models import (
    TaskCategory,
    NotificationMethod,
    Location,
    Link,
    Task,
    TaskLink,
    FileAttachment,
)
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class TaskCategorySerializer(serializers.ModelSerializer):
    task_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = TaskCategory
        fields = ["id", "name", "description", "task_count"]
        read_only_fields = ["id", "task_count"]


class NotificationMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationMethod
        fields = "__all__"
        read_only_fields = ["id"]


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = "__all__"
        read_only_fields = ["id"]


class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class TaskLinkSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all())
    link = serializers.PrimaryKeyRelatedField(queryset=Link.objects.all())

    class Meta:
        model = TaskLink
        fields = "__all__"
        read_only_fields = ["created_at"]


class FileAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileAttachment
        fields = "__all__"
        read_only_fields = ["uploaded_at", "task"]


class TaskSerializer(serializers.ModelSerializer):
    # Убрана явная валидация progress - она уже есть в модели
    # is_ready сделано read_only (вычисляется автоматически)
    category_names = serializers.SerializerMethodField(
        help_text="Названия категорий задачи"
    )

    def get_category_names(self, obj):
        """Возвращает список названий категорий"""
        return list(obj.categories.values_list('name', flat=True))

    author = UserSerializer(read_only=True)
    last_editor = UserSerializer(read_only=True)
    
    assignee = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        allow_null=True,
        required=False,
        help_text="ID исполнителя задачи"
    )
    
    location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        allow_null=True,
        required=False,
        help_text="ID местоположения"
    )

    dependencies = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Task.objects.only('id'),
        required=False
    )
    
    categories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=TaskCategory.objects.only('id'),
        required=False
    )
    
    notifications = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=NotificationMethod.objects.only('id'),
        required=False
    )
    
    links = TaskLinkSerializer(many=True, read_only=True)
    attachments = FileAttachmentSerializer(many=True, read_only=True)

    status = serializers.ChoiceField(
        choices=Task.STATUS_CHOICES,
        required=False
    )
    risk_level = serializers.ChoiceField(
        choices=Task.RISK_LEVEL_CHOICES,
        required=False
    )

    progress_dependencies = serializers.IntegerField(
        read_only=True,
        min_value=0,
        max_value=100,
        help_text="Прогресс выполнения зависимостей в %"
    )
    
    tags = serializers.SerializerMethodField(help_text="Список тегов задачи")

    def get_tags(self, obj):
        return list(obj.tags.names())

    tag_list = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False,
        help_text="Список тегов для добавления (только запись)"
    )

    is_overdue = serializers.BooleanField(
        read_only=True,
        help_text="Просрочена ли задача"
    )
    
    outgoing_dependencies = serializers.PrimaryKeyRelatedField(
        many=True,
        read_only=True,
        help_text="ID задач, зависящих от этой"
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "priority",
            "status",
            "progress",
            "progress_dependencies",
            "created_at",
            "updated_at",
            "start_date",
            "end_date",
            "deadline",
            "dependencies",
            "categories",
            "location",
            "author",
            "last_editor",
            "assignee",
            "complexity",
            "risk_level",
            "is_ready",
            "is_recurring",
            "needs_approval",
            "is_template",
            "estimated_time",
            "actual_time",
            "quality_rating",
            "version",
            "budget",
            "cancel_reason",
            "time_intervals",
            "reminders",
            "repeat_interval",
            "next_activation",
            "tags",
            "tag_list",
            "notifications",
            "links",
            "attachments",
            "category_names",
            "is_overdue",
            "outgoing_dependencies",
            "is_deleted",
            "deleted_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "deleted_at",
            "version",
            "author",
            "last_editor",
            "attachments",
            "history",
            "progress_dependencies",
            "tags",
            "is_ready",
            "is_overdue",
            "outgoing_dependencies",
            "is_deleted",
        ]

    def create(self, validated_data):
        """Создание задачи с обработкой связей и тегов"""
        dependencies = validated_data.pop("dependencies", [])
        categories = validated_data.pop("categories", [])
        notifications = validated_data.pop("notifications", [])
        tag_list = validated_data.pop("tag_list", [])

        user = self.context['request'].user
        
        task = Task.objects.create(
            **validated_data,
            author=user,
            last_editor=user
        )
        
        task.dependencies.set(dependencies)
        task.categories.set(categories)
        task.notifications.set(notifications)
        
        if tag_list:
            task.tags.set(tag_list)
            
        return task

    def update(self, instance, validated_data):
        """Обновление задачи с обработкой связей и тегов"""
        dependencies = validated_data.pop("dependencies", None)
        categories = validated_data.pop("categories", None)
        notifications = validated_data.pop("notifications", None)
        tag_list = validated_data.pop("tag_list", None)

        user = self.context['request'].user
        validated_data['last_editor'] = user
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if dependencies is not None:
            instance.dependencies.set(dependencies)
        if categories is not None:
            instance.categories.set(categories)
        if notifications is not None:
            instance.notifications.set(notifications)
        if tag_list is not None:
            instance.tags.set(tag_list)

        instance.save()
        return instance


class TaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["id", "title", "status", "progress", "deadline"]
