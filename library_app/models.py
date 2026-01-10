from django.db import models

from account.models import CustomUser
from classroom_app.institution.models import Institution
from library_app.catalogue.models import Catalogue
from library_app.definitions.models import Genre  # Make sure this import path is correct


class Author(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    biography = models.TextField(blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Publisher(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300, blank=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    authors = models.ManyToManyField(Author, related_name="books")
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    isbn = models.CharField(max_length=13, unique=True)
    genre = models.ManyToManyField(Genre, related_name="books")
    description = models.TextField(blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    file = models.FileField(upload_to="uploaded_books/", null=True, blank=True, help_text="Upload a digital version of the book (PDF, EPUB, etc.)")
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="uploaded_books", help_text="The librarian who uploaded this book")

    # NEW: Institution-specific ownership (null means general/public library)
    institution = models.ForeignKey(
        Institution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="institution_books",
        help_text="The institution that owns and manages this book's library (blank for public/general library)"
    )

    # Optionally support catalogues in the future, leave a placeholder:
    catalogue = models.ForeignKey(Catalogue, on_delete=models.SET_NULL, null=True, blank=True, related_name="books")

    def __str__(self):
        return self.title

class Member(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="library_profile")
    address = models.CharField(max_length=300, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    joined_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    # NEW: Membership can be institution-based or public (null means public)
    institution = models.ForeignKey(
        Institution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="institution_members",
        help_text="The institution this membership belongs to (blank for public/general membership)"
    )

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class LibraryCollection(models.Model):
    """
    A user-owned library collection.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="owned_collections",
        help_text="The user who owns this collection"
    )
    books = models.ManyToManyField(Book, related_name="collections", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} (owned by {self.owner.get_full_name() or self.owner.username})"