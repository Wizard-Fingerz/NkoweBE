from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from .models import SuggestedSolution, SuggestedSolutionVote, SolutionComment
from .serializers import SuggestedSolutionSerializer, SuggestedSolutionVoteSerializer, SolutionCommentSerializer

class SuggestedSolutionViewSet(viewsets.ModelViewSet):
    queryset = SuggestedSolution.objects.all()
    serializer_class = SuggestedSolutionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        queryset = super().get_queryset()
        question_id = self.request.query_params.get("question")
        if question_id:
            queryset = queryset.filter(question_id=question_id)
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
