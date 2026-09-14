import math
from .config import BASELINE_CONFIG, RULE_CONFIG_VERSION
from .trajectory import build_trajectory


def detect_productive_signals(trajectory_data: dict) -> list:
    """
    Detect active productive struggle evidence signals (P1..P5) from a trajectory prefix.
    """
    transitions = trajectory_data.get("transitions", [])
    summary = trajectory_data.get("trajectory_summary", {})

    signals = []
    if not transitions:
        return signals

    latest_trans = transitions[-1]
    latest_perf = latest_trans.get("performance", {})
    latest_err = latest_trans.get("error_evolution", {})
    latest_exp = latest_trans.get("exploration", {})
    latest_rep = latest_trans.get("repetition", {})

    # P1: PERFORMANCE_IMPROVEMENT
    delta_pass = latest_perf.get("delta_pass_rate", 0.0)
    delta_tests = latest_perf.get("delta_tests_passed", 0)
    if delta_pass >= BASELINE_CONFIG['MEANINGFUL_PASS_RATE_IMPROVEMENT'] or delta_tests >= BASELINE_CONFIG['MEANINGFUL_TESTS_IMPROVEMENT']:
        signals.append({
            "id": "P1_PERFORMANCE_IMPROVEMENT",
            "weight": 1.0,
            "description": f"Recent attempt improved performance (+{delta_tests} tests passed, +{round(delta_pass*100, 1)}% pass rate)."
        })

    # P2: ERROR_EVOLUTION
    if latest_err.get("error_resolved", False):
        signals.append({
            "id": "P2_ERROR_EVOLUTION",
            "weight": 0.8,
            "description": "Execution error was resolved in the latest attempt."
        })
    elif latest_err.get("error_changed", False) and summary.get("overall_test_improvement", 0) > 0:
        signals.append({
            "id": "P2_ERROR_EVOLUTION",
            "weight": 0.6,
            "description": "Error state changed accompanied by overall test progression."
        })

    # P3: EXPLORATION
    if latest_exp.get("is_approach_change", False):
        signals.append({
            "id": "P3_EXPLORATION",
            "weight": 0.6,
            "description": "Substantial code/approach modification detected indicating active solution exploration."
        })
    elif latest_exp.get("exploration_score", 0.0) > 0.40 and latest_perf.get("performance_trend") != "regressed":
        signals.append({
            "id": "P3_EXPLORATION",
            "weight": 0.4,
            "description": "Active code exploration observed without performance regression."
        })

    # P4: STAGNATION_ESCAPE
    prior_stagnation_existed = any(t.get("repetition", {}).get("stagnation_length", 0) >= 1 for t in transitions)
    current_improving_or_changed = (summary.get("peak_test_improvement", 0) > 0 or latest_perf.get("performance_trend") == "improved" or latest_rep.get("interaction_type") == "OUTCOME_CHANGE")

    if prior_stagnation_existed and current_improving_or_changed:
        signals.append({
            "id": "P4_STAGNATION_ESCAPE",
            "weight": 0.9,
            "description": "Successfully escaped prior stagnation loop into a new evaluation state or test improvement."
        })

    # P5: OVERALL_TRAJECTORY_PROGRESS
    overall_tests = summary.get("peak_test_improvement", 0)
    overall_pass_rate = summary.get("peak_pass_rate_improvement", 0.0)
    if overall_tests >= BASELINE_CONFIG['MEANINGFUL_TESTS_IMPROVEMENT'] or overall_pass_rate >= BASELINE_CONFIG['MEANINGFUL_PASS_RATE_IMPROVEMENT']:
        signals.append({
            "id": "P5_OVERALL_TRAJECTORY_PROGRESS",
            "weight": 0.9,
            "description": f"Cumulative trajectory prefix demonstrates net test progress (+{overall_tests} tests gained from initial attempt)."
        })

    return signals


