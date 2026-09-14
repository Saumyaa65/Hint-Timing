"""
Research Assessment Baseline Configuration.

Contains initial operational thresholds selected for baseline prototype experimentation.
These thresholds are provisional parameters for operationalizing the research baseline and
do NOT represent scientifically validated or hardcoded ground truth.
"""

RULE_CONFIG_VERSION = "TASK_2B_RULE_V1"

BASELINE_CONFIG = {
    # Minimum trajectory length required before attempting a directional assessment
    'MIN_TRAJECTORY_LENGTH': 2,

    # Threshold for considering pass rate change as meaningful improvement (0.0 to 1.0)
    'MEANINGFUL_PASS_RATE_IMPROVEMENT': 0.15,

    # Threshold for considering test pass count change as meaningful improvement
    'MEANINGFUL_TESTS_IMPROVEMENT': 1,

    # Threshold of consecutive stagnant transitions to trigger stagnation signal
    'STAGNATION_THRESHOLD': 2,
    
    # High stagnation threshold
    'HIGH_STAGNATION_THRESHOLD': 3,

    # Consecutive failure count threshold when accompanied by zero progress
    'CONSECUTIVE_FAILURES_THRESHOLD': 3,

    # Minimum heuristic confidence required to assert PRODUCTIVE or UNPRODUCTIVE state
    'MIN_CONFIDENCE_THRESHOLD': 0.40,

    # High heuristic confidence threshold
    'HIGH_CONFIDENCE_THRESHOLD': 0.75,
}

HYBRID_CONFIG = {
    'VERSION': '2E_HYBRID_PROVISIONAL_V1',
    'PROMPT_VERSION': 'TASK_2C_SYSTEM_V1',
    'CONSENSUS_BOOST': 0.15,
    'CONFLICT_PENALTY': 0.30,
    'DEFAULT_UNCERTAIN_CONFIDENCE': 0.50,
    'HIGH_CONFIDENCE_THRESHOLD': 0.80,
    'MIN_CONFIDENCE_THRESHOLD': 0.40,
}

# Configurable user ID exclusions for fallback, manual test, and system admin accounts
RESEARCH_EXCLUDED_USER_IDS = {
    "1",          # Unauthenticated frontend fallback ID
    "123",        # Developer manual Postman/API test user
    "test_user",  # Synthetic test user
    "admin",      # System admin user
}

def is_research_valid_user(user_id: str) -> bool:
    """
    Returns True if user_id belongs to an authenticated candidate user,
    excluding unauthenticated fallback '1', dev test ID '123', synthetic test users,
    and user profiles marked with is_test_account=True.
    """
    if not user_id or str(user_id).strip() in RESEARCH_EXCLUDED_USER_IDS:
        return False

    try:
        from hints.models import UserProfile
        profile = UserProfile.objects.filter(clerk_id=str(user_id)).first()
        if profile and profile.is_test_account:
            return False
    except Exception:
        pass

    return True


def is_research_valid_session(session_or_id) -> bool:
    """
    Determines if a problem-solving session is eligible for research sampling.
    Can accept a session_id string or a list/queryset of Attempt objects.

    Eligibility criteria:
    1. Authenticated user (is_research_valid_user(user_id) is True, not in RESEARCH_EXCLUDED_USER_IDS, is_test_account=False).
    2. Valid, non-empty session_id.
    3. Genuine trajectory length t >= 2.
    4. Consistent non-empty language recorded across session attempts.
    5. Excludes starter-code-only / zero-code-modification sessions (must have >= 2 distinct code states).
    6. Excludes obvious testing / dummy artifact sessions (e.g. empty/dummy code).
    """
    from hints.models import Attempt
    from struggle_analysis.trajectory import normalize_code

    if isinstance(session_or_id, str):
        session_id = session_or_id.strip()
        if not session_id:
            return False
        attempts = list(Attempt.objects.filter(session_id=session_id).order_by('created_at', 'id'))
    elif isinstance(session_or_id, (list, tuple)):
        attempts = list(session_or_id)
    else:
        try:
            attempts = list(session_or_id)
        except Exception:
            return False

    if not attempts or len(attempts) < 2:
        return False

    # Check session_id validity across attempts
    first_session_id = getattr(attempts[0], 'session_id', None)
    if not first_session_id or not str(first_session_id).strip():
        return False

    for att in attempts:
        if getattr(att, 'session_id', None) != first_session_id:
            return False

    # Check user authenticity & test account exclusion
    user_id = getattr(attempts[0], 'user_id', None)
    if not is_research_valid_user(user_id):
        return False

    for att in attempts:
        if getattr(att, 'user_id', None) != user_id:
            return False

    # 3. Check language consistency
    # Code execution attempts (RUN / SUBMIT) must have a single consistent non-empty language
    code_languages = {getattr(att, 'language', '').strip().lower() for att in attempts if getattr(att, 'language', None) and getattr(att, 'source', None) in {'RUN', 'SUBMIT'}}
    all_languages = {getattr(att, 'language', '').strip().lower() for att in attempts if getattr(att, 'language', None)}

    if code_languages:
        if len(code_languages) != 1 or '' in code_languages:
            return False
    else:
        if len(all_languages) != 1 or '' in all_languages:
            return False

    # Check code evolution (exclude starter-code-only / zero code modification sessions)
    normalized_codes = [normalize_code(getattr(att, 'code', '')) for att in attempts]

    # Exclude dummy/test codes
    if all(not c or c.strip() in {'test', 'asdf', 'foo', 'bar'} for c in normalized_codes):
        return False

    # Must contain code edits (at least 2 distinct normalized code snapshots)
    unique_codes = set(normalized_codes)
    if len(unique_codes) < 2:
        return False

    return True


