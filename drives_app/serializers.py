from rest_framework import serializers
from .models import DriveFolder, DriveFile


class DriveFileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = DriveFile
        fields = ['id', 'name', 'folder', 'file', 'file_url', 'size', 'mime_type', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'size', 'created_at', 'updated_at']

    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None


class DriveFolderSerializer(serializers.ModelSerializer):
    files = DriveFileSerializer(many=True, read_only=True)
    children_count = serializers.SerializerMethodField()
    files_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DriveFolder
        fields = ['id', 'name', 'parent', 'is_default', 'files', 'children_count', 'files_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'owner', 'is_default', 'created_at', 'updated_at']

    def get_children_count(self, obj):
        return obj.children.count()

    def get_files_count(self, obj):
        return obj.files.count()


class DriveTreeSerializer(serializers.ModelSerializer):
    """Recursive serializer for folder tree structure"""
    children = serializers.SerializerMethodField()
    files = DriveFileSerializer(many=True, read_only=True)
    type = serializers.SerializerMethodField()
    
    class Meta:
        model = DriveFolder
        fields = ['id', 'name', 'type', 'is_default', 'children', 'files', 'created_at', 'updated_at']

    def get_type(self, obj):
        return 'folder'

    def get_children(self, obj):
        children_folders = obj.children.all()
        return DriveTreeSerializer(children_folders, many=True, context=self.context).data
