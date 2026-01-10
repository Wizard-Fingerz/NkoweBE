from django.contrib import admin
from .models import Author, Publisher, Book, Member

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'dob')
    search_fields = ('first_name', 'last_name')
    list_filter = ('dob',)

@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'website')
    search_fields = ('name',)
    list_filter = ('name',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'publisher', 'publication_date', 'isbn', 'total_copies', 'available_copies', 'institution')
    search_fields = ('title', 'isbn')
    list_filter = ('publisher', 'publication_date', 'institution')

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'joined_date', 'is_active', 'institution')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone_number')
    list_filter = ('joined_date', 'is_active', 'institution')
