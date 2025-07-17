# file_manager/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import Document, Image, TestFile

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'file_name', 'file_size_display', 'uploaded_at', 'file_link']
    list_filter = ['uploaded_at']
    search_fields = ['title', 'description']
    readonly_fields = ['file_size', 'uploaded_at', 'file_link']
    
    def file_name(self, obj):
        if obj.file:
            return obj.file.name.split('/')[-1]
        return "Aucun fichier"
    file_name.short_description = "Nom du fichier"
    
    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = "Taille"
    
    def file_link(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank" class="button">Voir le fichier</a>',
                obj.file.url
            )
        return "Aucun fichier"
    file_link.short_description = "Lien"

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['name', 'dimensions_display', 'uploaded_at', 'image_preview', 'image_link']
    list_filter = ['uploaded_at']
    search_fields = ['name', 'description']
    readonly_fields = ['width', 'height', 'uploaded_at', 'image_preview', 'image_link']
    
    def dimensions_display(self, obj):
        return obj.get_dimensions_display()
    dimensions_display.short_description = "Dimensions"
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 100px;" />',
                obj.image.url
            )
        return "Aucune image"
    image_preview.short_description = "Aperçu"
    
    def image_link(self, obj):
        if obj.image:
            return format_html(
                '<a href="{}" target="_blank" class="button">Voir l\'image</a>',
                obj.image.url
            )
        return "Aucune image"
    image_link.short_description = "Lien"

@admin.register(TestFile)
class TestFileAdmin(admin.ModelAdmin):
    list_display = ['name', 'file_name', 'created_at', 'file_link']
    list_filter = ['created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'file_link']
    
    def file_name(self, obj):
        if obj.file:
            return obj.file.name.split('/')[-1]
        return "Aucun fichier"
    file_name.short_description = "Nom du fichier"
    
    def file_link(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank" class="button">Voir le fichier</a>',
                obj.file.url
            )
        return "Aucun fichier"
    file_link.short_description = "Lien"
    
    actions = ['delete_selected_files']
    
    def delete_selected_files(self, request, queryset):
        """Action personnalisée pour supprimer les fichiers de MinIO aussi"""
        count = 0
        for obj in queryset:
            try:
                if obj.file:
                    obj.file.delete()  # Supprime de MinIO
                obj.delete()  # Supprime de la DB
                count += 1
            except Exception as e:
                self.message_user(request, f"Erreur lors de la suppression de {obj.name}: {e}")
        
        if count > 0:
            self.message_user(request, f"{count} fichier(s) supprimé(s) avec succès.")
    
    delete_selected_files.short_description = "Supprimer les fichiers sélectionnés (MinIO + DB)"