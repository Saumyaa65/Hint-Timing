from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
import logging
import json
import random

logger = logging.getLogger(__name__)

class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet for handling user authentication.
    This is a simplified mock implementation for demo purposes.
    """
    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register a new user"""
        name = request.data.get('name')
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not all([name, email, password]):
            return Response(
                {'error': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # In a real implementation, we would validate, hash the password, etc.
        # For now, just return a mock success
        
        # Generate a random user ID
        user_id = random.randint(1000, 9999)
        
        # Generate a mock token
        token = f"token_{random.randint(100000, 999999)}"
        
        return Response({
            'user': {
                'id': user_id,
                'name': name,
                'email': email
            },
            'token': token
        })
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """Log in a user"""
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not all([email, password]):
            return Response(
                {'error': 'Missing email or password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # In a real implementation, we would validate credentials
        # For now, just return a mock success
        
        # Generate a random user ID and name
        user_id = random.randint(1000, 9999)
        name = email.split('@')[0]  # Use part of email as name
        
        # Generate a mock token
        token = f"token_{random.randint(100000, 999999)}"
        
        return Response({
            'user': {
                'id': user_id,
                'name': name,
                'email': email
            },
            'token': token
        })
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """Log out a user"""
        # In a real implementation, we would invalidate the token
        # For now, just return a success message
        
        return Response({
            'message': 'Successfully logged out'
        })
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        # In a real implementation, we would get the user from the token
        # For now, return a mock error since we don't have a real auth system
        
        return Response(
            {'error': 'Not authenticated'},
            status=status.HTTP_401_UNAUTHORIZED
        )