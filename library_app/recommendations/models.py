from django.db import models

from account.models import CustomUser
from library_app.models import Book



# Model for storing book recommendations for user
class BookRecommendation(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="book_recommendations",
        help_text="The user for whom these recommendations are generated"
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="recommended_to_users",
        help_text="The recommended book"
    )
    score = models.FloatField(default=0.0, help_text="A score/ranking for the recommendation (higher is more strongly recommended)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')
        ordering = ['-score', '-created_at']

    def __str__(self):
        return f"Recommendation for {self.user.get_full_name() or self.user.username}: {self.book.title} ({self.score})"