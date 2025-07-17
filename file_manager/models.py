# file_manager/models.py

from django.db import models
import uuid
import os

def upload_to_documents(instance, filename):
    """Fonction pour organiser les documents"""
    ext = filename.split('.')[-1] if '.' in filename else ''
    filename = f"{uuid.uuid4()}.{ext}"
    return f"documents/{filename}"

def upload_to_images(instance, filename):
    """Fonction pour organiser les images"""
    ext = filename.split('.')[-1] if '.' in filename else ''
    filename = f"{uuid.uuid4()}.{ext}"
    return f"images/{filename}"

class Document(models.Model):
    """Modèle pour stocker les informations des documents uploadés"""
    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(blank=True, verbose_name="Description")
    file = models.FileField(upload_to=upload_to_documents, verbose_name="Fichier")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Uploadé le")
    file_size = models.PositiveIntegerField(default=0, verbose_name="Taille (bytes)")
    original_filename = models.CharField(max_length=255, blank=True, verbose_name="Nom original")
    
    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            if not self.original_filename:
                self.original_filename = self.file.name
        super().save(*args, **kwargs)
    
    def get_file_url(self):
        """Retourne l'URL du fichier"""
        if self.file:
            return self.file.url
        return None
    
    def get_file_size_display(self):
        """Affiche la taille du fichier de manière lisible"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
    
    def get_presigned_url(self, expiration=3600):
        """Génère une URL pré-signée pour accès temporaire"""
        try:
            import boto3
            client = boto3.client(
                's3',
                endpoint_url='http://localhost:9000',
                aws_access_key_id='minioadmin',
                aws_secret_access_key='minioadmin123',
                region_name='us-east-1'
            )
            
            if self.file:
                return client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': 'django-test', 'Key': self.file.name},
                    ExpiresIn=expiration
                )
        except Exception:
            pass
        return None

class Image(models.Model):
    """Modèle pour stocker les informations des images uploadées"""
    name = models.CharField(max_length=200, verbose_name="Nom")
    description = models.TextField(blank=True, verbose_name="Description")
    image = models.ImageField(upload_to=upload_to_images, verbose_name="Image")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Uploadée le")
    width = models.PositiveIntegerField(default=0)
    height = models.PositiveIntegerField(default=0)
    file_size = models.PositiveIntegerField(default=0, verbose_name="Taille (bytes)")
    original_filename = models.CharField(max_length=255, blank=True, verbose_name="Nom original")
    
    class Meta:
        verbose_name = "Image"
        verbose_name_plural = "Images"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.image:
            self.file_size = self.image.size
            if not self.original_filename:
                self.original_filename = self.image.name
        
        super().save(*args, **kwargs)
        
        # Obtenir les dimensions de l'image
        if self.image and (not self.width or not self.height):
            try:
                from PIL import Image as PILImage
                with PILImage.open(self.image) as img:
                    self.width, self.height = img.size
                    # Sauvegarder à nouveau pour mettre à jour les dimensions
                    super().save(update_fields=['width', 'height'])
            except Exception:
                pass
    
    def get_dimensions_display(self):
        """Affiche les dimensions de l'image"""
        if self.width and self.height:
            return f"{self.width} x {self.height} px"
        return "Dimensions inconnues"
    
    def get_file_size_display(self):
        """Affiche la taille du fichier de manière lisible"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
    
    def get_presigned_url(self, expiration=3600):
        """Génère une URL pré-signée pour accès temporaire"""
        try:
            import boto3
            client = boto3.client(
                's3',
                endpoint_url='http://localhost:9000',
                aws_access_key_id='minioadmin',
                aws_secret_access_key='minioadmin123',
                region_name='us-east-1'
            )
            
            if self.image:
                return client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': 'django-test', 'Key': self.image.name},
                    ExpiresIn=expiration
                )
        except Exception:
            pass
        return None

class TestFile(models.Model):
    """Modèle simple pour tester MinIO"""
    name = models.CharField(max_length=100)
    file = models.FileField(upload_to='test/')
    created_at = models.DateTimeField(auto_now_add=True)
    file_size = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Fichier de test"
        verbose_name_plural = "Fichiers de test"