def detect_unproductive_signals(trajectory_data: dict) -> list:
    """
    Detect active unproductive struggle evidence signals (U1..U6) from a trajectory prefix.
    """
    transitions = trajectory_data.get("transitions", [])
    summary = trajectory_data.get("trajectory_summary", {})

    signals = []
    if not transitions:
        return signals

    latest_trans = transitions[-1]
    latest_rep = latest_trans.get("repetition", {})
    latest_err = latest_trans.get("error_evolution", {})
    latest_temp = latest_trans.get("temporal", {})
    latest_perf = latest_trans.get("performance", {})

    # U1: REPEATED_EXECUTION
    if latest_rep.get("interaction_type") == "REPEAT_EXECUTION":
        signals.append({
            "id": "U1_REPEATED_EXECUTION",
            "weight": 0.7,
            "description": "Student re-executed identical code with no change in evaluation outcome."
        })

    # U2: REPEATED_ERROR
    if latest_err.get("repeated_error", False):
        signals.append({
            "id": "U2_REPEATED_ERROR",
            "weight": 0.8,
            "description": "Identical execution error encountered repeatedly without modification."
        })

    # U3: REPEATED_STATE
    if latest_rep.get("repeated_state", False):
        signals.append({
            "id": "U3_REPEATED_STATE",
            "weight": 0.9,
            "description": "Complete state (code, error, and test outcomes) remains stagnant."
        })

    # U4: PERFORMANCE_STAGNATION
    stagnation_len = latest_rep.get("stagnation_length", 0)
    if stagnation_len >= BASELINE_CONFIG['STAGNATION_THRESHOLD'] and summary.get("overall_test_improvement", 0) <= 0:
        weight = 1.0 if stagnation_len >= BASELINE_CONFIG['HIGH_STAGNATION_THRESHOLD'] else 0.7
        signals.append({
            "id": "U4_PERFORMANCE_STAGNATION",
            "weight": weight,
            "description": f"Sustained stagnation observed across {stagnation_len} consecutive attempts with zero test progress."
        })

    # U5: REPEATED_FAILED_ATTEMPTS
    consec_failures = latest_temp.get("consecutive_failed_attempts", 0)
    # Require evaluation test presence before flagging repeated failed attempts as unproductive
    has_eval_tests = any(a.get("total_tests", 0) > 0 for a in trajectory_data.get("attempts", []))

    if has_eval_tests and consec_failures >= BASELINE_CONFIG['CONSECUTIVE_FAILURES_THRESHOLD'] and summary.get("overall_test_improvement", 0) <= 0:
        signals.append({
            "id": "U5_REPEATED_FAILED_ATTEMPTS",
            "weight": 0.7,
            "description": f"{consec_failures} consecutive failing attempts recorded without test score improvement."
        })

    # U6: REVERSION_CYCLIC
    if latest_rep.get("reverts_to_prior_code", False) and latest_perf.get("performance_trend") != "improved":
        signals.append({
            "id": "U6_REVERSION_CYCLIC",
            "weight": 0.8,
            "description": "Reverted solution to an earlier attempted code state without achieving test progress."
        })

    return signals


def detect_uncertainty_signals(trajectory_data: dict, productive_signals: list, unproductive_signals: list) -> list:
    """
    Detect explicit uncertainty factors that prevent confident classification.
    """
    length = trajectory_data.get("trajectory_length", 0)
    attempts = trajectory_data.get("attempts", [])
    transitions = trajectory_data.get("transitions", [])
    signals = []

    if length < BASELINE_CONFIG['MIN_TRAJECTORY_LENGTH']:
        signals.append({
            "id": "UNCERTAIN_SHORT_TRAJECTORY",
            "description": "Trajectory prefix contains insufficient attempts (< 2) to observe a process trend."
        })

    if productive_signals and unproductive_signals:
        prod_weight = sum(s["weight"] for s in productive_signals)
        unprod_weight = sum(s["weight"] for s in unproductive_signals)
        if abs(prod_weight - unprod_weight) < 0.35:
            signals.append({
                "id": "UNCERTAIN_CONFLICTING_EVIDENCE",
                "description": "Trajectory exhibits strong conflicting evidence of both progress and stagnation."
            })

    # Code edits without evaluation test feedback
    has_no_eval_tests = attempts and all(a.get("total_tests", 0) == 0 for a in attempts)
    if has_no_eval_tests and length >= 2:
        signals.append({
            "id": "UNCERTAIN_NO_EVALUATION_FEEDBACK",
            "description": "Code was modified, but no test suite evaluation feedback is available for trajectory assessment."
        })

    return signals


def compute_heuristic_confidence(
    trajectory_length: int,
    state: str,
    prod_weight: float,
    unprod_weight: float,
    uncertainty_signals: list
) -> float:
    """
    Calculate evidence confidence (0.0 to 1.0) based on signal volume, strength ratio,
    trajectory length, and conflict penalty.
    """
    if state == "UNCERTAIN":
        if trajectory_length < 2:
            return 0.20
        return 0.35

    total_weight = prod_weight + unprod_weight
    if total_weight == 0.0:
        return 0.30

    if state == "PRODUCTIVE":
        net_margin = (prod_weight - unprod_weight) / total_weight
    else:
        net_margin = (unprod_weight - prod_weight) / total_weight

    length_factor = min(1.0, 0.5 + (trajectory_length * 0.1))
    penalty = 0.20 if uncertainty_signals else 0.0

    raw_conf = (0.5 * net_margin) + (0.5 * min(1.0, total_weight / 2.0))
    conf = max(0.30, min(0.95, (raw_conf * length_factor) - penalty))
    return round(conf, 2)


