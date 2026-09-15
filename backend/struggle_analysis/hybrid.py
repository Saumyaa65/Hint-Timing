"""
Hybrid Struggle Assessment Method (Condition M4)

Combines objective trajectory features & rule-based outputs (M2) with
LLM trajectory reasoning (M3) using an interpretable evidence-fusion layer.

Research Methodological Candidate (Not validated empirical ground truth).
"""

import logging
from typing import Dict, Any, Optional

from .config import HYBRID_CONFIG, RULE_CONFIG_VERSION
from .trajectory import build_trajectory
from .assessment import assess_trajectory
from .llm_assessment import assess_trajectory_with_llm, PROMPT_VERSION

logger = logging.getLogger(__name__)


def fuse_struggle_evidence(rule_result: dict, llm_result: dict, trajectory_data: dict, strict_model_pinning: bool = False) -> dict:
    """
    Interpretable Evidence-Fusion Layer (Condition M4):
    Explicitly combines objective trajectory signals (M2) and LLM trajectory reasoning (M3)
    using weighted confidence dominance, objective test suite precedence, and consensus fusion.
    """
    t = trajectory_data.get("trajectory_length", 0)
    summary = trajectory_data.get("trajectory_summary", {})
    pass_rate_imp = summary.get("overall_pass_rate_improvement", 0.0)
    peak_test_imp = summary.get("peak_test_improvement", 0)

    rule_state = rule_result.get("state", "UNCERTAIN")
    rule_conf = float(rule_result.get("confidence", 0.5))
    rule_pos = rule_result.get("positive_signals", [])
    rule_neg = rule_result.get("negative_signals", [])
    rule_unc = rule_result.get("uncertainty_signals", [])
    rule_reasoning = rule_result.get("reasoning", "")

    llm_error = llm_result.get("error")
    llm_state = llm_result.get("state", "UNCERTAIN") if not llm_error else "UNCERTAIN"
    llm_conf = float(llm_result.get("confidence", 0.5)) if not llm_error else 0.0
    llm_pos = llm_result.get("positive_signals", []) if not llm_error else []
    llm_neg = llm_result.get("negative_signals", []) if not llm_error else []
    llm_unc = llm_result.get("uncertainty_signals", []) if not llm_error else []
    llm_reasoning = llm_result.get("reasoning", "") if not llm_error else ""
    llm_model = llm_result.get("model", "N/A")

    objective_evidence = []
    for s in rule_pos:
        objective_evidence.append(f"Objective Positive: {s}")
    for s in rule_neg:
        objective_evidence.append(f"Objective Negative: {s}")
    for s in rule_unc:
        objective_evidence.append(f"Objective Uncertainty: {s}")

    llm_evidence_list = []
    if llm_error:
        llm_evidence_list.append(f"LLM Unavailable: {llm_error}")
    else:
        for s in llm_pos:
            llm_evidence_list.append(f"LLM Positive: {s}")
        for s in llm_neg:
            llm_evidence_list.append(f"LLM Negative: {s}")
        for s in llm_unc:
            llm_evidence_list.append(f"LLM Uncertainty: {s}")

    agreement_evidence = []
    conflict_evidence = []

    pos_signals = list(dict.fromkeys(rule_pos + llm_pos))
    neg_signals = list(dict.fromkeys(rule_neg + llm_neg))
    unc_signals = list(dict.fromkeys(rule_unc + llm_unc))

    # Evidence Fusion Logic:
    if t < 2:
        final_state = "UNCERTAIN"
        final_conf = HYBRID_CONFIG['DEFAULT_UNCERTAIN_CONFIDENCE']
        unc_signals.append("HYBRID_SHORT_TRAJECTORY")
        reasoning = f"Trajectory prefix is too short ({t} attempts). Hybrid struggle assessment requires at least 2 attempts."
    elif llm_error:
        final_state = rule_state
        final_conf = max(0.30, rule_conf * 0.90)
        unc_signals.append("HYBRID_LLM_UNAVAILABLE")
        reasoning = f"LLM reasoning unavailable ({llm_error}). Hybrid output fallback to Rule Baseline ({rule_state})."
    elif rule_state == llm_state:
        # Full Consensus / Agreement
        final_state = rule_state
        if final_state in ["PRODUCTIVE", "UNPRODUCTIVE"]:
            base_c = (rule_conf + llm_conf) / 2.0
            final_conf = min(1.0, round(base_c + HYBRID_CONFIG['CONSENSUS_BOOST'], 2))
            agreement_evidence.append(f"Full Consensus: Both Rule Baseline and LLM Reasoning assessed state as {final_state}.")
        else:
            final_state = "UNCERTAIN"
            final_conf = HYBRID_CONFIG['DEFAULT_UNCERTAIN_CONFIDENCE']
            agreement_evidence.append("Full Consensus: Both Rule Baseline and LLM Reasoning assessed state as UNCERTAIN.")

        reasoning = f"Hybrid assessment reached consensus ({final_state}, confidence: {round(final_conf, 2)}). Rule Baseline and LLM Trajectory Reasoning aligned on trajectory evidence."
    elif (rule_state in ["PRODUCTIVE", "UNPRODUCTIVE"]) and (llm_state in ["PRODUCTIVE", "UNPRODUCTIVE"]):
        # Directional Conflict Case (PRODUCTIVE vs UNPRODUCTIVE)
        conf_diff = round(abs(rule_conf - llm_conf), 2)
        conflict_msg = f"Directional Method Conflict: Rule Baseline assessed {rule_state} (conf: {rule_conf:.2f}), whereas LLM Reasoning assessed {llm_state} (conf: {llm_conf:.2f})."
        conflict_evidence.append(conflict_msg)

        # Check for hard objective test suite evidence override (test pass improvement)
        has_strong_obj_productive = (pass_rate_imp >= 0.25 or peak_test_imp >= 2)

        if has_strong_obj_productive and rule_state == "PRODUCTIVE":
            final_state = "PRODUCTIVE"
            final_conf = round(max(0.60, rule_conf * 0.85), 2)
            reasoning = f"Hybrid conflict resolved: Objective test suite evidence (+{pass_rate_imp*100:.1f}% pass rate, +{peak_test_imp} tests passed) takes precedence for PRODUCTIVE state."
        elif conf_diff >= 0.15:
            # High confidence dominance
            if llm_conf > rule_conf:
                final_state = llm_state
                final_conf = round(llm_conf * 0.85, 2)
                reasoning = f"Hybrid conflict resolved: LLM Reasoning higher confidence ({llm_conf:.2f} vs {rule_conf:.2f}) takes precedence for {final_state} state."
            else:
                final_state = rule_state
                final_conf = round(rule_conf * 0.85, 2)
                reasoning = f"Hybrid conflict resolved: Rule Baseline higher confidence ({rule_conf:.2f} vs {llm_conf:.2f}) takes precedence for {final_state} state."
        else:
            # Genuine balanced conflict with close confidence -> UNCERTAIN
            penalty_conf = max(0.20, min(rule_conf, llm_conf) - HYBRID_CONFIG['CONFLICT_PENALTY'])
            final_state = "UNCERTAIN"
            final_conf = round(penalty_conf, 2)
            unc_signals.append("HYBRID_METHOD_CONFLICT")
            reasoning = f"Hybrid assessment detected strong disagreement (Rule: {rule_state}:{rule_conf:.2f} vs LLM: {llm_state}:{llm_conf:.2f}). Defaulting conservatively to UNCERTAIN state (confidence: {round(final_conf, 2)})."
    else:
        # One Method UNCERTAIN, One Directional
        non_unc_state = rule_state if rule_state != "UNCERTAIN" else llm_state
        non_unc_conf = rule_conf if rule_state != "UNCERTAIN" else llm_conf
        source_name = "Rule Baseline" if rule_state != "UNCERTAIN" else "LLM Reasoning"

        agreement_evidence.append(f"Partial Evidence: {source_name} identified directional evidence ({non_unc_state}), while alternate method output UNCERTAIN.")

        final_state = non_unc_state
        final_conf = max(0.40, round(non_unc_conf * 0.85, 2))
        reasoning = f"Hybrid assessment evaluated partial evidence ({final_state}, confidence: {final_conf}). {source_name} provided directional signals while alternate method output UNCERTAIN."

    # Action Recommendation Formulation:
    if final_state == "PRODUCTIVE":
        recommended_action = "CONTINUE"
    elif final_state == "UNPRODUCTIVE":
        recommended_action = "INTERVENE"
    else:
        recommended_action = "MONITOR"

    return {
        "method": "hybrid",
        "assessment_attempt": t,
        "state": final_state,
        "confidence": round(final_conf, 2),
        "evidence": {
            "objective": objective_evidence,
            "llm": llm_evidence_list,
            "agreement": agreement_evidence,
            "conflict": conflict_evidence
        },
        "positive_signals": pos_signals,
        "negative_signals": neg_signals,
        "uncertainty_signals": unc_signals,
        "reasoning": reasoning,
        "recommended_action": recommended_action,
        "metadata": {
            "trajectory_length": t,
            "rule_state": rule_state,
            "rule_confidence": round(rule_conf, 2),
            "rule_config_version": RULE_CONFIG_VERSION,
            "llm_state": llm_state,
            "llm_confidence": round(llm_conf, 2),
            "llm_model": llm_model,
            "strict_model_pinning": strict_model_pinning,
            "prompt_version": PROMPT_VERSION,
            "hybrid_config_version": HYBRID_CONFIG['VERSION'],
            "config_version": HYBRID_CONFIG['VERSION']
        }
    }


