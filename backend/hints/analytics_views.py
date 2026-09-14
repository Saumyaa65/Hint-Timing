from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, F, Q
from django.contrib.auth.models import User
from .models import Problem, Attempt, UserProgress, HintDelivery, UserProfile
import datetime

class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def admin_dashboard(self, request):
        total_users = User.objects.count()
        total_problems = Problem.objects.count()
        total_attempts = Attempt.objects.count()

        # Most popular problems (by total attempts)
        popular_problems = Problem.objects.annotate(
            attempt_count=Count('attempts'),
            success_count=Count('attempts', filter=Q(attempts__status='passed'))
        ).order_by('-attempt_count')[:10]

        # Calculate global solve rate (use 'success' OR 'passed' for compatibility)
        successful_attempts = Attempt.objects.filter(
            Q(status='passed') | Q(status='success')
        ).count()
        solve_rate = (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0

        # Per-problem solve rates for top problems
        per_problem_stats = []
        for p in popular_problems:
            total = p.attempt_count or 0
            success = p.success_count or 0
            rate = round((success / total * 100), 1) if total > 0 else 0
            per_problem_stats.append({
                "id": p.problem_id,
                "title": p.title,
                "difficulty": p.difficulty,
                "topic": p.topic,
                "attempts": total,
                "solved": success,
                "solve_rate": rate,
            })

        data = {
            "total_users": total_users,
            "total_problems": total_problems,
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "global_solve_rate": round(solve_rate, 2),
            "popular_problems": per_problem_stats,
        }
        return Response(data)

    @action(detail=False, methods=['get'])
    def user_dashboard(self, request):
        user = request.user

        # User specific stats
        total_attempts = Attempt.objects.filter(user_id=user.id).count()
        successful_attempts = Attempt.objects.filter(
            user_id=user.id
        ).filter(Q(status='passed') | Q(status='success')).count()
        solve_rate = (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0

        # Topic mastery based on successful attempts
        successful_problems = Attempt.objects.filter(
            user_id=user.id
        ).filter(Q(status='passed') | Q(status='success')).values('problem__topic').annotate(
            problems_solved=Count('problem', distinct=True)
        )

        topic_stats = []
        for stats in successful_problems:
            topic = stats['problem__topic'] or 'General'
            solved = stats['problems_solved']
            mastery_level = min(solved / 5.0, 1.0)
            topic_stats.append({
                "topic": topic,
                "mastery_level": mastery_level,
                "problems_solved": solved
            })

        # Hints used
        hints_used = HintDelivery.objects.filter(user_id=user.id).count()

        # Streak info
        profile = UserProfile.objects.filter(user_id=user.id).first()
        current_streak = profile.current_streak if profile else 0
        longest_streak = profile.longest_streak if profile else 0
        total_score = profile.total_score if profile else 0

        # Recent activity: last 90 days of solve dates (for heatmap)
        cutoff = datetime.date.today() - datetime.timedelta(days=90)
        recent_solves = Attempt.objects.filter(
            user_id=user.id,
            created_at__date__gte=cutoff
        ).filter(Q(status='passed') | Q(status='success')).values('created_at__date').annotate(
            count=Count('id')
        ).order_by('created_at__date')

        activity = {
            str(item['created_at__date']): item['count']
            for item in recent_solves
        }

        data = {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "solve_rate": round(solve_rate, 2),
            "hints_used": hints_used,
            "topic_stats": topic_stats,
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "total_score": total_score,
            "recent_activity": activity,
        }
        return Response(data)
