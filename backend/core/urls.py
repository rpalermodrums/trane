from django.urls import path, include
from django.http import HttpResponse
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from core.views.auth import (
    RegisterView,
    CustomTokenObtainPairView,
    LogoutView
)
from core.views.views import (
    EntryViewSet, 
    NoteViewSet, 
    DocumentViewSet, 
    TagViewSet,
)

router = DefaultRouter()
router.register(r'entries', EntryViewSet)
router.register(r'notes', NoteViewSet)
router.register(r'documents', DocumentViewSet)
router.register(r'tags', TagViewSet)


def health_check(request):
    return HttpResponse("OK")

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include([
        path('register/', RegisterView.as_view(), name='register'),
        path('login/', CustomTokenObtainPairView.as_view(), name='login'),
        path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('logout/', LogoutView.as_view(), name='logout'),
    ])),
    path('health/', health_check, name='health-check'),
]