def assess_hybrid_trajectory(trajectory_data: dict, model_name: Optional[str] = None, strict_model_pinning: bool = False, llm_result: Optional[dict] = None) -> dict:
    """
    Evaluates trajectory prefix using Condition M4 (Hybrid Feature + LLM struggle assessment).
    If llm_result is provided (e.g., from cache), uses it directly without making an LLM API call.
    """
    rule_result = assess_trajectory(trajectory_data)
    if llm_result is None:
        llm_result = assess_trajectory_with_llm(trajectory_data, model_name=model_name, strict_model_pinning=strict_model_pinning)

    return fuse_struggle_evidence(
        rule_result=rule_result,
        llm_result=llm_result,
        trajectory_data=trajectory_data,
        strict_model_pinning=strict_model_pinning
    )


def assess_prefix_hybrid(user_id: str, problem_id_or_obj, max_attempts: Optional[int] = None, model_name: Optional[str] = None, strict_model_pinning: bool = False) -> dict:
    """
    Assess struggle state for a specific USER + PROBLEM trajectory prefix (1 ... t) using Hybrid Assessment.
    Guarantees online temporal validity (zero future information leakage).
    """
    trajectory_data = build_trajectory(user_id=user_id, problem_id_or_obj=problem_id_or_obj, max_attempts=max_attempts)

    if "error" in trajectory_data:
        return trajectory_data

    assessment = assess_hybrid_trajectory(trajectory_data, model_name=model_name, strict_model_pinning=strict_model_pinning)

    return {
        "trajectory_prefix": trajectory_data,
        "assessment": assessment
    }
