from django.db import models


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="The name of the genre (e.g. Fiction, History, Romance).")
    description = models.TextField(blank=True, help_text="A brief description of this genre.")

    def __str__(self):
        return self.name