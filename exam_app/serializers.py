from rest_framework import serializers

from classroom_app.definitions.subjects.serializers import SubjectSerializer

from .models import Exam, Question, Choice, ExamAttempt, Answer

class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ('id', 'choice_text', 'is_correct')

class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = (
            'custom_id', 
            'question_text', 
            'question_type', 
            'marks', 
            'order', 
            'choices'
        )

class QuestionCreateSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True)
    
    class Meta:
        model = Question
        fields = (
            'question_text', 
            'question_type', 
            'marks', 
            'order', 
            'choices'
        )
    
    def create(self, validated_data):
        choices_data = validated_data.pop('choices')
        question = Question.objects.create(**validated_data)
        for choice_data in choices_data:
            Choice.objects.create(question=question, **choice_data)
        return question

class ExamSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Exam
        fields = (
            'custom_id', 'subject', 'title', 'description', 'duration', 'total_marks',
            'passing_marks', 'examination_type', 'year', 'start_time', 'end_time',
            'is_published', 'created_at', 'updated_at', 'questions'
        )

class ExamCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = (
            'title', 'description', 'duration', 'total_marks', 'passing_marks',
            'examination_type', 'year', 'start_time', 'end_time',
            'is_published', 'subject'
        )

class StaffExamCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = (
            'title', 'description', 'duration', 'total_marks', 'passing_marks',
            'examination_type', 'year', 'start_time', 'end_time', 'is_published'
        )

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ('question', 'answer_text')
        ref_name = 'ExamAppAnswerSerializer'

class ExamAttemptSerializer(serializers.ModelSerializer):
    exam = serializers.PrimaryKeyRelatedField(read_only=True)
    answers = AnswerSerializer(many=True, read_only=True)
    
    class Meta:
        model = ExamAttempt
        fields = (
            'custom_id', 'exam', 'student', 'start_time', 'end_time', 'score',
            'is_completed', 'answers'
        )
        read_only_fields = ('student', 'score', 'is_completed')

class ExamSubmissionSerializer(serializers.Serializer):
    answers = AnswerSerializer(many=True)
    
    def validate(self, data):
        attempt = self.context['attempt']
        exam = attempt.exam
        
        # Validate that all questions are answered
        answered_questions = set(answer['question'].id for answer in data['answers'])
        exam_questions = set(question.id for question in exam.questions.all())
        
        if answered_questions != exam_questions:
            raise serializers.ValidationError("All questions must be answered.")
        
        return data

class ScrapeQuestionsSerializer(serializers.Serializer):
    subject = serializers.CharField()
    year = serializers.IntegerField()
    pages = serializers.IntegerField()
    slug = serializers.CharField()
    exam_type = serializers.CharField()


# --------
# PracticeExamSerializer for practice quizzes (with expected answer & comprehension)

class PracticeExamQuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)
    expected_answer = serializers.CharField()
    comprehension_reference = serializers.CharField()

    class Meta:
        model = Question
        fields = (
            'custom_id',
            'question_text',
            'question_type',
            'marks',
            'order',
            'choices',
            'expected_answer',
            'comprehension_reference'
        )

class PracticeExamSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)
    questions = PracticeExamQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Exam
        fields = (
            'custom_id',
            'subject',
            'title',
            'description',
            'duration',
            'total_marks',
            'passing_marks',
            'examination_type',
            'year',
            'start_time',
            'end_time',
            'is_published',
            'created_at',
            'updated_at',
            'questions'
        )
