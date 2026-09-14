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

# Configurable user ID exclusions for fallback and test accounts
RESEARCH_EXCLUDED_USER_IDS = {
    "1",                                 # Unauthenticated frontend fallback ID
    "123",                               # Developer manual Postman/API test user
    "test_user",                         # Synthetic test user
    "admin",                             # System admin user
}

def is_research_valid_user(user_id: str) -> bool:
    """
    Returns True if user_id belongs to an authenticated candidate user,
    excluding unauthenticated fallback '1', dev test account '123', synthetic test users,
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


def is_research_valid_session(session_id: str) -> bool:
    """
    Returns True if session_id represents a valid research session:
    - Session ID is non-null and non-empty
    - Belongs to an authenticated non-excluded research user (is_research_valid_user)
    - Profile is_test_account is False
    - Session has at least MIN_TRAJECTORY_LENGTH attempts (t >= 2)
    - All attempts in the session belong to the same user and problem
    - Programming language is consistent across code execution attempts
    - Excludes starter-code-only or duplicate-artifact sessions (code evolves across attempts)
    """
    if not session_id or not str(session_id).strip():
        return False

    from hints.models import Attempt
    atts = list(Attempt.objects.filter(session_id=str(session_id).strip()).order_by('created_at', 'id'))
    if len(atts) < BASELINE_CONFIG.get('MIN_TRAJECTORY_LENGTH', 2):
        return False

    first_user = atts[0].user_id
    if not is_research_valid_user(first_user):
        return False

    # Ensure user and problem isolation across the session
    first_problem_id = atts[0].problem_id
    if any(a.user_id != first_user or a.problem_id != first_problem_id for a in atts):
        return False

    # Language consistency across code-executing attempts (RUN / SUBMIT) or non-empty code attempts
    code_langs = set(a.language for a in atts if a.source in ('RUN', 'SUBMIT') and a.language)
    if not code_langs:
        code_langs = set(a.language for a in atts if a.language)
    if len(code_langs) > 1:
        return False

    # Starter-code-only / duplicate-artifact exclusion: requires > 1 distinct non-empty code version
    distinct_codes = set((a.code or '').strip() for a in atts if (a.code or '').strip())
    if len(distinct_codes) <= 1:
        return False

    return True


