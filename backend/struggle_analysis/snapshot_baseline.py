"""
Snapshot Baseline Struggle Classifier (Condition M1)

Evaluates strictly the latest attempt A_t at step t.
Guarantees ZERO access to prior attempts A_1 ... A_{t-1}.

Demonstrates the pedagogical limitation of snapshot-only reasoning:
without historical evolution, single-attempt analysis is inherently conservative.
"""

from typing import Dict, Any

def assess_snapshot_trajectory(trajectory_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates strictly attempt A_t from a trajectory prefix.
    """
    attempts = trajectory_data.get("attempts", [])
    if not attempts:
        return {
            "method": "Snapshot Baseline",
            "assessment_attempt": 0,
            "state": "UNCERTAIN",
            "confidence": 0.0,
            "evidence": {
                "positive_signals": [],
                "negative_signals": [],
                "uncertainty_signals": ["NO_ATTEMPTS_RECORDED"]
            },
            "reasoning": "No attempts present in trajectory payload."
        }

    # Extract strictly latest attempt A_t at step t
    latest_attempt = attempts[-1]
    t = latest_attempt.get("index", len(attempts))
    status = latest_attempt.get("status", "").upper()
    pass_rate = float(latest_attempt.get("pass_rate", 0.0))
    passed = latest_attempt.get("tests_passed", 0)
    total = latest_attempt.get("total_tests", 0)
    err = latest_attempt.get("error_message", "")
    code = latest_attempt.get("code", "")

    positive_signals = []
    negative_signals = []
    uncertainty_signals = []

    if pass_rate >= 1.0 or status == "ACCEPTED":
        state = "PRODUCTIVE"
        confidence = 0.90
        positive_signals.append("SNAPSHOT_ALL_TESTS_PASSED")
        reasoning = f"Latest attempt #{t} passed all tests ({passed}/{total}). Assessed as PRODUCTIVE struggle (solved)."
    elif pass_rate > 0.0:
        state = "UNCERTAIN"
        confidence = 0.50
        positive_signals.append("SNAPSHOT_PARTIAL_TESTS_PASSED")
        uncertainty_signals.append("SNAPSHOT_NO_HISTORICAL_TREND")
        reasoning = f"Latest attempt #{t} passed partial tests ({passed}/{total}, {round(pass_rate*100, 1)}%). Single snapshot lacks temporal context to verify progression trend."
    else:
        if len(code.strip()) < 15:
            state = "UNPRODUCTIVE"
            confidence = 0.70
            negative_signals.append("SNAPSHOT_TRIVIAL_EMPTY_CODE")
            reasoning = f"Latest attempt #{t} contains empty or trivial code with zero test passes."
        else:
            state = "UNCERTAIN"
            confidence = 0.50
            if err:
                negative_signals.append("SNAPSHOT_EXECUTION_ERROR")
            else:
                negative_signals.append("SNAPSHOT_ZERO_TESTS_PASSED")
            uncertainty_signals.append("SNAPSHOT_NO_HISTORICAL_TREND")
            reasoning = f"Latest attempt #{t} failed all tests or errored. Single snapshot cannot distinguish between initial attempt, active exploration, or repeated stagnation."

    return {
        "method": "Snapshot Baseline",
        "assessment_attempt": t,
        "state": state,
        "confidence": confidence,
        "evidence": {
            "positive_signals": positive_signals,
            "negative_signals": negative_signals,
            "uncertainty_signals": uncertainty_signals
        },
        "reasoning": reasoning
    }