def generate_reasoning(
    state: str,
    confidence: float,
    attempt_index: int,
    productive_signals: list,
    unproductive_signals: list,
    uncertainty_signals: list
) -> str:
    """Generate clean natural language explanation for research inspection."""
    if state == "PRODUCTIVE":
        prod_desc = ", ".join(s["description"] for s in productive_signals)
        return f"Assessed as PRODUCTIVE struggle at attempt {attempt_index} (confidence: {confidence}). Primary evidence: {prod_desc}"
    elif state == "UNPRODUCTIVE":
        unprod_desc = ", ".join(s["description"] for s in unproductive_signals)
        return f"Assessed as UNPRODUCTIVE struggle at attempt {attempt_index} (confidence: {confidence}). Primary evidence: {unprod_desc}"
    else:
        reasons = [s["description"] for s in uncertainty_signals]
        if not reasons:
            reasons = ["Evidence signals are balanced or insufficient."]
        return f"Assessed as UNCERTAIN at attempt {attempt_index} (confidence: {confidence}). Factors: {' '.join(reasons)}"


def assess_trajectory(trajectory_data: dict) -> dict:
    """
    Core Research Entry Point:
    Assess a trajectory (or trajectory prefix) using the operational baseline methodology.
    
    Returns structured, explainable assessment dictionary.
    """
    attempts = trajectory_data.get("attempts", [])
    attempt_index = len(attempts)

    if attempt_index == 0:
        return {
            "state": "UNCERTAIN",
            "confidence": 0.0,
            "assessment_attempt": 0,
            "evidence": {
                "progression_weight": 0.0,
                "stagnation_weight": 0.0,
                "conflict_margin": 0.0
            },
            "positive_signals": [],
            "negative_signals": [],
            "uncertainty_signals": ["No attempt data available."],
            "reasoning": "No attempts recorded for this user/problem trajectory.",
        }

    productive_signals = detect_productive_signals(trajectory_data)
    unproductive_signals = detect_unproductive_signals(trajectory_data)
    uncertainty_signals = detect_uncertainty_signals(trajectory_data, productive_signals, unproductive_signals)

    prod_weight = sum(s["weight"] for s in productive_signals)
    unprod_weight = sum(s["weight"] for s in unproductive_signals)

    is_short = attempt_index < BASELINE_CONFIG['MIN_TRAJECTORY_LENGTH']
    has_heavy_conflict = any(s["id"] == "UNCERTAIN_CONFLICTING_EVIDENCE" for s in uncertainty_signals)
    has_no_eval = any(s["id"] == "UNCERTAIN_NO_EVALUATION_FEEDBACK" for s in uncertainty_signals)

    if is_short or has_heavy_conflict or has_no_eval:
        state = "UNCERTAIN"
    elif prod_weight > unprod_weight and (prod_weight - unprod_weight) >= 0.3:
        state = "PRODUCTIVE"
    elif unprod_weight > prod_weight and (unprod_weight - prod_weight) >= 0.3:
        state = "UNPRODUCTIVE"
    else:
        state = "UNCERTAIN"

    confidence = compute_heuristic_confidence(
        attempt_index,
        state,
        prod_weight,
        unprod_weight,
        uncertainty_signals
    )

    reasoning = generate_reasoning(
        state,
        confidence,
        attempt_index,
        productive_signals,
        unproductive_signals,
        uncertainty_signals
    )

    return {
        "state": state,
        "confidence": confidence,
        "assessment_attempt": attempt_index,
        "evidence": {
            "progression_weight": round(prod_weight, 2),
            "stagnation_weight": round(unprod_weight, 2),
            "conflict_margin": round(abs(prod_weight - unprod_weight), 2)
        },
        "positive_signals": [s["id"] for s in productive_signals],
        "negative_signals": [s["id"] for s in unproductive_signals],
        "uncertainty_signals": [s["id"] for s in uncertainty_signals],
        "signal_details": {
            "productive": productive_signals,
            "unproductive": unproductive_signals,
            "uncertainty": uncertainty_signals
        },
        "reasoning": reasoning,
        "rule_config_version": RULE_CONFIG_VERSION
    }


def assess_prefix(user_id: str, problem_id_or_obj, max_attempts: int = None) -> dict:
    """
    Assess struggle state for a specific USER + PROBLEM trajectory prefix (1 ... t).
    Guarantees online temporal validity (zero future information leakage).
    """
    trajectory_data = build_trajectory(
        user_id=user_id,
        problem_id_or_obj=problem_id_or_obj,
        max_attempts=max_attempts
    )
    
    if "error" in trajectory_data:
        return trajectory_data

    assessment = assess_trajectory(trajectory_data)

    return {
        "trajectory": trajectory_data,
        "assessment": assessment
    }
