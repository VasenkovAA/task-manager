# views.py
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
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

from django.db.models import Count, Case, When, Q, F, ExpressionWrapper, IntegerField
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json


class TaskCategoryViewSet(viewsets.ModelViewSet):
    queryset = TaskCategory.objects.all()
    serializer_class = TaskCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class NotificationMethodViewSet(viewsets.ModelViewSet):
    queryset = NotificationMethod.objects.all()
    serializer_class = NotificationMethodSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class LinkViewSet(viewsets.ModelViewSet):
    queryset = Link.objects.all()
    serializer_class = LinkSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class TaskLinkViewSet(viewsets.ModelViewSet):
    queryset = TaskLink.objects.all()
    serializer_class = TaskLinkSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class FileAttachmentViewSet(viewsets.ModelViewSet):
    queryset = FileAttachment.objects.all()
    serializer_class = FileAttachmentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.filter(is_deleted=False)
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # Аннотируем количество зависимостей и выполненных зависимостей
        queryset = (
            super()
            .get_queryset()
            .annotate(
                total_dependencies=Count("dependencies", distinct=True),
                completed_dependencies=Count(
                    "dependencies", distinct=True, filter=Q(dependencies__status="done")
                ),
            )
        )

        # Безопасное вычисление процента с проверкой на ноль
        return queryset.annotate(
            completed_dependencies_percentage=Case(
                When(total_dependencies=0, then=100),  # Если нет зависимостей - 100%
                default=ExpressionWrapper(
                    F("completed_dependencies") * 100 / F("total_dependencies"),
                    output_field=IntegerField(),
                ),
                output_field=IntegerField(),
            )
        )

    @action(detail=True, methods=["post"])
    def add_dependency(self, request, pk=None):
        task = self.get_object()
        dependency = Task.objects.get(pk=request.data["dependency_id"])
        task.dependencies.add(dependency)
        return Response({"status": "dependency added"})

    @action(detail=True, methods=["post"])
    def remove_dependency(self, request, pk=None):
        task = self.get_object()
        dependency = Task.objects.get(pk=request.data["dependency_id"])
        task.dependencies.remove(dependency)
        return Response({"status": "dependency removed"})


def task_form(request, pk=None):
    context = {}
    if pk:
        context["task"] = get_object_or_404(Task, pk=pk)
    return render(request, "task_form.html", context)


def task_graph(request):
    return render(request, "graph.html")


@login_required
def update_graph_settings(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            request.user.profile.graph_settings = data
            request.user.profile.save()
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)
