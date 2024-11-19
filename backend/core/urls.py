from django.urls import path, include
from django.http import HttpResponse
from rest_framework.routers import DefaultRouter
from .views import EntryViewSet, NoteViewSet, DocumentViewSet, TagViewSet, example_task

router = DefaultRouter()
router.register(r'entries', EntryViewSet)
router.register(r'notes', NoteViewSet)
router.register(r'documents', DocumentViewSet)
router.register(r'tags', TagViewSet)


def health_check(request):
    return HttpResponse("OK")

urlpatterns = [
    path('example-task/', example_task, name='example-task'),
    path('health/', health_check, name='health-check'),
    path('', include(router.urls)),
]
