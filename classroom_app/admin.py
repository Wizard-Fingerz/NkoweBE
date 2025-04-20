from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

# Register your models here.

from django.urls import reverse
from django.utils.html import format_html

from django.contrib import admin
from django.template import RequestContext
from import_export.admin import ImportExportModelAdmin
from django.contrib.admin.actions import delete_selected
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.core.mail import send_mass_mail

from classroom_app.institution.models import Institution, InstitutionType
from classroom_app.definitions.subjects.models import Subject

from .classroom.models import Classroom, ClassroomTermsAndConditions, ClassroomTutor, ClassroomStudent, ExaminationType, ClassroomExamination, ClassroomAttachment, Tag, Comment


class SendMassEmailMixin:
    def send_mass_email(self, request, queryset):
        # Implement your mass email sending logic here
        pass

    send_mass_email.short_description = 'Send mass email'


@admin.register(InstitutionType)
class InstitutionTypeAdmin(ImportExportModelAdmin):
    list_display = ('name', )
    search_fields = ('name', )
    actions = ['delete_selected']


@admin.register(Classroom)
class ClassroomAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('name', 'institution', 
                    'capacity', 'description')
    list_filter = ('institution', 'subject')
    search_fields = ('name', 'institution__name', 'subject__name')
    actions = ['delete_selected', 'send_mass_email']


@admin.register(ClassroomTutor)
class ClassroomTutorAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('classroom', 'tutor', 'role')
    list_filter = ('classroom', 'tutor')
    search_fields = ('classroom__name', 'tutor__username')
    actions = ['delete_selected', 'send_mass_email']


@admin.register(ClassroomStudent)
class ClassroomStudentAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('classroom', 'student')
    list_filter = ('classroom', 'student')
    search_fields = ('classroom__name', 'student__username')
    actions = ['delete_selected', 'send_mass_email']


@admin.register(ExaminationType)
class ExaminationTypeAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('name',)
    search_fields = ('name',)
    actions = ['delete_selected', 'send_mass_email']


@admin.register(ClassroomExamination)
class ClassroomExaminationAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('classroom', 'examination_type', 'description')
    list_filter = ('classroom', 'examination_type')
    search_fields = ('classroom__name', 'examination_type__name')
    actions = ['delete_selected', 'send_mass_email']


@admin.register(ClassroomAttachment)
class ClassroomAttachmentAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('classroom', 'file', 'description')
    list_filter = ('classroom',)
    search_fields = ('classroom__name', 'description')
    actions = ['delete_selected', 'send_mass_email']


@admin.register(Tag)
class TagAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('name',)
    search_fields = ('name',)
    actions = ['delete_selected', 'send_mass_email']


@admin.register(Comment)
class CommentAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('classroom', 'text', 'created_at')
    list_filter = ('classroom',)
    search_fields = ('classroom__name', 'text')
    actions = ['delete_selected', 'send_mass_email']


@admin.register(ClassroomTermsAndConditions)
class ClassroomTermsAndConditionsAdmin(ImportExportModelAdmin):
    list_display = ('classroom', 'created_at', 'updated_at', 'view_terms_and_conditions')
    list_filter = ('classroom',)
    search_fields = ('classroom__name', 'terms_and_conditions')
    actions = ['delete_selected']

    def view_terms_and_conditions(self, obj):
        url = reverse('view_terms_and_conditions', args=[obj.id])
        return format_html('<a href="{}">View Terms and Conditions</a>', url)

    view_terms_and_conditions.short_description = 'View Terms and Conditions'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    


@admin.register(Institution)
class InstitutionAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('name', 'institution_type', 'address', 'phone', 'email')
    list_filter = ('institution_type',)
    search_fields = ('name', 'address', 'phone', 'email')
    actions = ['delete_selected', 'send_mass_email']

@admin.register(Subject)
class SubjectAdmin(ImportExportModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    actions = ['delete_selected']

    def delete_selected(self, request, queryset):
        # Custom delete action logic
        for obj in queryset:
            obj.delete()
        self.message_user(request, "Selected subjects have been deleted.")