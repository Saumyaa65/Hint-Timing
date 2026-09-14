from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    clerk_id = models.CharField(max_length=255, unique=True)
    bio = models.TextField(blank=True, null=True)
    total_score = models.IntegerField(default=0)
    global_rank = models.IntegerField(null=True, blank=True)
    
    # Streak tracking
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_potd_attempt_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.username}"

class ProblemSheet(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_sheets')
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class SheetProblem(models.Model):
    sheet = models.ForeignKey(ProblemSheet, on_delete=models.CASCADE, related_name='sheet_problems')
    problem = models.ForeignKey('Problem', on_delete=models.CASCADE, related_name='in_sheets')
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        unique_together = ('sheet', 'problem')

    def __str__(self):
        return f"{self.problem.title} in {self.sheet.title}"

class DailyProblem(models.Model):
    date = models.DateField(unique=True)
    problem = models.ForeignKey('Problem', on_delete=models.CASCADE, related_name='daily_appearances')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"POTD for {self.date}: {self.problem.title}"

class Problem(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ]
    
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    problem_id = models.CharField(max_length=255, unique=True, null=True, blank=True)  # User-provided problem ID
    description = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    topic = models.CharField(max_length=100, default='General', blank=True)  # Added topic field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id}: {self.title}"

class UserProgress(models.Model):
    user_id = models.CharField(max_length=255)  # Clerk user ID (e.g. user_3FAzV5...)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='user_progress')
    last_activity = models.DateTimeField(auto_now=True)
    attempts_count = models.IntegerField(default=0)
    failed_attempts_count = models.IntegerField(default=0)
    current_hint_level = models.IntegerField(default=1)
    hints_requested = models.IntegerField(default=0)

    def is_stuck(self):
        """Check if user is stuck based on inactivity and failed attempts"""
        time_threshold = timedelta(minutes=5)
        return (
            timezone.now() - self.last_activity > time_threshold and
            self.failed_attempts_count >= 3
        )

    def __str__(self):
        return f"Progress for user {self.user_id} on {self.problem.title}"

class Attempt(models.Model):
    user_id = models.CharField(max_length=255, default='')  # Clerk user ID
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='attempts')
    code = models.TextField()
    language = models.CharField(max_length=50, default='javascript')
    status = models.CharField(max_length=20, default='pending')
    execution_time = models.CharField(max_length=50, null=True, blank=True)
    evaluation_details = models.JSONField(null=True, blank=True)  # Added field for storing evaluation details
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Attempt by user {self.user_id} on {self.problem.title}"

class Hint(models.Model):
    HINT_TYPES = [
        ('conceptual', 'Conceptual'),
        ('approach', 'Approach'),
        ('implementation', 'Implementation'),
        ('debug', 'Debug')
    ]

    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='hints')
    content = models.TextField()
    level = models.IntegerField(default=1)
    hint_type = models.CharField(max_length=20, choices=HINT_TYPES, default='conceptual')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Hint {self.level} for {self.problem.title}"

class HintDelivery(models.Model):
    hint = models.ForeignKey(Hint, on_delete=models.CASCADE, related_name='deliveries')
    user_id = models.CharField(max_length=255, default='')  # Clerk user ID
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name='hint_deliveries')
    is_auto_triggered = models.BooleanField(default=False)
    feedback = models.TextField(null=True, blank=True)
    rating = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Hint delivery to user {self.user_id}"

class HintEvaluation(models.Model):
    hint = models.ForeignKey(Hint, on_delete=models.CASCADE, related_name='evaluations')
    safety_score = models.FloatField(default=0)
    helpfulness_score = models.FloatField(default=0)
    quality_score = models.FloatField(default=0)
    progress_alignment_score = models.FloatField(default=0)
    pedagogical_value_score = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Evaluation for hint {self.hint.id}"

# --- Social & Competitive Models ---

class Friendship(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

class ForumPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_posts')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='forum_posts', null=True, blank=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    upvotes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class ForumComment(models.Model):
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_comments')
    content = models.TextField()
    upvotes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class SolutionShare(models.Model):
    attempt = models.OneToOneField(Attempt, on_delete=models.CASCADE, related_name='shared_solution')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_solutions')
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='shared_solutions')
    title = models.CharField(max_length=255)
    explanation = models.TextField()
    upvotes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
