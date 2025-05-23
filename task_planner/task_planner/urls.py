# urls.py (основной)
from django.urls import path, include
from rest_framework import routers
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from tasks import views
from django.contrib import admin

router = routers.DefaultRouter()
router.register(r'task-categories', views.TaskCategoryViewSet)
router.register(r'notification-methods', views.NotificationMethodViewSet)
router.register(r'locations', views.LocationViewSet)
router.register(r'links', views.LinkViewSet)
router.register(r'task-links', views.TaskLinkViewSet)
router.register(r'attachments', views.FileAttachmentViewSet)
router.register(r'tasks', views.TaskViewSet)

schema_view = get_schema_view(
    openapi.Info(
        title="Task Management API",
        default_version='v1',
        description="API для управления задачами",
        contact=openapi.Contact(email="admin@example.com"),
    ),
    public=True,
    permission_classes=(AllowAny,),
)

urlpatterns = [
    path('', include(router.urls)),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path("admin/", admin.site.urls),
]

