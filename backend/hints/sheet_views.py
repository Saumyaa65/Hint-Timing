from rest_framework import viewsets, permissions
from .models import ProblemSheet
from .serializers import ProblemSheetSerializer

class ProblemSheetViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for retrieving problem sheets.
    For now, users can only read sheets, not create them.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = ProblemSheet.objects.filter(is_public=True).prefetch_related('sheet_problems__problem').order_by('-created_at')
    serializer_class = ProblemSheetSerializer
