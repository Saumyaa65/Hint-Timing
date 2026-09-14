from typing import Dict, Any
from .assessment import assess_prefix
from .llm_assessment import assess_prefix_with_llm


def compare_struggle_assessments(
    user_id: str,
    problem_id_or_obj,
    max_attempts: int = None,
    model_name: str = None
) -> Dict[str, Any]:
    """
    Research Utility:
    Run BOTH the Rule-Based Baseline and LLM Trajectory Reasoning methods
    on the exact same trajectory prefix (1 ... t) and compare outputs.
    
    IMPORTANT: 'agreement' indicates whether both provisional operationalizations
    produced the same state. It is NOT accuracy or empirical gold-standard validation.
    """
    rule_result = assess_prefix(
        user_id=user_id,
        problem_id_or_obj=problem_id_or_obj,
        max_attempts=max_attempts
    )

    if "error" in rule_result:
        return rule_result

    llm_result = assess_prefix_with_llm(
        user_id=user_id,
        problem_id_or_obj=problem_id_or_obj,
        max_attempts=max_attempts,
        model_name=model_name
    )

    rule_assessment = rule_result.get("assessment", {})
    llm_assessment = llm_result.get("assessment", {})

    rule_state = rule_assessment.get("state", "UNCERTAIN")
    llm_state = llm_assessment.get("state", "UNCERTAIN")

    agreement = (rule_state == llm_state)

    return {
        "user_id": user_id,
        "problem_id": rule_result.get("trajectory", {}).get("problem_id"),
        "trajectory_length": rule_result.get("trajectory", {}).get("trajectory_length", 0),
        "rule_based": {
            "method": "Rule-Based Baseline",
            "state": rule_state,
            "confidence": rule_assessment.get("confidence"),
            "positive_signals": rule_assessment.get("positive_signals", []),
            "negative_signals": rule_assessment.get("negative_signals", []),
            "uncertainty_signals": rule_assessment.get("uncertainty_signals", []),
            "reasoning": rule_assessment.get("reasoning", "")
        },
        "llm": {
            "method": "LLM Trajectory Reasoning",
            "model": llm_assessment.get("model", "N/A"),
            "state": llm_state,
            "confidence": llm_assessment.get("confidence"),
            "positive_signals": llm_assessment.get("positive_signals", []),
            "negative_signals": llm_assessment.get("negative_signals", []),
            "uncertainty_signals": llm_assessment.get("uncertainty_signals", []),
            "recommended_action": llm_assessment.get("recommended_action", "N/A"),
            "reasoning": llm_assessment.get("reasoning", ""),
            "error": llm_assessment.get("error") if "error" in llm_assessment else None
        },
        "agreement": agreement,
        "disagreement_detected": not agreement,
        "comparison_note": "PROTOTYPE METHODOLOGY COMPARISON ONLY. Agreement does not equal empirical accuracy validation."
    }
