from django.shortcuts import render
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
import logging
import json

from .models import Problem
from .serializers import ProblemSerializer, ProblemDetailSerializer

logger = logging.getLogger(__name__)

class ProblemViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for retrieving problem information.
    """
    queryset = Problem.objects.all()
    serializer_class = ProblemSerializer
    
    def get_queryset(self):
        """
        Filter problems based on query parameters.
        """
        queryset = Problem.objects.all().order_by('id')
        
        # Apply filters if they exist in the request
        topic = self.request.query_params.get('topic', None)
        difficulty = self.request.query_params.get('difficulty', None)
        search = self.request.query_params.get('search', None)
        
        if topic:
            queryset = queryset.filter(topic=topic)
        
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
            
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        return queryset
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'retrieve':
            return ProblemDetailSerializer
        return ProblemSerializer

    def list(self, request, *args, **kwargs):
        """
        List problems with caching (5 minutes).
        Cache key is built from query parameters.
        """
        topic = request.query_params.get('topic', '')
        difficulty = request.query_params.get('difficulty', '')
        search = request.query_params.get('search', '')
        cache_key = f'problems_list:topic={topic}:difficulty={difficulty}:search={search}'

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=300)  # 5 minutes
        return response

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single problem with caching (30 minutes).
        """
        problem_id = kwargs.get('pk')
        cache_key = f'problem_detail:{problem_id}'

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=1800)  # 30 minutes
        return response

    @action(detail=False, methods=['get'])
    def topics(self, request):
        """
        Get all available topics with caching (10 minutes).
        """
        cache_key = 'problem_topics'

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        # Group by topic and count problems
        topics = Problem.objects.values('topic').annotate(count=Count('id')).order_by('topic')

        data = [
            {
                'name': topic['topic'],
                'count': topic['count']
            }
            for topic in topics if topic['topic']
        ]
        cache.set(cache_key, data, timeout=600)  # 10 minutes
        return Response(data)