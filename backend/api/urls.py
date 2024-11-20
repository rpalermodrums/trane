from django.urls import path
from . import views

urlpatterns = [
    # ... existing urls ...
    path('auth/register/', views.register_user, name='register'),
] 