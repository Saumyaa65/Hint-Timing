from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Friendship, ForumPost, ForumComment, SolutionShare, UserProfile, Problem
from .serializers import ForumPostSerializer, ForumCommentSerializer, SolutionShareSerializer
from django.db.models import Count, F

class LeaderboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def global_rankings(self, request):
        profiles = UserProfile.objects.select_related('user').order_by('-total_score')[:100]
        data = [
            {
                "username": p.user.username,
                "clerk_id": p.clerk_id,
                "score": p.total_score,
                "current_streak": p.current_streak,
                "rank": idx + 1
            }
            for idx, p in enumerate(profiles)
        ]
        return Response(data)


class ForumPostViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ForumPostSerializer

    def get_queryset(self):
        qs = ForumPost.objects.select_related('user', 'problem').prefetch_related(
            'comments__user'
        ).order_by('-created_at')
        problem_id = self.request.query_params.get('problem_id')
        if problem_id:
            qs = qs.filter(problem_id=problem_id)
        return qs

    def perform_create(self, serializer):
        # Allow optional problem_id from request
        problem_id = self.request.data.get('problem_id')
        problem = None
        if problem_id:
            try:
                problem = Problem.objects.get(pk=problem_id)
            except Problem.DoesNotExist:
                pass
        serializer.save(user=self.request.user, problem=problem)

    @action(detail=True, methods=['post'])
    def upvote(self, request, pk=None):
        post = self.get_object()
        ForumPost.objects.filter(pk=post.pk).update(upvotes=F('upvotes') + 1)
        post.refresh_from_db()
        return Response({"status": "upvoted", "upvotes": post.upvotes})

    @action(detail=True, methods=['post'])
    def comment(self, request, pk=None):
        post = self.get_object()
        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)
        comment = ForumComment.objects.create(
            post=post,
            user=request.user,
            content=content
        )
        serializer = ForumCommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SolutionShareViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SolutionShareSerializer

    def get_queryset(self):
        qs = SolutionShare.objects.select_related('user', 'problem', 'attempt').order_by('-created_at')
        problem_id = self.request.query_params.get('problem_id')
        if problem_id:
            qs = qs.filter(problem_id=problem_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def upvote(self, request, pk=None):
        solution = self.get_object()
        SolutionShare.objects.filter(pk=solution.pk).update(upvotes=F('upvotes') + 1)
        solution.refresh_from_db()
        return Response({"status": "upvoted", "upvotes": solution.upvotes})
