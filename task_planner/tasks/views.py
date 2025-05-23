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
    FileAttachment
)
from tasks.serializers import (
    TaskCategorySerializer,
    NotificationMethodSerializer,
    LocationSerializer,
    LinkSerializer,
    TaskSerializer,
    TaskLinkSerializer,
    FileAttachmentSerializer
)

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

    @action(detail=True, methods=['post'])
    def add_dependency(self, request, pk=None):
        task = self.get_object()
        dependency = Task.objects.get(pk=request.data['dependency_id'])
        task.dependencies.add(dependency)
        return Response({'status': 'dependency added'})

    @action(detail=True, methods=['post'])
    def remove_dependency(self, request, pk=None):
        task = self.get_object()
        dependency = Task.objects.get(pk=request.data['dependency_id'])
        task.dependencies.remove(dependency)
        return Response({'status': 'dependency removed'})
    
# views.py
from django.shortcuts import render, get_object_or_404

def task_form(request, pk=None):
    context = {}
    if pk:
        context['task'] = get_object_or_404(Task, pk=pk)
    return render(request, 'task_form.html', context)

def task_graph(request):
    return render(request, 'graf.html')