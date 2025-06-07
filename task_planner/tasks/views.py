from time import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, NotFound
from django.db.models import Count, Case, When, Q, F, ExpressionWrapper, IntegerField
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
import json

from tasks.models import (
    TaskCategory,
    NotificationMethod,
    Location,
    Link,
    Task,
    TaskLink,
    FileAttachment,
)
from tasks.serializers import (
    TaskCategorySerializer,
    NotificationMethodSerializer,
    LocationSerializer,
    LinkSerializer,
    TaskSerializer,
    TaskLinkSerializer,
    FileAttachmentSerializer,
)
from django.shortcuts import render

class BaseViewSet(viewsets.ModelViewSet):
    """Базовый класс для ViewSet с общей конфигурацией"""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """Оптимизация запросов по умолчанию"""
        return super().get_queryset().select_related().prefetch_related()


class TaskCategoryViewSet(BaseViewSet):
    """ViewSet для управления категориями задач"""

    queryset = TaskCategory.objects.all()
    serializer_class = TaskCategorySerializer
    search_fields = ["name"]
    ordering_fields = ["name"]

    def get_queryset(self):
        """Оптимизация запросов для категорий"""
        return super().get_queryset().only("id", "name", "description")


class NotificationMethodViewSet(BaseViewSet):
    """ViewSet для управления методами уведомлений"""

    queryset = NotificationMethod.objects.all()
    serializer_class = NotificationMethodSerializer
    search_fields = ["name"]
    ordering_fields = ["name"]


class LocationViewSet(BaseViewSet):
    """ViewSet для управления местоположениями"""

    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    search_fields = ["name", "address"]
    ordering_fields = ["name"]


class LinkViewSet(BaseViewSet):
    """ViewSet для управления ссылками"""

    queryset = Link.objects.all()
    serializer_class = LinkSerializer
    search_fields = ["url"]
    ordering_fields = ["created_at"]


class TaskLinkViewSet(BaseViewSet):
    """ViewSet для управления связями задач и ссылок"""

    queryset = TaskLink.objects.all()
    serializer_class = TaskLinkSerializer

    def get_queryset(self):
        """Оптимизация запросов с подгрузкой связанных объектов"""
        return super().get_queryset().select_related("task", "link")


class FileAttachmentViewSet(BaseViewSet):
    """ViewSet для управления файловыми вложениями"""

    queryset = FileAttachment.objects.all()
    serializer_class = FileAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """Автоматическое связывание файла с текущим пользователем"""
        serializer.save(uploaded_by=self.request.user)


