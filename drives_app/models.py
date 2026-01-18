from django.db import models
from django.conf import settings


class DriveFolder(models.Model):
    """Represents a folder in the user's drive"""
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='drive_folders')
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    is_default = models.BooleanField(default=False)  # For system folders like Documents, Music, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ['owner', 'name', 'parent']

    def __str__(self):
        return f"{self.owner.username}/{self.name}"


class DriveFile(models.Model):
    """Represents a file in the user's drive"""
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='drive_files')
    name = models.CharField(max_length=255)
    folder = models.ForeignKey(DriveFolder, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='drives/%Y/%m/%d/')
    size = models.BigIntegerField()  # in bytes
    mime_type = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.owner.username}/{self.folder.name}/{self.name}"

    def save(self, *args, **kwargs):
        if self.file:
            self.size = self.file.size
        super().save(*args, **kwargs)
