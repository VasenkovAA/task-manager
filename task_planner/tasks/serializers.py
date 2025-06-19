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
    class Meta:
        model = TaskCategory
        fields = "__all__"
        read_only_fields = ["id"]


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
    progress = serializers.IntegerField(min_value=0, max_value=100)
    is_ready = serializers.BooleanField()

    category_names = serializers.SerializerMethodField(
        help_text="Названия категорий задачи"
    )

    def get_category_names(self, obj):
        """Возвращает список названий категорий"""
        return list(obj.categories.values_list('name', flat=True))

    author = UserSerializer(read_only=True)
    last_editor = UserSerializer(read_only=True)
    assignee = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), allow_null=True
    )
    location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), allow_null=True
    )

    dependencies = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Task.objects.all()
    )
    categories = serializers.PrimaryKeyRelatedField(
        many=True, queryset=TaskCategory.objects.all()
    )
    notifications = serializers.PrimaryKeyRelatedField(
        many=True, queryset=NotificationMethod.objects.all()
    )
    links = TaskLinkSerializer(many=True, read_only=True)
    attachments = FileAttachmentSerializer(many=True, read_only=True)

    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES)
    risk_level = serializers.ChoiceField(choices=Task.RISK_LEVEL_CHOICES)

    completed_dependencies_percentage = serializers.IntegerField(
        read_only=True,
        help_text="Процент выполненных зависимых задач (только для чтения)",
    )
    tags = serializers.SerializerMethodField(help_text="Список тегов задачи")

    def get_tags(self, obj):
        """Возвращает список названий тегов вместо менеджера тегов"""
        return list(obj.tags.names())

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "priority",
            "status",
            "progress",
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
            "notifications",
            "links",
            "attachments",
            "completed_dependencies_percentage",
            "category_names",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "deleted_at",
            "version",
            "is_deleted",
            "author",
            "last_editor",
            "attachments",
            "history",
            "completed_dependencies_percentage",
            "tags",
        ]

    def create(self, validated_data):
        dependencies = validated_data.pop("dependencies", [])
        categories = validated_data.pop("categories", [])
        notifications = validated_data.pop("notifications", [])

        task = Task.objects.create(**validated_data)
        task.dependencies.set(dependencies)
        task.categories.set(categories)
        task.notifications.set(notifications)
        return task

    def update(self, instance, validated_data):
        dependencies = validated_data.pop("dependencies", None)
        categories = validated_data.pop("categories", None)
        notifications = validated_data.pop("notifications", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if dependencies is not None:
            instance.dependencies.set(dependencies)
        if categories is not None:
            instance.categories.set(categories)
        if notifications is not None:
            instance.notifications.set(notifications)

        instance.save()
        return instance


class TaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ["id", "title", "status", "progress", "deadline"]
