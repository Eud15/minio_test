# file_manager/views.py

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.generic import ListView
from django.core.files.storage import default_storage
from .models import Document, Image, TestFile
import boto3
from botocore.exceptions import ClientError

def home(request):
    """Page d'accueil avec statistiques"""
    context = {
        'documents_count': Document.objects.count(),
        'images_count': Image.objects.count(),
        'test_files_count': TestFile.objects.count(),
        'recent_documents': Document.objects.all()[:5],
        'recent_images': Image.objects.all()[:5],
    }
    return render(request, 'file_manager/home.html', context)

def upload_document(request):
    """Upload de documents vers MinIO avec sauvegarde en base"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        file = request.FILES.get('file')
        
        if title and file:
            try:
                # Créer l'enregistrement Document
                document = Document.objects.create(
                    title=title,
                    description=description,
                    file=file,
                    original_filename=file.name
                )
                
                # Générer une URL pré-signée pour l'accès
                presigned_url = document.get_presigned_url(86400)  # 24 heures
                
                return JsonResponse({
                    'success': True,
                    'message': f'Document "{title}" uploadé avec succès!',
                    'file_url': presigned_url or document.get_file_url(),
                    'document_id': document.id,
                    'file_size': document.get_file_size_display(),
                    'original_filename': document.original_filename
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Erreur lors de l\'upload: {str(e)}'
                })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Titre et fichier requis'
            })
    
    return render(request, 'file_manager/upload_document.html')

def upload_image(request):
    """Upload d'images vers MinIO avec sauvegarde en base"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        image = request.FILES.get('image')
        
        if name and image:
            try:
                # Créer l'enregistrement Image
                image_obj = Image.objects.create(
                    name=name,
                    description=description,
                    image=image,
                    original_filename=image.name
                )
                
                # Générer une URL pré-signée pour l'accès
                presigned_url = image_obj.get_presigned_url(86400)  # 24 heures
                
                return JsonResponse({
                    'success': True,
                    'message': f'Image "{name}" uploadée avec succès!',
                    'file_url': presigned_url or image_obj.image.url,
                    'image_id': image_obj.id,
                    'file_size': image_obj.get_file_size_display(),
                    'dimensions': image_obj.get_dimensions_display(),
                    'original_filename': image_obj.original_filename
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Erreur lors de l\'upload: {str(e)}'
                })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Nom et image requis'
            })
    
    return render(request, 'file_manager/upload_image.html')

def quick_test(request):
    """Test rapide d'upload avec sauvegarde en base"""
    if request.method == 'POST':
        name = request.POST.get('name')
        file = request.FILES.get('file')
        
        if name and file:
            try:
                # Créer l'enregistrement TestFile
                test_file = TestFile.objects.create(
                    name=name,
                    file=file
                )
                
                return JsonResponse({
                    'success': True,
                    'file_id': test_file.id,
                    'file_url': test_file.file.url,
                    'file_name': test_file.file.name,
                    'file_size': f'{test_file.file_size} bytes'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Erreur lors de l\'upload: {str(e)}'
                })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Nom et fichier requis'
            })
    
    files = TestFile.objects.all().order_by('-created_at')
    return render(request, 'file_manager/quick_test.html', {'files': files})

class DocumentListView(ListView):
    model = Document
    template_name = 'file_manager/list_documents.html'
    context_object_name = 'documents'
    paginate_by = 10
    ordering = ['-uploaded_at']

class ImageListView(ListView):
    model = Image
    template_name = 'file_manager/list_images.html'
    context_object_name = 'images'
    paginate_by = 12
    ordering = ['-uploaded_at']

def delete_document(request, document_id):
    """Supprimer un document"""
    document = get_object_or_404(Document, id=document_id)
    
    if request.method == 'POST':
        # Supprimer le fichier de MinIO
        try:
            document.file.delete()
        except Exception as e:
            print(f"Erreur lors de la suppression du fichier: {e}")
        
        # Supprimer l'enregistrement de la base de données
        title = document.title
        document.delete()
        
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'success': True,
                'message': f'Document "{title}" supprimé avec succès'
            })
        
        messages.success(request, f'Document "{title}" supprimé avec succès!')
        return redirect('file_manager:list_documents')
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

