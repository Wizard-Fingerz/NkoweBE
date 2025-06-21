from django.contrib import admin
from django.template import RequestContext
from django.contrib.auth.admin import UserAdmin

# Register your models here.
import import_export
from import_export.admin import ImportExportModelAdmin
from django.contrib import admin
from django.contrib.admin.actions import delete_selected
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.core.mail import send_mass_mail

from account.mails.models import MailTemplate
# from classroom_app.models import InstitutionType
from .models import Administrator, Alumni, Counselor, CustomUser , Admin, GovernmentAgency, GuestLecturer, ITStaff, Librarian, Mentor, ResearchPartner, Student, Parent, InstitutionalOwner, Teacher, Tutor, Moderator, UserType

class SendMassEmailMixin:
    def send_mass_email(self, request, queryset):
        mail_template_id = request.POST.get('mail_template_id')
        if mail_template_id:
            try:
                mail_template = MailTemplate.objects.get(id=mail_template_id)
            except MailTemplate.DoesNotExist:
                self.message_user(request, 'Mail template not found', level='error')
                return
            subject = mail_template.subject
            body = mail_template.body
            emails = [obj.user.email for obj in queryset]
            messages = [(subject, body, 'from@example.com', [email]) for email in emails]
            send_mass_mail(messages, fail_silently=False)
            self.message_user(request, 'Mass email sent successfully')
        else:
            self.message_user(request, 'Please select a mail template', level='error')

    send_mass_email.short_description = 'Send mass email'

@admin.register(CustomUser )
class CustomUserAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('username', 'first_name', 'last_name' ,'email', 'user_type')
    list_filter = ('user_type',)
    search_fields = ('username', 'email')
    actions = ['delete_selected', 'send_mass_email']

@admin.register(Admin)
class AdminAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('user', )
    search_fields = ('user__username', 'user__email')
    actions = ['delete_selected', 'send_mass_email']

@admin.register(Student)
class StudentAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('user', 'date_of_birth', 'state', 'country', 'grade_level')
    list_filter = ('grade_level', 'state', 'country')
    search_fields = ('user__username', 'user__email', 'state', 'country')
    actions = ['delete_selected', 'send_mass_email']

   
@admin.register(Parent)
class ParentAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('user', 'name', 'email', 'phone', 'address', 'relationship')
    list_filter = ('relationship',)
    search_fields = ('user__username', 'user__email', 'name', 'email', 'phone', 'address')
    actions = ['delete_selected', 'send_mass_email']

@admin.register(Tutor)
class TutorAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('user', 'date_of_birth', 'state', 'country', 'qualification', 'experience')
    list_filter = ('state', 'country', 'qualification')
    search_fields = ('user__username', 'user__email', 'state', 'country', 'qualification', 'experience')
    actions = ['delete_selected', 'send_mass_email']

@admin.register(Moderator)
class ModeratorAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('user', )
    search_fields = ('user__username', 'user__email')
    actions = ['delete_selected', 'send_mass_email']


@admin.register(Teacher)
class TeacherAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('user', 'subject_specialization', 'experience', 'qualifications')
    list_filter = ('subject_specialization',)
    search_fields = ('user__username', 'subject_specialization', 'experience', 'qualifications')
    actions = ['delete_selected', 'send_mass_email']

@admin.register(Counselor)
class CounselorAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('user', 'specialization', 'experience', 'qualifications')
    list_filter = ('specialization',)
    search_fields = ('user__username', 'specialization', 'experience', 'qualifications')
    actions = ['delete_selected', 'send_mass_email']

@admin.register(Administrator)
class AdministratorAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('user', 'role', 'experience', 'qualifications')
    list_filter = ('role',)
    search_fields = ('user__username', 'role', 'experience', 'qualifications')
    actions = ['delete_selected', 'send_mass_email']

@admin.register(Librarian)
class LibrarianAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('user', 'experience', 'qualifications')
    search_fields = ('user__username', 'experience', 'qualifications')
    actions = ['delete_selected', 'send_mass_email']

@admin.register(ITStaff)
class ITStaffAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('user', 'role', 'experience', 'qualifications')
    list_filter = ('role',)
    search_fields = ('user__username', 'role', 'experience', 'qualifications')
    actions = ['delete_selected', 'send_mass_email']

@admin.register(Alumni)
class AlumniAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('user', 'graduation_year', 'degree')
    list_filter = ('graduation_year',)
    search_fields = ('user__username', 'graduation_year', 'degree')
    actions = ['delete_selected', 'send_mass_email']

@admin.register(GuestLecturer)
class GuestLecturerAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('user', 'subject_specialization', 'experience', 'qualifications')
    list_filter = ('subject_specialization',)
    search_fields = ('user__username', 'subject_specialization', 'experience', 'qualifications')
    actions = ['delete_selected', 'send_mass_email']

@admin.register(Mentor)
class MentorAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('user', 'experience', 'qualifications')
    search_fields = ('user__username', 'experience', 'qualifications')
    actions = ['delete_selected', 'send_mass_email']

@admin.register(ResearchPartner)
class ResearchPartnerAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('user', 'organization', 'research_interests')
    list_filter = ('organization',)
    search_fields = ('user__username', 'organization', 'research_interests')
    actions = ['delete_selected', 'send_mass_email']

@admin.register(GovernmentAgency)
class GovernmentAgencyAdmin(ImportExportModelAdmin, SendMassEmailMixin):
    list_display = ('user', 'agency_name', 'role')
    list_filter = ('agency_name',)
    search_fields = ('user__username', 'agency_name', 'role')
    actions = ['delete_selected', 'send_mass_email']

@admin.register(UserType)
class UserTypeAdmin(ImportExportModelAdmin):
    list_display = ('name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active', 'is_deleted')
    search_fields = ('name', 'description')
    ordering = ('name',)
    readonly_fields = ('custom_id', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Status', {
            'fields': ('is_active', 'is_deleted')
        }),
        ('System Information', {
            'fields': ('custom_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

