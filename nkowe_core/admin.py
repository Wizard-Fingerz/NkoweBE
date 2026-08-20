from django.contrib import admin

from .models import Enrollment, LearnerIdentity, LearnerRecordEvent, LearningJourney


@admin.register(LearnerIdentity)
class LearnerIdentityAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'display_name', 'created_at')
    search_fields = ('display_name', 'user__username', 'user__email')


@admin.register(LearningJourney)
class LearningJourneyAdmin(admin.ModelAdmin):
    list_display = ('id', 'learner', 'title', 'journey_type', 'institution', 'is_active', 'started_at')
    list_filter = ('journey_type', 'is_active')
    search_fields = ('title', 'learner__display_name', 'learner__user__username')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'journey', 'institution', 'program', 'status', 'provenance', 'start_date')
    list_filter = ('status', 'provenance')


@admin.register(LearnerRecordEvent)
class LearnerRecordEventAdmin(admin.ModelAdmin):
    list_display = ('id', 'learner', 'source_app', 'event_type', 'provenance_category', 'occurred_at')
    list_filter = ('source_app', 'provenance_category')
    readonly_fields = ('recorded_at',)
