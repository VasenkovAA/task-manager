from time import timezone
from warnings import filters
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db.models import Count, Case, When, Q, F, ExpressionWrapper, IntegerField
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

import json
from django.db.models import Prefetch

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters

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
    queryset = Task.objects.filter(is_deleted=False)  # Базовый queryset
    
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
    

    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Получение списка категорий с количеством задач"""
        queryset = TaskCategory.objects.annotate(
            task_count=Count('tasks', filter=Q(tasks__is_deleted=False)))
        serializer = TaskCategorySerializer(queryset, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        """
        Возвращает оптимизированный запрос для задач с:
        - Аннотацией зависимостей
        - Фильтрацией по категориям
        - Оптимизацией связанных данных
        """

        queryset = super().get_queryset()
        

        params = self.request.query_params
        category_ids = params.get('categories')
        include_no_category = params.get('include_no_category') == 'true'
        tag_list = params.get('tags')
        
        if category_ids:
            category_ids = [int(id) for id in category_ids.split(',') if id.isdigit()]
            if category_ids:
                queryset = queryset.filter(categories__id__in=category_ids).distinct()
        
        if include_no_category:
            no_category_qs = Task.objects.filter(is_deleted=False, categories__isnull=True)
            queryset = queryset | no_category_qs if category_ids else no_category_qs
        
        if tag_list:
            tags = [tag.strip() for tag in tag_list.split(',') if tag.strip()]
            if tags:
                queryset = queryset.filter(tags__name__in=tags).distinct()
        
        queryset = queryset.select_related(
            'author', 'last_editor', 'assignee', 'location'
        ).prefetch_related(
            Prefetch('dependencies', queryset=Task.objects.only('id', 'title', 'status')),
            Prefetch('categories', queryset=TaskCategory.objects.only('id', 'name')),
            'notifications',
            'tags',
            Prefetch('links', queryset=Link.objects.only('id', 'url')),
            Prefetch('attachments', queryset=FileAttachment.objects.only('id', 'file'))
        )
        
        return queryset.annotate(
            total_dependencies=Count('dependencies', distinct=True),
            completed_dependencies=Count(
                'dependencies',
                distinct=True,
                filter=Q(dependencies__status__in=['done', 'canceled'])
            ),
            dep_progress=Case(
                When(total_dependencies=0, then=100),
                default=ExpressionWrapper(
                    F('completed_dependencies') * 100 / F('total_dependencies'),
                    output_field=IntegerField()
                ),
                output_field=IntegerField()
            )
        ).distinct()

    def perform_create(self, serializer):
        """Автоматическое заполнение автора при создании задачи"""
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        """Автоматическое обновление редактора при изменении задачи"""
        serializer.save(last_editor=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Мягкое удаление задачи"""
        task = self.get_object()
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        """Восстановление мягко удаленной задачи"""
        task = self.get_object()
        
        if not task.is_deleted:
            return Response(
                {"error": "Задача не была удалена"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        task.restore()
        return Response(
            {"status": "task restored"}, 
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def add_dependency(self, request, pk=None):
        """Добавление зависимости к задаче"""
        task = self.get_object()
        dependency_id = request.data.get("dependency_id")
        
        if not dependency_id:
            return Response(
                {"error": "Требуется параметр dependency_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            dependency = Task.objects.get(pk=dependency_id, is_deleted=False)
        except Task.DoesNotExist:
            return Response(
                {"error": "Зависимость не найдена или удалена"},
                status=status.HTTP_404_NOT_FOUND
            )
        

        if dependency.id == task.id:
            return Response(
                {"error": "Задача не может зависеть от самой себя"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if check_cyclic_dependency(task, dependency):
            return Response(
                {"error": "Обнаружена циклическая зависимость"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.dependencies.add(dependency)
        return Response(
            {"status": "dependency added"}, 
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["post"])
    def remove_dependency(self, request, pk=None):
        """Удаление зависимости у задачи"""
        task = self.get_object()
        dependency_id = request.data.get("dependency_id")
        
        if not dependency_id:
            return Response(
                {"error": "Требуется параметр dependency_id"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            dependency = Task.objects.get(pk=dependency_id)
            task.dependencies.remove(dependency)
            return Response({"status": "dependency removed"})
        except Task.DoesNotExist:
            return Response(
                {"error": "Зависимость не найдена"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=["get"])
    def overdue(self, request):
        """Получение списка просроченных задач"""
        queryset = self.get_queryset().filter(
            deadline__lt=timezone.now(), 
            status__in=["waiting", "progress"]
        ).order_by('deadline')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):
        """Изменение статуса задачи с валидацией"""
        task = self.get_object()
        new_status = request.data.get("status")
        
        if not new_status:
            return Response(
                {"error": "Требуется параметр status"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        valid_transitions = {
            "waiting": ["progress", "canceled"],
            "progress": ["done", "canceled"],
            "done": ["progress"],
            "canceled": ["waiting", "progress"],
        }

        if new_status not in valid_transitions.get(task.status, []):
            return Response(
                {"error": f"Недопустимый переход из {task.status} в {new_status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_status == "done":
            if task.progress < 100:
                return Response(
                    {"error": "Прогресс должен быть 100% для завершения задачи"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            if task.needs_approval:
                task.status = "pending_approval"
                task.save()
                return Response(
                    {"status": "pending_approval", "message": "Требуется подтверждение руководителя"},
                    status=status.HTTP_200_OK
                )
        
        if new_status == "canceled":
            cancel_reason = request.data.get("cancel_reason", "")
            if not cancel_reason and not task.cancel_reason:
                return Response(
                    {"error": "Требуется указать причину отмены"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            task.cancel_reason = cancel_reason or task.cancel_reason

        # Обновление задачи
        task.status = new_status
        task.last_editor = request.user
        
        if new_status == "done":
            task.progress = 100
            task.end_date = timezone.now()
        elif new_status == "progress" and not task.start_date:
            task.start_date = timezone.now()
        
        task.save()
        return Response(self.get_serializer(task).data)

    # Новые экшены
    @action(detail=True, methods=["post"])
    def add_tags(self, request, pk=None):
        """Добавление тегов к задаче"""
        task = self.get_object()
        tags = request.data.get("tags", [])
        
        if not tags or not isinstance(tags, list):
            return Response(
                {"error": "Требуется список тегов"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.tags.add(*tags)
        return Response({"status": f"Добавлено {len(tags)} тегов"})

    @action(detail=True, methods=["post"])
    def remove_tag(self, request, pk=None):
        """Удаление тега из задачи"""
        task = self.get_object()
        tag = request.data.get("tag")
        
        if not tag:
            return Response(
                {"error": "Требуется параметр tag"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.tags.remove(tag)
        return Response({"status": "Тег удален"})

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        """Получение истории изменений задачи"""
        task = self.get_object()
        history = task.history.all().order_by('-history_date')
        
        page = self.paginate_queryset(history)
        if page is not None:
            serializer = HistoricalTaskSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = HistoricalTaskSerializer(history, many=True)
        return Response(serializer.data)

def check_cyclic_dependency(task, dependency):
    """Рекурсивная проверка циклических зависимостей"""
    visited = set()
    stack = [dependency]
    
    while stack:
        current = stack.pop()
        if current.id == task.id:
            return True
        if current.id not in visited:
            visited.add(current.id)
            stack.extend(current.dependencies.all())
    return False
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
