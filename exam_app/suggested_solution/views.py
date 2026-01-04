from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework.authentication import TokenAuthentication
from .models import SuggestedSolution, SuggestedSolutionVote, SolutionComment
from .serializers import SuggestedSolutionSerializer, SuggestedSolutionVoteSerializer, SolutionCommentSerializer

class SuggestedSolutionViewSet(viewsets.ModelViewSet):
    queryset = SuggestedSolution.objects.all()
    serializer_class = SuggestedSolutionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    authentication_classes = [TokenAuthentication]

    def create(self, request, *args, **kwargs):
        from exam_app.models import Question
        question_custom_id = request.data.get("question")
        if not question_custom_id:
            raise PermissionDenied("question__custom_id is required to create a suggested solution.")
        try:
            question = Question.objects.get(custom_id=question_custom_id)
        except Question.DoesNotExist:
            raise PermissionDenied("No question found for the given custom_id.")
        # Construct data with pk instead of custom_id to avoid incorrect type error
        input_data = request.data.copy()
        input_data["question"] = question.pk  # Use pk, not custom_id
        serializer = self.get_serializer(data=input_data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, question=question)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def get_queryset(self):
        queryset = super().get_queryset()
        question_id = self.request.query_params.get("question")
        if question_id:
            queryset = queryset.filter(question__custom_id=question_id)
        return queryset

    def perform_update(self, serializer):
        # Only the author of the solution can update
        solution = self.get_object()
        if solution.user != self.request.user:
            raise PermissionDenied("You can only update your own solutions.")
        serializer.save()

    def perform_destroy(self, instance):
        # Only the author of the solution can delete
        if instance.user != self.request.user:
            raise PermissionDenied("You can only delete your own solutions.")
        instance.delete()


class SuggestedSolutionVoteViewSet(viewsets.ModelViewSet):
    queryset = SuggestedSolutionVote.objects.all()
    serializer_class = SuggestedSolutionVoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        solution_id = self.request.data.get("solution")
        solution = get_object_or_404(SuggestedSolution, pk=solution_id)
        # Only one vote per user per solution
        vote, created = SuggestedSolutionVote.objects.get_or_create(
            solution=solution, user=self.request.user,
            defaults={"vote_type": self.request.data.get("vote_type")}
        )
        if not created:
            # If vote already exists, update its type
            vote.vote_type = self.request.data.get("vote_type")
            vote.save()
            serializer.instance = vote
        else:
            serializer.save(user=self.request.user, solution=solution)

    def get_queryset(self):
        queryset = super().get_queryset()
        solution_id = self.request.query_params.get("solution")
        if solution_id:
            queryset = queryset.filter(solution_id=solution_id)
        return queryset


class SolutionCommentViewSet(viewsets.ModelViewSet):
    queryset = SolutionComment.objects.all()
    serializer_class = SolutionCommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        solution_id = self.request.data.get("solution")
        solution = get_object_or_404(SuggestedSolution, pk=solution_id)
        parent_id = self.request.data.get("parent")
        parent = None
        if parent_id:
            parent = get_object_or_404(SolutionComment, pk=parent_id)
        serializer.save(user=self.request.user, solution=solution, parent=parent)

    def get_queryset(self):
        queryset = super().get_queryset()
        solution_id = self.request.query_params.get("solution")
        if solution_id:
            queryset = queryset.filter(solution_id=solution_id, parent__isnull=True)
        else:
            queryset = queryset.filter(parent__isnull=True)
        return queryset

    def perform_update(self, serializer):
        comment = self.get_object()
        if comment.user != self.request.user:
            raise PermissionDenied("You can only edit your own comments.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            raise PermissionDenied("You can only delete your own comments.")
        instance.delete()
