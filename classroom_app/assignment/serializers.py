from rest_framework import serializers
from .models import Assignment, Question, Answer, StudentAssignment



class RecursiveQuestionSerializer(serializers.ModelSerializer):
    subquestions = serializers.ListSerializer(child=serializers.DictField(), required=False)

    class Meta:
        model = Question
        fields = [
            "question", "type", "score", "expected_answer",
            "comprehension", "options", "subquestions"
        ]

    def create(self, validated_data):
        subquestions_data = validated_data.pop("subquestions", [])
        question = Question.objects.create(**validated_data)

        for subq_data in subquestions_data:
            self._create_subquestion(subq_data, question)

        return question

    def _create_subquestion(self, data, parent):
        subquestions_data = data.pop("subquestions", [])
        subq = Question.objects.create(parent=parent, **data)
        for sub_subq_data in subquestions_data:
            self._create_subquestion(sub_subq_data, subq)


class AssignmentSerializer(serializers.ModelSerializer):
    questions = RecursiveQuestionSerializer(many=True)

    class Meta:
        model = Assignment
        fields = ["id", "title", "total_score", "questions"]

    def create(self, validated_data):
        questions_data = validated_data.pop("questions", [])
        assignment = Assignment.objects.create(**validated_data)

        for question_data in questions_data:
            self.fields["questions"].create({
                **question_data,
                "assignment": assignment
            })

        return assignment


class AnswerSerializer(serializers.ModelSerializer):
    question = serializers.PrimaryKeyRelatedField(queryset=Question.objects.all())

    class Meta:
        model = Answer
        fields = ['id', 'question', 'response']


class StudentAssignmentSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)
    assignment = serializers.PrimaryKeyRelatedField(read_only=True)
    student = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = StudentAssignment
        fields = ['id', 'assignment', 'student', 'status', 'is_draft', 'submitted_at', 'answers']
        read_only_fields = ['submitted_at']

    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        student_assignment = StudentAssignment.objects.create(**validated_data)

        for answer_data in answers_data:
            Answer.objects.create(student_assignment=student_assignment, **answer_data)

        return student_assignment

    def update(self, instance, validated_data):
        answers_data = validated_data.pop('answers', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if not instance.is_draft:
            instance.submitted_at = timezone.now()

        instance.save()

        if answers_data is not None:
            instance.answers.all().delete()
            for answer_data in answers_data:
                Answer.objects.create(student_assignment=instance, **answer_data)

        return instance
