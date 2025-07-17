# file_manager/urls.py

from django.urls import path
from . import views

app_name = 'file_manager'

urlpatterns = [
    path('', views.home, name='home'),
    path('upload/document/', views.upload_document, name='upload_document'),
    path('upload/image/', views.upload_image, name='upload_image'),
    path('test/', views.quick_test, name='quick_test'),
    path('documents/', views.DocumentListView.as_view(), name='list_documents'),
    path('images/', views.ImageListView.as_view(), name='list_images'),
    path('delete/document/<int:document_id>/', views.delete_document, name='delete_document'),
    path('delete/image/<int:image_id>/', views.delete_image, name='delete_image'),
    path('api/minio-status/', views.minio_status, name='minio_status'),
    path('api/file-stats/', views.get_file_stats, name='file_stats'),
]