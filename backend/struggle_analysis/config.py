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
