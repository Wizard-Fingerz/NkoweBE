from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from library_app.recommendations.models import BookRecommendation
from library_app.recommendations.serializers import BookRecommendationSerializer
from library_app.recommendations.recommender import create_and_get_book_recommendations_for_user

class BookRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing book recommendations for a user.
    - GET /recommendations/bookrecommendations/ : List recommendations for current user (auto-generate if needed)
    """
    serializer_class = BookRecommendationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only recommendations belonging to current user
        return BookRecommendation.objects.filter(user=self.request.user).order_by('-created_at', '-score')
    
    def list(self, request, *args, **kwargs):
        """
        List recommendations for current user.
        Auto-generate recommendations for today if not already generated.
        """
        user = request.user
        # Limit can be provided in query param, default 10
        limit = request.query_params.get('limit')
        try:
            limit = int(limit) if limit is not None else 10
        except ValueError:
            limit = 10

        recommendations = create_and_get_book_recommendations_for_user(user, limit=limit)
        page = self.paginate_queryset(recommendations)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(recommendations, many=True)
        return Response(serializer.data)
