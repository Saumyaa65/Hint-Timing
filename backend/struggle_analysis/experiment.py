"""
Research Experimentation Framework for Struggle Assessment (TASK 2D)

Provides common evaluation interface, prefix trajectory experiment runner,
method agreement/disagreement analyzer, controlled pattern evaluators (P1..P10),
and research JSON dataset exporter.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from .trajectory import build_trajectory, build_trajectory_from_dicts
from .snapshot_baseline import assess_snapshot_trajectory
from .assessment import assess_trajectory
from .llm_assessment import assess_trajectory_with_llm
from .hybrid import assess_hybrid_trajectory

logger = logging.getLogger(__name__)


def normalize_assessment_output(raw_output: dict, method_name: str, attempt_idx: int) -> dict:
    """
    Normalizes assessment outputs across all methods into a common schema.
    """
    state = raw_output.get("state", "UNCERTAIN")
    if state not in ["PRODUCTIVE", "UNPRODUCTIVE", "UNCERTAIN"]:
        state = "UNCERTAIN"

    confidence = raw_output.get("confidence")
    if confidence is None:
        confidence = 0.5
    else:
        try:
            confidence = float(confidence)
        except (ValueError, TypeError):
            confidence = 0.5

    evidence = raw_output.get("evidence", {})
    if not isinstance(evidence, dict):
        evidence = {"raw": str(evidence)}

    pos_signals = raw_output.get("positive_signals") or evidence.get("positive_signals") or []
    neg_signals = raw_output.get("negative_signals") or evidence.get("negative_signals") or []
    unc_signals = raw_output.get("uncertainty_signals") or evidence.get("uncertainty_signals") or []

    reasoning = raw_output.get("reasoning", "")
    error_msg = raw_output.get("error")

    norm_dict = {
        "method": method_name,
        "assessment_attempt": attempt_idx,
        "state": state,
        "confidence": round(confidence, 2),
        "positive_signals": pos_signals,
        "negative_signals": neg_signals,
        "uncertainty_signals": unc_signals,
        "reasoning": reasoning,
        "error": error_msg
    }

    if "recommended_action" in raw_output:
        norm_dict["recommended_action"] = raw_output["recommended_action"]
    if "metadata" in raw_output:
        norm_dict["metadata"] = raw_output["metadata"]
    if "evidence" in raw_output and isinstance(raw_output["evidence"], dict) and ("objective" in raw_output["evidence"] or "llm" in raw_output["evidence"]):
        norm_dict["evidence"] = raw_output["evidence"]

    return norm_dict


def assess_with_method(
    method: str,
    user_id: str,
    problem_id_or_obj,
    max_attempts: Optional[int] = None,
    model_name: Optional[str] = None
) -> dict:
    """
    Common Assessment Interface:
    Evaluates a trajectory prefix (1 ... t) with a specified method:
    - 'snapshot' (Condition M1)
    - 'rule_based' (Condition M2)
    - 'llm' (Condition M3)
    - 'hybrid' (Condition M4)
    """
    method_key = method.lower().strip()
    trajectory_data = build_trajectory(user_id=user_id, problem_id_or_obj=problem_id_or_obj, max_attempts=max_attempts)

    if "error" in trajectory_data:
        return trajectory_data

    attempt_idx = trajectory_data.get("trajectory_length", 0)

    if method_key == "snapshot":
        raw = assess_snapshot_trajectory(trajectory_data)
        normalized = normalize_assessment_output(raw, "Snapshot Baseline", attempt_idx)
    elif method_key in ["rule_based", "baseline", "rule"]:
        raw = assess_trajectory(trajectory_data)
        normalized = normalize_assessment_output(raw, "Rule-Based Baseline", attempt_idx)
    elif method_key in ["llm", "llm_reasoning"]:
        raw = assess_trajectory_with_llm(trajectory_data, model_name=model_name)
        normalized = normalize_assessment_output(raw, "LLM Trajectory Reasoning", attempt_idx)
        normalized["model"] = raw.get("model", model_name or "N/A")
    elif method_key in ["hybrid", "m4"]:
        raw = assess_hybrid_trajectory(trajectory_data, model_name=model_name)
        normalized = normalize_assessment_output(raw, "Hybrid Feature + LLM", attempt_idx)
    else:
        return {"error": f"Unsupported method '{method}'. Choose from: 'snapshot', 'rule_based', 'llm', 'hybrid'."}

    return {
        "user_id": user_id,
        "problem_id": trajectory_data.get("problem_id"),
        "trajectory_length": attempt_idx,
        "assessment": normalized
    }


def analyze_method_agreement(evaluations: List[dict]) -> dict:
    """
    Calculates pairwise and 4-way agreement metrics across attempt step evaluations.
    Explicitly framed as METHOD AGREEMENT, NOT empirical accuracy validation.
    """
    if not evaluations:
        return {"error": "No evaluations provided for agreement analysis."}

    total_steps = len(evaluations)
    snap_rule_agree = 0
    snap_llm_agree = 0
    rule_llm_agree = 0
    rule_hybrid_agree = 0
    llm_hybrid_agree = 0
    all_3_agree = 0
    all_4_agree = 0
    disagreements = []

    for item in evaluations:
        t = item.get("attempt")
        snap = item.get("snapshot", {}).get("state")
        rule = item.get("rule_based", {}).get("state")
        llm = item.get("llm", {}).get("state")
        hyb = item.get("hybrid", {}).get("state")

        s_r = (snap == rule) if (snap and rule) else False
        s_l = (snap == llm) if (snap and llm) else False
        r_l = (rule == llm) if (rule and llm) else False
        r_h = (rule == hyb) if (rule and hyb) else False
        l_h = (llm == hyb) if (llm and hyb) else False

        a_3 = (snap == rule == llm) if (snap and rule and llm) else False
        a_4 = (snap == rule == llm == hyb) if (snap and rule and llm and hyb) else False

        if s_r: snap_rule_agree += 1
        if s_l: snap_llm_agree += 1
        if r_l: rule_llm_agree += 1
        if r_h: rule_hybrid_agree += 1
        if l_h: llm_hybrid_agree += 1
        if a_3: all_3_agree += 1
        if a_4: all_4_agree += 1

        if not a_4:
            explanations = []
            if snap != rule:
                explanations.append(f"Snapshot ({snap}) vs Rule ({rule}): Snapshot evaluates only latest attempt.")
            if rule != llm:
                explanations.append(f"Rule ({rule}) vs LLM ({llm}): Rule-based heuristics and LLM trajectory reasoning evaluated conflicting signals differently.")
            if hyb and (hyb != rule or hyb != llm):
                explanations.append(f"Hybrid ({hyb}) vs Component Methods: Evidence fusion resolved signal weights or uncertainty conservatively.")

            disagreements.append({
                "attempt": t,
                "states": {"snapshot": snap, "rule_based": rule, "llm": llm, "hybrid": hyb},
                "explanation": " | ".join(explanations)
            })

    return {
        "total_evaluated_attempts": total_steps,
        "agreement_rates": {
            "snapshot_vs_rule": round(snap_rule_agree / total_steps, 2) if total_steps else 0.0,
            "snapshot_vs_llm": round(snap_llm_agree / total_steps, 2) if total_steps else 0.0,
            "rule_vs_llm": round(rule_llm_agree / total_steps, 2) if total_steps else 0.0,
            "rule_vs_hybrid": round(rule_hybrid_agree / total_steps, 2) if total_steps else 0.0,
            "llm_vs_hybrid": round(llm_hybrid_agree / total_steps, 2) if total_steps else 0.0,
            "all_three_consensus": round(all_3_agree / total_steps, 2) if total_steps else 0.0,
            "all_four_consensus": round(all_4_agree / total_steps, 2) if total_steps else 0.0
        },
        "disagreement_count": len(disagreements),
        "disagreement_locations": disagreements,
        "note": "METHOD AGREEMENT ONLY. Agreement indicates operational state alignment across algorithms, NOT empirical gold-standard validation."
    }


def run_prefix_experiment(user_id: str, problem_id_or_obj, model_name: Optional[str] = None, include_llm: bool = True) -> dict:
    """
    Evaluates trajectory prefixes A_1 ... A_t for t=1 ... N across active methods M1..M4.
    Returns full prefix progression matrix.
    """
    full_trajectory = build_trajectory(user_id=user_id, problem_id_or_obj=problem_id_or_obj)

    if "error" in full_trajectory:
        return full_trajectory

    attempts = full_trajectory.get("attempts", [])
    total_attempts = len(attempts)

    prefix_evaluations = []

    for t in range(1, total_attempts + 1):
        prefix_data = build_trajectory(user_id=user_id, problem_id_or_obj=problem_id_or_obj, max_attempts=t)

        snap_raw = assess_snapshot_trajectory(prefix_data)
        snap_norm = normalize_assessment_output(snap_raw, "Snapshot Baseline", t)

        rule_raw = assess_trajectory(prefix_data)
        rule_norm = normalize_assessment_output(rule_raw, "Rule-Based Baseline", t)

        if include_llm:
            llm_raw = assess_trajectory_with_llm(prefix_data, model_name=model_name, strict_model_pinning=True)
            llm_norm = normalize_assessment_output(llm_raw, "LLM Trajectory Reasoning", t)
            llm_norm["model"] = llm_raw.get("model", model_name or "N/A")

            hyb_raw = assess_hybrid_trajectory(prefix_data, model_name=model_name, strict_model_pinning=True)
            hyb_norm = normalize_assessment_output(hyb_raw, "Hybrid Feature + LLM", t)
        else:
            llm_norm = {"method": "LLM Trajectory Reasoning", "assessment_attempt": t, "state": "SKIPPED", "confidence": 0.0, "reasoning": "LLM execution omitted in fast mode."}
            hyb_raw = assess_hybrid_trajectory(prefix_data, model_name=model_name, strict_model_pinning=True)
            hyb_norm = normalize_assessment_output(hyb_raw, "Hybrid Feature + LLM", t)

        prefix_evaluations.append({
            "attempt": t,
            "snapshot": snap_norm,
            "rule_based": rule_norm,
            "llm": llm_norm,
            "hybrid": hyb_norm
        })

    agreement_analysis = analyze_method_agreement(prefix_evaluations)

    return {
        "user_id": user_id,
        "problem_id": full_trajectory.get("problem_id"),
        "problem_title": full_trajectory.get("problem_title"),
        "trajectory_length": total_attempts,
        "prefix_results": prefix_evaluations,
        "agreement_summary": agreement_analysis
    }


def get_controlled_patterns() -> Dict[str, dict]:
    """
    Generates research controlled behavioral trajectory scenarios P1..P10.
    """
    base_meta = {"user_id": "test_user_controlled", "problem_id": "controlled-test-problem", "problem_title": "Controlled Test Problem"}

    def make_att(idx, passed, total, status="ACCEPTED", err="", code="class Solution {}"):
        pr = passed / total if total > 0 else 0.0
        return {
            "index": idx,
            "status": status,
            "language": "java",
            "tests_passed": passed,
            "tests_failed": total - passed,
            "total_tests": total,
            "pass_rate": pr,
            "error_message": err,
            "code": code
        }

    patterns = {}

    # P1: Monotonic Progression (0/10 -> 2/10 -> 5/10 -> 8/10 -> 10/10)
    p1_atts = [make_att(1,0,10,"WRONG_ANSWER","","code_v1"), make_att(2,2,10,"WRONG_ANSWER","","code_v2"), make_att(3,5,10,"WRONG_ANSWER","","code_v3"), make_att(4,8,10,"WRONG_ANSWER","","code_v4"), make_att(5,10,10,"ACCEPTED","","code_v5")]
    patterns["P1"] = {"pattern_id": "P1", "name": "Monotonic Progression", "expected_behavior": "Exposes consistent performance improvement towards solution.", "attempts": p1_atts}

    # P2: Persistent Stagnation (0/10 x5 identical code)
    p2_atts = [make_att(i, 0, 10, "WRONG_ANSWER", "", "same_code_loop") for i in range(1, 6)]
    patterns["P2"] = {"pattern_id": "P2", "name": "Persistent Stagnation", "expected_behavior": "Exposes static repetition negative signals.", "attempts": p2_atts}

    # P3: Error Evolution (Compile Error -> Runtime Error -> Wrong Answer -> 5/10 -> 8/10)
    p3_atts = [
        make_att(1,0,10,"COMPILE_ERROR","Syntax error line 5","code_v1"),
        make_att(2,0,10,"RUNTIME_ERROR","NullPointerException","code_v2"),
        make_att(3,2,10,"WRONG_ANSWER","","code_v3"),
        make_att(4,5,10,"WRONG_ANSWER","","code_v4"),
        make_att(5,8,10,"WRONG_ANSWER","","code_v5")
    ]
    patterns["P3"] = {"pattern_id": "P3", "name": "Error Evolution", "expected_behavior": "Shifting error types represent execution stage progress.", "attempts": p3_atts}

    # P4: Exploration Without Feedback (Code A -> Code B -> Code C no evaluation)
    p4_atts = [make_att(1,0,0,"NO_EVAL","","code_a"), make_att(2,0,0,"NO_EVAL","","code_b"), make_att(3,0,0,"NO_EVAL","","code_c")]
    patterns["P4"] = {"pattern_id": "P4", "name": "Exploration Without Feedback", "expected_behavior": "Output UNCERTAIN due to lack of evaluation feedback.", "attempts": p4_atts}

    # P5: Stagnation -> Recovery (0/10 x3 -> 5/10 -> 8/10)
    p5_atts = [make_att(1,0,10,"WRONG_ANSWER","","code_a"), make_att(2,0,10,"WRONG_ANSWER","","code_a"), make_att(3,0,10,"WRONG_ANSWER","","code_a"), make_att(4,5,10,"WRONG_ANSWER","","code_b"), make_att(5,8,10,"WRONG_ANSWER","","code_c")]
    patterns["P5"] = {"pattern_id": "P5", "name": "Stagnation -> Recovery", "expected_behavior": "Distinguishes early stagnation (t=3) from later recovery (t=5).", "attempts": p5_atts}

    # P6: Cyclic Exploration (A -> B -> A -> B)
    p6_atts = [make_att(1,0,10,"WRONG_ANSWER","","code_a"), make_att(2,0,10,"WRONG_ANSWER","","code_b"), make_att(3,0,10,"WRONG_ANSWER","","code_a"), make_att(4,0,10,"WRONG_ANSWER","","code_b")]
    patterns["P6"] = {"pattern_id": "P6", "name": "Cyclic Exploration", "expected_behavior": "Exposes code reversion and cyclic oscillation without progress.", "attempts": p6_atts}

    # P7: Mixed Evidence (Repeated error -> major code change -> same score -> different error)
    p7_atts = [make_att(1,0,10,"RUNTIME_ERROR","IndexOutOfBounds","code_a"), make_att(2,0,10,"RUNTIME_ERROR","IndexOutOfBounds","code_a"), make_att(3,0,10,"WRONG_ANSWER","","code_b_major_change"), make_att(4,0,10,"RUNTIME_ERROR","NullPointer","code_c")]
    patterns["P7"] = {"pattern_id": "P7", "name": "Mixed Evidence", "expected_behavior": "Captures conflicting progress and error regression signals.", "attempts": p7_atts}

    # P8: Temporary Regression (5/10 -> 3/10 -> 6/10 -> 8/10)
    p8_atts = [make_att(1,5,10,"WRONG_ANSWER","","code_a"), make_att(2,3,10,"WRONG_ANSWER","","code_b_refactor"), make_att(3,6,10,"WRONG_ANSWER","","code_c"), make_att(4,8,10,"WRONG_ANSWER","","code_d")]
    patterns["P8"] = {"pattern_id": "P8", "name": "Temporary Regression", "expected_behavior": "Temporary score drop during refactoring does not force UNPRODUCTIVE.", "attempts": p8_atts}

    # P9: Fast Success (0/10 -> 10/10)
    p9_atts = [make_att(1,0,10,"WRONG_ANSWER","","code_a"), make_att(2,10,10,"ACCEPTED","","code_b")]
    patterns["P9"] = {"pattern_id": "P9", "name": "Fast Success", "expected_behavior": "Quick solve; trajectory exposes brief attempt history.", "attempts": p9_atts}

    # P10: Long Failure With Exploration (0/10 -> 0/10 -> 1/10 -> 0/10 -> 2/10 -> 3/10)
    p10_atts = [make_att(1,0,10,"WRONG_ANSWER","","c1"), make_att(2,0,10,"WRONG_ANSWER","","c2"), make_att(3,1,10,"WRONG_ANSWER","","c3"), make_att(4,0,10,"WRONG_ANSWER","","c4"), make_att(5,2,10,"WRONG_ANSWER","","c5"), make_att(6,3,10,"WRONG_ANSWER","","c6")]
    patterns["P10"] = {"pattern_id": "P10", "name": "Long Failure With Exploration", "expected_behavior": "Slow progress with high exploration; tests threshold handling.", "attempts": p10_atts}

    for pid, pdata in patterns.items():
        traj_data = build_trajectory_from_dicts(
            attempts_list=pdata["attempts"],
            user_id="test_user_controlled",
            problem_id="controlled-test-problem",
            problem_title="Controlled Test Problem"
        )
        pdata["trajectory_data"] = traj_data

    return patterns


def run_controlled_experiment(pattern_id: Optional[str] = None, include_llm: bool = False, model_name: Optional[str] = None) -> dict:
    """
    Evaluates controlled behavioral patterns P1..P10 across active assessment methods (M1..M4).
    """
    patterns = get_controlled_patterns()
    if pattern_id:
        if pattern_id not in patterns:
            return {"error": f"Invalid pattern_id '{pattern_id}'. Available: {list(patterns.keys())}"}
        target_patterns = {pattern_id: patterns[pattern_id]}
    else:
        target_patterns = patterns

    results = []

    for pid, pdata in target_patterns.items():
        traj_data = pdata["trajectory_data"]
        t = len(pdata["attempts"])

        snap_raw = assess_snapshot_trajectory(traj_data)
        snap_norm = normalize_assessment_output(snap_raw, "Snapshot Baseline", t)

        rule_raw = assess_trajectory(traj_data)
        rule_norm = normalize_assessment_output(rule_raw, "Rule-Based Baseline", t)

        if include_llm:
            llm_raw = assess_trajectory_with_llm(traj_data, model_name=model_name, strict_model_pinning=True)
            llm_norm = normalize_assessment_output(llm_raw, "LLM Trajectory Reasoning", t)
        else:
            llm_norm = {"method": "LLM Trajectory Reasoning", "assessment_attempt": t, "state": "SKIPPED", "confidence": 0.0, "reasoning": "Omitted"}

        hyb_raw = assess_hybrid_trajectory(traj_data, model_name=model_name, strict_model_pinning=True)
        hyb_norm = normalize_assessment_output(hyb_raw, "Hybrid Feature + LLM", t)

        results.append({
            "pattern_id": pid,
            "name": pdata["name"],
            "expected_behavior": pdata["expected_behavior"],
            "attempt_count": t,
            "snapshot": snap_norm,
            "rule_based": rule_norm,
            "llm": llm_norm,
            "hybrid": hyb_norm
        })

    return {
        "experiment": "Controlled Trajectory Pattern Experiment (P1..P10)",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "results": results
    }


def export_experiment_dataset(experiment_results: dict, output_file: Optional[str] = None) -> dict:
    """
    Exports research experiment results into structured, pandas-friendly JSON format.
    """
    export_payload = {
        "export_metadata": {
            "system": "Personalized Contextual Hint Generation System - Research Framework",
            "export_timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "TASK_2D_EXPERIMENTAL_V1"
        },
        "experiment_data": experiment_results
    }

    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_payload, f, indent=2)
            export_payload["export_file"] = output_file
        except Exception as e:
            logger.error(f"Failed to export experiment dataset to {output_file}: {e}")
            export_payload["export_error"] = str(e)

    return export_payload