class TaskViewSet(BaseViewSet):
    """ViewSet для управления задачами с расширенной функциональностью"""
    serializer_class = TaskSerializer
    # Добавляем явное определение queryset
    queryset = Task.objects.filter(is_deleted=False)
    
    # Остальной код без изменений...
    search_fields = ['title', 'description', 'assignee__username']
    ordering_fields = [
        'created_at', 'updated_at', 'deadline', 
        'priority', 'progress', 'complexity'
    ]
    filterset_fields = [
        'status', 'priority', 'risk_level', 
        'is_ready', 'is_recurring', 'is_template',
        'assignee', 'author'
    ]

    def get_queryset(self):
        """
        Возвращает запрос для задач с аннотацией зависимостей.
        Исключает удаленные задачи и оптимизирует запросы.
        """
        # Используем базовый queryset вместо super().get_queryset()
        queryset = self.queryset
        
        # Оптимизация связанных данных
        queryset = queryset.select_related(
            'author', 'last_editor', 'assignee', 'location'
        ).prefetch_related(
            'dependencies', 'categories', 'notifications', 
            'tags', 'links', 'attachments'
        )
        
        # Аннотация зависимостей
        return queryset.annotate(
            total_dependencies=Count("dependencies", distinct=True),
            completed_dependencies=Count(
                "dependencies", 
                distinct=True, 
                filter=Q(dependencies__status="done")
            ),
            completed_dependencies_percentage=Case(
                When(total_dependencies=0, then=100),
                default=ExpressionWrapper(
                    F("completed_dependencies") * 100 / F("total_dependencies"),
                    output_field=IntegerField(),
                ),
                output_field=IntegerField(),
            )
        )

        # Аннотация зависимостей
        return queryset.annotate(
            total_dependencies=Count("dependencies", distinct=True),
            completed_dependencies=Count(
                "dependencies", distinct=True, filter=Q(dependencies__status="done")
            ),
            completed_dependencies_percentage=Case(
                When(total_dependencies=0, then=100),
                default=ExpressionWrapper(
                    F("completed_dependencies") * 100 / F("total_dependencies"),
                    output_field=IntegerField(),
                ),
                output_field=IntegerField(),
            ),
        )

    def perform_create(self, serializer):
        """Автоматическое заполнение автора при создании задачи"""
        serializer.save(author=self.request.user, last_editor=self.request.user)

    def perform_update(self, serializer):
        """Автоматическое обновление редактора при изменении задачи"""
        serializer.save(last_editor=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Мягкое удаление вместо физического"""
        task = self.get_object()
        task.delete()  # Используем кастомный метод delete модели
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        """Восстановление мягко удаленной задачи"""
        task = self.get_object()
        if not task.is_deleted:
            raise ValidationError("Задача не была удалена")
        task.is_deleted = False
        task.deleted_at = None
        task.save()
        return Response({"status": "task restored"})

    @action(detail=True, methods=["post"])
    def add_dependency(self, request, pk=None):
        """Добавление зависимости к задаче"""
        task = self.get_object()
        try:
            dependency_id = request.data["dependency_id"]
            dependency = Task.objects.get(pk=dependency_id, is_deleted=False)

            # Проверка циклических зависимостей
            if dependency.id == task.id:
                raise ValidationError("Задача не может зависеть от самой себя")
            if task in dependency.dependencies.all():
                raise ValidationError("Обнаружена циклическая зависимость")

            task.dependencies.add(dependency)
            return Response({"status": "dependency added"})

        except ObjectDoesNotExist:
            raise NotFound("Зависимость не найдена")
        except KeyError:
            raise ValidationError("Требуется параметр dependency_id")

    @action(detail=True, methods=["post"])
    def remove_dependency(self, request, pk=None):
        """Удаление зависимости у задачи"""
        task = self.get_object()
        try:
            dependency_id = request.data["dependency_id"]
            dependency = Task.objects.get(pk=dependency_id)
            task.dependencies.remove(dependency)
            return Response({"status": "dependency removed"})
        except ObjectDoesNotExist:
            raise NotFound("Зависимость не найдена")
        except KeyError:
            raise ValidationError("Требуется параметр dependency_id")

    @action(detail=False, methods=["get"])
    def overdue(self, request):
        """Получение списка просроченных задач"""
        queryset = self.get_queryset().filter(
            deadline__lt=timezone.now(), status__in=["waiting", "progress"]
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):
        """Изменение статуса задачи с валидацией"""
        task = self.get_object()
        new_status = request.data.get("status")

        if not new_status:
            raise ValidationError("Требуется параметр status")

        # Валидация перехода статусов
        valid_transitions = {
            "waiting": ["progress", "canceled"],
            "progress": ["done", "canceled"],
            "done": [],
            "canceled": ["waiting", "progress"],
        }

        if new_status not in valid_transitions[task.status]:
            raise ValidationError(
                f"Недопустимый переход из {task.status} в {new_status}"
            )

        # Особые проверки для статусов
        if new_status == "done" and task.progress < 100:
            raise ValidationError("Прогресс должен быть 100% для завершения задачи")

        if new_status == "canceled" and not request.data.get("cancel_reason"):
            if not task.cancel_reason:
                raise ValidationError("Требуется указать причину отмены")

        # Обновление задачи
        task.status = new_status
        task.last_editor = request.user

        if new_status == "done":
            task.progress = 100
        elif new_status == "canceled":
            task.cancel_reason = request.data.get("cancel_reason", task.cancel_reason)

        task.save()
        return Response(self.get_serializer(task).data)


@login_required
def update_graph_settings(request):
    """
    Обновление настроек графика для текущего пользователя.
    Требует аутентификации и POST-запроса с JSON-данными.
    """
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Требуется POST-запрос"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        data = json.loads(request.body)

        # Базовая валидация структуры
        if not isinstance(data, dict):
            raise ValidationError("Данные должны быть объектом JSON")

        # Обновление профиля
        profile = request.user.profile
        profile.graph_settings = data
        profile.save()

        return JsonResponse({"status": "success"})

    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Некорректный JSON"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST
        )


# Функции для фронтенда (если используются)
def task_form(request, pk=None):
    """Рендеринг формы задачи для фронтенда"""
    context = {}
    if pk:
        context["task"] = get_object_or_404(Task, pk=pk, is_deleted=False)
    return render(request, "task_form.html", context)


def task_graph(request):
    """Рендеринг страницы с графом задач"""
    return render(request, "graph.html")
