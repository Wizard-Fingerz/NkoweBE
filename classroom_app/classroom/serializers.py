from rest_framework import serializers
from .models import Classroom, ClassroomTermsAndConditions, ClassroomTutor, ClassroomStudent, ExaminationType, ClassroomExamination, ClassroomAttachment


class DetailedClassroomSerializer(serializers.ModelSerializer):
    participantCount = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    avatars = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    classDetails = serializers.SerializerMethodField()
    examinations = serializers.SerializerMethodField()

    class Meta:
        model = Classroom
        fields = [
            'id', 'name', 'institution', 'subject', 'capacity', 'description', 'created_at',
            'updated_at', 'participantCount', 'tags', 'avatars', 'attachments',
            'comments', 'examinations', 'classDetails'
        ]

    def get_participantCount(self, obj):
        return obj.classroomstudent_set.count()

    def get_tags(self, obj):
        return [tag.name for tag in obj.tag.all()]

    def get_avatars(self, obj):
        # Return URLs or paths of student avatars
        students = obj.classroomstudent_set.select_related('student__user').all()[:10]
        return [student.student.profile_picture.url if student.student.profile_picture else None for student in students]

    def get_attachments(self, obj):
        return obj.classroomattachment_set.count()

    def get_comments(self, obj):
        return obj.comment_set.count()

    def get_examinations(self, obj):
        return [
            {
                "id": exam.id,
                "type": exam.examination_type.name,  # Exam Type name
                "description": exam.description,
            }
            for exam in obj.classroomexamination_set.select_related('examination_type').all()
        ]

    def get_classDetails(self, obj):
        terms = ""
        try:
            terms_obj = obj.classroomtermsandconditions
            terms = terms_obj.terms_and_conditions
        except ClassroomTermsAndConditions.DoesNotExist:
            terms = "By joining this class, you agree to follow the course guidelines and participate in discussions."
        
        return {
            "title": obj.name,
            "description": obj.description,
            "terms": terms,
        }


class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = ['id', 'name', 'institution', 'tag', 'subject',
                  'capacity', 'description', 'created_at', 'updated_at']


class ClassroomTutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomTutor
        fields = ['id', 'classroom', 'tutor', 'role']


class ClassroomStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomStudent
        fields = ['id', 'classroom', 'student']


class ExaminationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExaminationType
        fields = ['id', 'name']


class ClassroomExaminationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomExamination
        fields = ['id', 'classroom', 'examination_type', 'description']


class ClassroomAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomAttachment
        fields = ['id', 'classroom', 'file', 'description', 'uploaded_at']


class ClassroomTermsAndConditionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomTermsAndConditions
        fields = ['id', 'classroom', 'terms_and_conditions',
                  'created_at', 'updated_at']
