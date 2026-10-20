from django.utils import timezone
from hints.models import UserProgress, Attempt
from .models import TrajectoryFeature
from .trajectory import extract_attempt_info, compute_transition, normalize_code, normalize_error

def record_attempt(attempt):
    """Update UserProgress with latest activity and attempt count derived from ordering."""
    progress, _ = UserProgress.objects.get_or_create(user_id=attempt.user_id, problem=attempt.problem)
    progress.last_activity = timezone.now()
    progress.attempts_count = Attempt.objects.filter(user_id=attempt.user_id, problem=attempt.problem).count()
    progress.failed_attempts_count = Attempt.objects.filter(user_id=attempt.user_id, problem=attempt.problem, status='failed').count()
    progress.save()
    return progress

def extract_features(prev_attempt, curr_attempt):
    """Compute trajectory features between two consecutive attempts and persist them."""
    attempt_number = Attempt.objects.filter(
        user_id=curr_attempt.user_id,
        problem=curr_attempt.problem,
        created_at__lte=curr_attempt.created_at
    ).count()

    prev_info = extract_attempt_info(prev_attempt, max(1, attempt_number - 1))
    curr_info = extract_attempt_info(curr_attempt, attempt_number)

    prior_attempts = Attempt.objects.filter(
        user_id=curr_attempt.user_id,
        problem=curr_attempt.problem,
        created_at__lt=prev_attempt.created_at
    ).order_by('created_at')

    first_dt = None
    prev_transitions = []
    if prior_attempts.exists():
        att_list = [extract_attempt_info(a, idx) for idx, a in enumerate(prior_attempts, start=1)]
        first_dt = att_list[0]["created_at_dt"]
        att_list.append(prev_info)
        for i in range(1, len(att_list)):
            t = compute_transition(att_list[i-1], att_list[i], prev_transitions, first_dt=first_dt)
            prev_transitions.append(t)
    elif prev_info.get("created_at_dt"):
        first_dt = prev_info["created_at_dt"]

    transition = compute_transition(prev_info, curr_info, prev_transitions, first_dt=first_dt)

    tf = TrajectoryFeature.objects.create(
        previous_attempt=prev_attempt,
        current_attempt=curr_attempt,
        time_delta=transition["temporal"]["time_delta"],
        code_similarity=transition["code_evolution"]["code_similarity"],
        code_change_ratio=transition["code_evolution"]["code_change_ratio"],
        code_change_magnitude=transition["code_evolution"]["code_change_magnitude"],
        repeated_code=transition["code_evolution"]["repeated_code"],
        repeated_error=transition["error_evolution"]["repeated_error"],
        error_similarity=transition["error_evolution"]["error_similarity"],
        error_changed=transition["error_evolution"]["error_changed"],
        error_resolved=transition["error_evolution"]["error_resolved"],
        error_introduced=transition["error_evolution"]["error_introduced"],
        tests_passed_previous=transition["performance"]["tests_passed_prev"],
        tests_passed_current=transition["performance"]["tests_passed_curr"],
        test_improvement=transition["performance"]["delta_tests_passed"],
        tests_pass_ratio_previous=transition["performance"]["pass_rate_prev"],
        tests_pass_ratio_current=transition["performance"]["pass_rate_curr"],
        performance_trend=transition["performance"]["performance_trend"],
        is_approach_change=transition["exploration"]["is_approach_change"],
        exploration_score=transition["exploration"]["exploration_score"],
        repeated_test_outcome=transition["repetition"]["repeated_test_outcome"],
        repeated_state=transition["repetition"]["repeated_state"],
        interaction_type=transition["repetition"]["interaction_type"],
        stagnation_length=transition["repetition"]["stagnation_length"],
        attempt_number=attempt_number,
        consecutive_failure_count=transition["temporal"]["consecutive_failed_attempts"],
        feature_data=transition,
    )
    return tf

def handle_attempt(attempt):
    """Public entry point: record progress and extract features."""
    record_attempt(attempt)
    previous = (
        Attempt.objects.filter(user_id=attempt.user_id, problem=attempt.problem)
        .exclude(id=attempt.id)
        .order_by('-created_at')
        .first()
    )
    if previous:
        extract_features(previous, attempt)
