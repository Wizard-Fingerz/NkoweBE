from django.db.models import Q
from library_app.models import Book
from library_app.recommendations.models import BookRecommendation
from account.models import CustomUser

def create_and_get_book_recommendations_for_user(user, limit=10):
    """
    Automatically create book recommendations for a user if they do not already exist for today.
    Approach:
      - Prioritize books in the same genre(s) as the user's recently interacted/recommended books.
      - Exclude books the user has already received as recommendations.
      - Fallback to popular (available) books if not enough genre matches.
      - Automatically create BookRecommendation entries.
    Returns a list of BookRecommendation objects newly created, or existing if already auto-generated for today.
    """
    from django.utils import timezone

    if not isinstance(user, CustomUser):
        return []

    today = timezone.now().date()

    # Check if auto-generated recommendations for today already exist
    todays_recos = BookRecommendation.objects.filter(
        user=user,
        created_at__date=today
    ).order_by('-score')

    if todays_recos.count() >= limit:
        return list(todays_recos[:limit])

    # Get book ids already recommended to this user (all time)
    already_recommended_ids = set(
        BookRecommendation.objects.filter(user=user).values_list('book_id', flat=True)
    )

    # Try to find genres the user likes (from past recommendations)
    recent_recos = BookRecommendation.objects.filter(user=user).order_by('-created_at')[:10]
    genre_ids = set()
    for br in recent_recos:
        genre_ids.update(br.book.genre.values_list('id', flat=True))
    genre_ids = list(genre_ids)

    recommendations = []
    book_candidates = []

    # 1. Recommend available books in user's favorite genres the user hasn't been recommended yet
    if genre_ids:
        genre_books = Book.objects.filter(
            genre__id__in=genre_ids,
            available_copies__gt=0
        ).exclude(
            id__in=already_recommended_ids
        ).distinct().order_by('-available_copies')[:limit]
        book_candidates.extend(list(genre_books))

    # 2. Fallback: Recommend the most available books user hasn't seen
    if len(book_candidates) < limit:
        fallback_books = Book.objects.filter(
            available_copies__gt=0
        ).exclude(
            id__in=already_recommended_ids | set(b.id for b in book_candidates)
        ).distinct().order_by('-available_copies')[: (limit - len(book_candidates))]
        book_candidates.extend(list(fallback_books))

    # Create BookRecommendation objects if not already created today for these books
    for idx, book in enumerate(book_candidates[:limit]):
        rec, created = BookRecommendation.objects.get_or_create(
            user=user,
            book=book,
            defaults={'score': 100 - idx}  # Simple scoring: top = 100, descending
        )
        # Only count recommendations created today (or just now)
        if rec.created_at.date() == today or created:
            recommendations.append(rec)

    return recommendations
