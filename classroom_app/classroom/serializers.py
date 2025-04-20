from rest_framework import serializers
from .models import Classroom, ClassroomTermsAndConditions, ClassroomTutor, ClassroomStudent, ExaminationType, ClassroomExamination, ClassroomAttachment


class DetailedClassroomSerializer(serializers.ModelSerializer):
    participantCount = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    avatars = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    classDetails = serializers.SerializerMethodField()

    class Meta:
        model = Classroom
        fields = ['id', 'name', 'institution', 'subject', 'capacity', 'description', 'created_at',
                  'updated_at', 'participantCount', 'tags', 'avatars', 'attachments', 'comments', 'classDetails']

    def get_participantCount(self, obj):
        return obj.classroomstudent_set.count()

    def get_tags(self, obj):
        # Assuming you have a many-to-many field for tags in your Classroom model
        return [tag.name for tag in obj.tags.all()]

    def get_avatars(self, obj):
        # Assuming you have a many-to-many field for students in your Classroom model
        return [student.avatar for student in obj.classroomstudent_set.all()[:10]]

    def get_attachments(self, obj):
        return obj.classroomattachment_set.count()

    def get_comments(self, obj):
        # Assuming you have a many-to-many field for comments in your Classroom model
        return obj.classroomcomment_set.count()

    def get_classDetails(self, obj):
        return {
            'title': obj.name,
            'description': obj.description,
            'terms': 'By joining this class, you agree to follow the course guidelines and participate in discussions.',
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
