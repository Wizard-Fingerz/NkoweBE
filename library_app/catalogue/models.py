
from django.db import models
from account.models import CustomUser


class Catalogue(models.Model):
    """A catalogue grouping together books in the library."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="created_catalogues")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name