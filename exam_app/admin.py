from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Exam, Question, Choice, ExamAttempt, Answer

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4

class QuestionResource(resources.ModelResource):
    class Meta:
        model = Question
        fields = ('id', 'exam', 'question_text', 'question_type', 'marks', 'order')
        export_order = fields

class ExamResource(resources.ModelResource):
    class Meta:
        model = Exam
        fields = ('id', 'subject', 'title', 'description', 'duration', 'total_marks',
                 'passing_marks', 'start_time', 'end_time', 'is_published',
                 'created_at', 'updated_at')
        export_order = fields

class ExamAttemptResource(resources.ModelResource):
    class Meta:
        model = ExamAttempt
        fields = ('id', 'exam', 'student', 'start_time', 'end_time', 'score',
                 'is_completed')
        export_order = fields

class AnswerResource(resources.ModelResource):
    class Meta:
        model = Answer
        fields = ('id', 'attempt', 'question', 'answer_text', 'marks_obtained')
        export_order = fields

@admin.register(Exam)
class ExamAdmin(ImportExportModelAdmin):
    resource_class = ExamResource
    list_display = ('title', 'subject', 'start_time', 'end_time', 'is_published')
    list_filter = ('is_published', 'subject')
    search_fields = ('title', 'description')
    ordering = ('-start_time',)
    raw_id_fields = ('subject',)

@admin.register(Question)
class QuestionAdmin(ImportExportModelAdmin):
    resource_class = QuestionResource
    list_display = ('question_text', 'exam', 'question_type', 'marks', 'order')
    list_filter = ('question_type', 'exam')
    search_fields = ('question_text',)
    ordering = ('exam', 'order')
    raw_id_fields = ('exam',)
    inlines = [ChoiceInline]

@admin.register(ExamAttempt)
class ExamAttemptAdmin(ImportExportModelAdmin):
    resource_class = ExamAttemptResource
    list_display = ('exam', 'student', 'start_time', 'end_time', 'score', 'is_completed')
    list_filter = ('is_completed', 'exam')
    search_fields = ('exam__title', 'student__username')
    ordering = ('-start_time',)
    raw_id_fields = ('exam', 'student')

@admin.register(Answer)
class AnswerAdmin(ImportExportModelAdmin):
    resource_class = AnswerResource
    list_display = ('attempt', 'question', 'marks_obtained')
    list_filter = ('attempt__exam',)
    search_fields = ('answer_text', 'attempt__student__username')
    raw_id_fields = ('attempt', 'question')
