from django.contrib import admin
from .models import DriveFolder, DriveFile


@admin.register(DriveFolder)
class DriveFolderAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'parent', 'is_default', 'created_at']
    list_filter = ['is_default', 'created_at']
    search_fields = ['name', 'owner__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DriveFile)
class DriveFileAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'folder', 'size', 'mime_type', 'created_at']
    list_filter = ['mime_type', 'created_at']
    search_fields = ['name', 'owner__username']
    readonly_fields = ['size', 'created_at', 'updated_at']
