"""
URL configuration for trane project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from trane.realtime_dsp import views as dsp_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dsp/', dsp_views.upload_page, name='dsp_upload'),
    path('dsp/upload/', dsp_views.upload_file, name='dsp_upload_file'),
    path('dsp/result/<str:task_id>/', dsp_views.get_result, name='dsp_get_result'),
]
