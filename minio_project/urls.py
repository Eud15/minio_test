
# minio_project/urls.py
# Version propre sans imports inutiles

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('file_manager.urls')),
]