def delete_image(request, image_id):
    """Supprimer une image"""
    image = get_object_or_404(Image, id=image_id)
    
    if request.method == 'POST':
        # Supprimer le fichier de MinIO
        try:
            image.image.delete()
        except Exception as e:
            print(f"Erreur lors de la suppression du fichier: {e}")
        
        # Supprimer l'enregistrement de la base de données
        name = image.name
        image.delete()
        
        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({
                'success': True,
                'message': f'Image "{name}" supprimée avec succès'
            })
        
        messages.success(request, f'Image "{name}" supprimée avec succès!')
        return redirect('file_manager:list_images')
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})

def minio_status(request):
    """Vérifier le statut de MinIO et afficher les statistiques"""
    try:
        client = boto3.client(
            's3',
            endpoint_url='http://localhost:9000',
            aws_access_key_id='minioadmin',
            aws_secret_access_key='minioadmin123',
            region_name='us-east-1'
        )
        
        # Tester la connexion
        buckets = client.list_buckets()
        
        # Vérifier si notre bucket existe
        bucket_exists = False
        for bucket in buckets['Buckets']:
            if bucket['Name'] == 'django-test':
                bucket_exists = True
                break
        
        # Créer le bucket s'il n'existe pas
        if not bucket_exists:
            client.create_bucket(Bucket='django-test')
            bucket_status = "créé"
        else:
            bucket_status = "existe"
        
        # Compter les objets dans le bucket
        try:
            objects = client.list_objects_v2(Bucket='django-test')
            object_count = objects.get('KeyCount', 0)
            
            # Calculer la taille totale
            total_size = 0
            if 'Contents' in objects:
                total_size = sum(obj['Size'] for obj in objects['Contents'])
        except:
            object_count = 0
            total_size = 0
        
        # Statistiques de la base de données
        db_stats = {
            'documents': Document.objects.count(),
            'images': Image.objects.count(),
            'test_files': TestFile.objects.count(),
        }
        
        return JsonResponse({
            'success': True,
            'minio_connected': True,
            'bucket_name': 'django-test',
            'bucket_status': bucket_status,
            'minio_object_count': object_count,
            'minio_total_size': total_size,
            'database_stats': db_stats,
            'endpoint': 'http://localhost:9000'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'minio_connected': False,
            'error': str(e),
            'endpoint': 'http://localhost:9000'
        })

def get_file_stats(request):
    """API pour obtenir les statistiques des fichiers"""
    try:
        # Statistiques de la base de données
        stats = {
            'documents': {
                'count': Document.objects.count(),
                'total_size': sum(doc.file_size for doc in Document.objects.all()),
                'recent': Document.objects.order_by('-uploaded_at')[:3].values(
                    'id', 'title', 'uploaded_at', 'file_size'
                )
            },
            'images': {
                'count': Image.objects.count(),
                'total_size': sum(img.file_size for img in Image.objects.all()),
                'recent': Image.objects.order_by('-uploaded_at')[:3].values(
                    'id', 'name', 'uploaded_at', 'file_size'
                )
            },
            'test_files': {
                'count': TestFile.objects.count(),
                'total_size': sum(tf.file_size for tf in TestFile.objects.all()),
                'recent': TestFile.objects.order_by('-created_at')[:3].values(
                    'id', 'name', 'created_at', 'file_size'
                )
            }
        }
        
        return JsonResponse({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

# Classes génériques pour compatibilité (au cas où)
class DocumentListView(ListView):
    model = Document
    template_name = 'file_manager/list_documents.html'
    context_object_name = 'documents'
    paginate_by = 10
    ordering = ['-uploaded_at']

class ImageListView(ListView):
    model = Image
    template_name = 'file_manager/list_images.html'
    context_object_name = 'images'
    paginate_by = 12
    ordering = ['-uploaded_at']