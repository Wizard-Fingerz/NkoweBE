from django.db import models
from django.conf import settings

from exam_app.models import Question

class SuggestedSolution(models.Model):
    """
    Model allowing users to suggest solutions (with file upload) to a particular Question.
    Supports interactive discussion and voting.
    """
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="suggested_solutions"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="suggested_solutions"
    )
    content = models.TextField()
    file = models.FileField(upload_to="suggested_solutions/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # For extensibility: status field if later moderation is needed
    is_active = models.BooleanField(default=True)

    def total_votes(self):
        # Returns the net vote count (upvotes - downvotes)
        up = self.votes.filter(vote_type=SuggestedSolutionVote.UPVOTE).count()
        down = self.votes.filter(vote_type=SuggestedSolutionVote.DOWNVOTE).count()
        return up - down

    def __str__(self):
        return f"Solution by {self.user.username} for Q: {self.question.id}"

class SuggestedSolutionVote(models.Model):
    """
    Model for voting up or down a suggested solution.
    """
    UPVOTE = 1
    DOWNVOTE = -1
    VOTE_TYPE_CHOICES = (
        (UPVOTE, "Upvote"),
        (DOWNVOTE, "Downvote"),
    )
    solution = models.ForeignKey(
        SuggestedSolution,
        on_delete=models.CASCADE,
        related_name="votes"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="solution_votes"
    )
    vote_type = models.SmallIntegerField(choices=VOTE_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('solution', 'user')  # Only one vote per user per solution

    def __str__(self):
        return f"{self.get_vote_type_display()} by {self.user.username} on solution {self.solution.id}"

class SolutionComment(models.Model):
    """
    Interactive thread/comments for a suggested solution.
    Supports nesting (replies) via self-referential foreign key.
    """
    solution = models.ForeignKey(
        SuggestedSolution,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="solution_comments"
    )
    content = models.TextField()
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='replies'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.user.username} on solution {self.solution.id}"
