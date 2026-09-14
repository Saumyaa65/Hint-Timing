from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import DailyProblem
from .serializers import DailyProblemSerializer

class DailyProblemViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'])
    def today(self, request):
        """
        Get the problem of the day for the current date.
        """
        today = timezone.now().date()
        daily_problem = DailyProblem.objects.filter(date=today).first()
        
        if not daily_problem:
            return Response({"error": "No problem of the day found for today."}, status=404)
            
        serializer = DailyProblemSerializer(daily_problem)
        return Response(serializer.data)
