from django.contrib import admin
from .models import (
    Author, Publisher, Book, Member, LibraryCollection, RecentlyReadBook
)
from library_app.definitions.models import Genre
from library_app.catalogue.models import Catalogue

# Inline for Books on Author detail
class BookInline(admin.TabularInline):
    model = Book.authors.through
    extra = 0

# Inline for RecentlyReadBook on Member detail
class RecentlyReadBookInline(admin.TabularInline):
    model = RecentlyReadBook
    extra = 0
    autocomplete_fields = ['book']

# Inline for Books in a LibraryCollection
class LibraryCollectionBooksInline(admin.TabularInline):
    model = LibraryCollection.books.through
    extra = 0
    verbose_name = "Book in Collection"
    verbose_name_plural = "Books in Collection"
    autocomplete_fields = ['book']

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'dob')
    search_fields = ('first_name', 'last_name')
    list_filter = ('dob',)
    inlines = [BookInline]
    exclude = ('books',)  # Since using the through-model in inline

@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'website')
    search_fields = ('name',)
    list_filter = ('name',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'publisher', 'publication_date', 'isbn',
        'total_copies', 'available_copies', 'institution',
        'get_authors', 'get_genres', 'catalogue'
    )
    search_fields = ('title', 'isbn')
    list_filter = ('publisher', 'publication_date', 'institution', 'genre', 'catalogue')
    filter_horizontal = ('authors', 'genre')

    def get_authors(self, obj):
        return ", ".join([str(a) for a in obj.authors.all()])
    get_authors.short_description = 'Authors'

    def get_genres(self, obj):
        return ", ".join([g.name for g in obj.genre.all()])
    get_genres.short_description = 'Genres'

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'joined_date', 'is_active', 'institution')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone_number')
    list_filter = ('joined_date', 'is_active', 'institution')
    inlines = [RecentlyReadBookInline]

@admin.register(LibraryCollection)
class LibraryCollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at', 'visibility')
    search_fields = ('name', 'owner__username', 'owner__first_name', 'owner__last_name')
    list_filter = ('created_at', 'visibility')
    inlines = [LibraryCollectionBooksInline]
    exclude = ('books',)  # Since using the through-model in inline

@admin.register(RecentlyReadBook)
class RecentlyReadBookAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'last_read_at')
    search_fields = ('user__username', 'book__title')
    list_filter = ('last_read_at', 'user')

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    list_filter = ('name',)

@admin.register(Catalogue)
class CatalogueAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_by', 'created_at')
    search_fields = ('name', 'description', 'created_by__username')
    list_filter = ('created_at',)