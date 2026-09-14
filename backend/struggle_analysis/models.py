from django.db import models
from hints.models import Attempt

class TrajectoryFeature(models.Model):
    previous_attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name='next_features')
    current_attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name='prev_features')
    time_delta = models.FloatField(help_text='Seconds between attempts')
    code_similarity = models.FloatField(help_text='0-1 similarity')
    code_change_ratio = models.FloatField(help_text='1 - code_similarity')
    code_change_magnitude = models.CharField(max_length=50, default='none')
    repeated_code = models.BooleanField()
    repeated_error = models.BooleanField()
    error_similarity = models.FloatField(default=0.0)
    error_changed = models.BooleanField()
    error_resolved = models.BooleanField(default=False)
    error_introduced = models.BooleanField(default=False)
    tests_passed_previous = models.IntegerField(null=True, blank=True)
    tests_passed_current = models.IntegerField(null=True, blank=True)
    test_improvement = models.IntegerField(null=True, blank=True)
    tests_pass_ratio_previous = models.FloatField(null=True, blank=True)
    tests_pass_ratio_current = models.FloatField(null=True, blank=True)
    performance_trend = models.CharField(max_length=20, default='unchanged')
    is_approach_change = models.BooleanField(default=False)
    exploration_score = models.FloatField(default=0.0)
    repeated_test_outcome = models.BooleanField(default=False)
    repeated_state = models.BooleanField(default=False)
    interaction_type = models.CharField(max_length=30, default='CODE_CHANGE')
    stagnation_length = models.IntegerField(default=0)
    attempt_number = models.IntegerField(help_text='Ordinal of current attempt for this user/problem')
    consecutive_failure_count = models.IntegerField(help_text='Number of failures in a row up to this attempt')
    feature_data = models.JSONField(null=True, blank=True, help_text='Complete structured feature transition payload')
    created_at = models.DateTimeField(auto_now_add=True)

    def as_dict(self):
        if self.feature_data:
            return self.feature_data
        return {
            'previous_attempt_id': self.previous_attempt_id,
            'current_attempt_id': self.current_attempt_id,
            'time_delta': self.time_delta,
            'code_similarity': self.code_similarity,
            'code_change_ratio': self.code_change_ratio,
            'code_change_magnitude': self.code_change_magnitude,
            'repeated_code': self.repeated_code,
            'repeated_error': self.repeated_error,
            'error_similarity': self.error_similarity,
            'error_changed': self.error_changed,
            'error_resolved': self.error_resolved,
            'error_introduced': self.error_introduced,
            'tests_passed_previous': self.tests_passed_previous,
            'tests_passed_current': self.tests_passed_current,
            'test_improvement': self.test_improvement,
            'tests_pass_ratio_previous': self.tests_pass_ratio_previous,
            'tests_pass_ratio_current': self.tests_pass_ratio_current,
            'performance_trend': self.performance_trend,
            'is_approach_change': self.is_approach_change,
            'exploration_score': self.exploration_score,
            'repeated_test_outcome': self.repeated_test_outcome,
            'repeated_state': self.repeated_state,
            'interaction_type': self.interaction_type,
            'stagnation_length': self.stagnation_length,
            'attempt_number': self.attempt_number,
            'consecutive_failure_count': self.consecutive_failure_count,
        }
