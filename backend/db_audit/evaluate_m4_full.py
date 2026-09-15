import os
import sys
import json
import csv
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hint_system.settings')

import django
django.setup()

from hints.models import Attempt
from struggle_analysis.trajectory import extract_attempt_info, normalize_code, compute_transition
from struggle_analysis.snapshot_baseline import assess_snapshot_trajectory
from struggle_analysis.assessment import assess_trajectory
from struggle_analysis.hybrid import fuse_struggle_evidence

LABELS = ['PRODUCTIVE', 'UNPRODUCTIVE', 'UNCERTAIN']

def compute_metrics(y_true, y_pred, method_name):
    valid_pairs = [(t, p) for t, p in zip(y_true, y_pred) if p in LABELS]
    if not valid_pairs:
        return {}

    v_true = [p[0] for p in valid_pairs]
    v_pred = [p[1] for p in valid_pairs]
    
    acc = round(float(accuracy_score(v_true, v_pred)), 4)
    bal_acc = round(float(balanced_accuracy_score(v_true, v_pred)), 4)
    prec_macro = round(float(precision_score(v_true, v_pred, average='macro', zero_division=0)), 4)
    rec_macro = round(float(recall_score(v_true, v_pred, average='macro', zero_division=0)), 4)
    macro_f1 = round(float(f1_score(v_true, v_pred, average='macro', zero_division=0)), 4)

    per_class_f1 = f1_score(v_true, v_pred, labels=LABELS, average=None, zero_division=0)
    prod_f1 = round(float(per_class_f1[0]), 4)
    unprod_f1 = round(float(per_class_f1[1]), 4)
    uncert_f1 = round(float(per_class_f1[2]), 4)

    cm = confusion_matrix(v_true, v_pred, labels=LABELS).tolist()

    return {
        'method_name': method_name,
        'total_prefixes': len(y_true),
        'valid_count': len(valid_pairs),
        'failed_count': len(y_true) - len(valid_pairs),
        'accuracy': acc,
        'balanced_accuracy': bal_acc,
        'precision_macro': prec_macro,
        'recall_macro': rec_macro,
        'macro_f1': macro_f1,
        'productive_f1': prod_f1,
        'unproductive_f1': unprod_f1,
        'uncertain_f1': uncert_f1,
        'confusion_matrix': cm
    }

def main():
    print("=" * 80)
    print("STARTING EVALUATION OF M4 HYBRID MODEL (FULL DATASET: ALL 89 PREFIXES)")
    print("=" * 80)

    # 1. Load Ground Truth Human Reference Labels
    gt_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'human_annotations_with_final_label.json')
    with open(gt_json_path, 'r', encoding='utf-8') as f:
        gt_data = json.load(f)

    prefix_records = gt_data.get('records', [])
    print(f"Loaded {len(prefix_records)} ground truth reference prefixes.")

    # 2. Load Cached M3 Predictions
    m3_cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'm3_full_llm_cache.json')
    if not os.path.exists(m3_cache_path):
        raise FileNotFoundError(f"M3 cache file not found: {m3_cache_path}")

    with open(m3_cache_path, 'r', encoding='utf-8') as f:
        m3_cache = json.load(f)

    print(f"Loaded M3 full cache containing {len(m3_cache)} entries.")

    # 3. Pre-fetch attempts & build trajectories in memory
    unique_sids = set(rec['session_id'] for rec in prefix_records)
    print(f"Pre-fetching attempts for {len(unique_sids)} valid sessions...", flush=True)

    all_attempts = Attempt.objects.filter(
        session_id__in=unique_sids
    ).select_related('problem').order_by('created_at', 'id')

    attempts_by_session = {}
    for att in all_attempts:
        attempts_by_session.setdefault(att.session_id, []).append(att)

    def build_trajectory_from_attempts(attempt_objs):
        if not attempt_objs:
            return {}
        first_att = attempt_objs[0]
        user_id = first_att.user_id
        problem = first_att.problem
        problem_id = problem.problem_id or str(problem.id)
        problem_title = problem.title

        raw_attempts = []
        attempt_info_list = []
        for idx, att in enumerate(attempt_objs, start=1):
            info = extract_attempt_info(att, idx)
            attempt_info_list.append(info)
            clean_item = {k: v for k, v in info.items() if k != "created_at_dt"}
            raw_attempts.append(clean_item)

        transitions = []
        first_dt = attempt_info_list[0]["created_at_dt"] if attempt_info_list else None
        prior_codes = []

        for i in range(1, len(attempt_info_list)):
            prev_info = attempt_info_list[i - 1]
            curr_info = attempt_info_list[i]
            prior_codes.append(normalize_code(prev_info["code"]))
            trans = compute_transition(
                prev_info,
                curr_info,
                transitions,
                first_dt=first_dt,
                all_prior_attempt_codes=prior_codes[:-1]
            )
            transitions.append(trans)

        total_attempts = len(raw_attempts)
        total_duration = transitions[-1]["temporal"]["total_trajectory_duration"] if transitions else 0.0

        eval_attempts = [a for a in raw_attempts if a.get("total_tests", 0) > 0]
        if eval_attempts:
            initial_passed = eval_attempts[0]["tests_passed"]
            latest_eval_passed = eval_attempts[-1]["tests_passed"]
            max_passed = max(a["tests_passed"] for a in eval_attempts)
            initial_pass_rate = eval_attempts[0]["pass_rate"]
            latest_pass_rate = eval_attempts[-1]["pass_rate"]
            max_pass_rate = max(a["pass_rate"] for a in eval_attempts)
            overall_test_improvement = latest_eval_passed - initial_passed
            peak_test_improvement = max_passed - initial_passed
            overall_pass_rate_improvement = round(latest_pass_rate - initial_pass_rate, 4)
            peak_pass_rate_improvement = round(max_pass_rate - initial_pass_rate, 4)
        elif raw_attempts:
            initial_passed = raw_attempts[0]["tests_passed"]
            latest_eval_passed = raw_attempts[-1]["tests_passed"]
            max_passed = max(a["tests_passed"] for a in raw_attempts)
            overall_test_improvement = latest_eval_passed - initial_passed
            peak_test_improvement = max_passed - initial_passed
            overall_pass_rate_improvement = 0.0
            peak_pass_rate_improvement = 0.0
        else:
            overall_test_improvement = 0
            peak_test_improvement = 0
            overall_pass_rate_improvement = 0.0
            peak_pass_rate_improvement = 0.0

        number_of_repeat_executions = sum(1 for t in transitions if t["repetition"]["interaction_type"] == "REPEAT_EXECUTION")
        number_of_code_changes = sum(1 for t in transitions if t["repetition"]["interaction_type"] == "CODE_CHANGE")
        number_of_outcome_changes = sum(1 for t in transitions if t["repetition"]["interaction_type"] == "OUTCOME_CHANGE")
        number_of_repeated_states = sum(1 for t in transitions if t["repetition"]["repeated_state"])
        number_of_error_changes = sum(1 for t in transitions if t["error_evolution"]["error_changed"])

        max_stagnation = max([t["repetition"]["stagnation_length"] for t in transitions], default=0)
        current_stagnant = transitions[-1]["repetition"]["stagnation_length"] > 0 if transitions else False

        summary = {
            "total_attempts": total_attempts,
            "total_duration_seconds": round(total_duration, 2),
            "overall_test_improvement": overall_test_improvement,
            "peak_test_improvement": peak_test_improvement,
            "overall_pass_rate_improvement": overall_pass_rate_improvement,
            "peak_pass_rate_improvement": peak_pass_rate_improvement,
            "number_of_repeat_executions": number_of_repeat_executions,
            "number_of_code_changes": number_of_code_changes,
            "number_of_outcome_changes": number_of_outcome_changes,
            "number_of_repeated_states": number_of_repeated_states,
            "number_of_error_changes": number_of_error_changes,
            "stagnation_indicators": {
                "max_stagnation_length": max_stagnation,
                "is_currently_stagnant": current_stagnant
            }
        }

        return {
            "user_id": user_id,
            "problem_id": problem_id,
            "problem_title": problem_title,
            "trajectory_length": total_attempts,
            "attempts": raw_attempts,
            "transitions": transitions,
            "trajectory_summary": summary,
        }

    # 4. Evaluate M1, M2, M3, M4 across all 89 prefixes
    m1_preds = []
    m2_preds = []
    m3_preds = []
    m4_preds = []
    y_true = []

    m4_results_list = []
    m3_matched_count = 0
    missing_m3_keys = []
    m2_m3_disagreement_count = 0
    m4_diff_m2_count = 0
    m4_diff_m3_count = 0
    m4_diff_both_count = 0

    detailed_comparison_rows = []

    for idx, rec in enumerate(prefix_records, 1):
        pkey = rec['prefix_id']
        sid = rec['session_id']
        p_num = rec['prefix_number']
        ref_label = rec['final_human_label']
        y_true.append(ref_label)

        step_limit = p_num + 1
        session_atts = attempts_by_session.get(sid, [])[:step_limit]
        traj_data = build_trajectory_from_attempts(session_atts)

        # M1 Snapshot
        m1_res = assess_snapshot_trajectory(traj_data)
        m1_state = m1_res.get('state', 'UNCERTAIN')
        m1_preds.append(m1_state)

        # M2 Rule-Based
        m2_res = assess_trajectory(traj_data)
        m2_state = m2_res.get('state', 'UNCERTAIN')
        m2_preds.append(m2_state)

        # M3 Cached LLM
        m3_res = m3_cache.get(pkey)
        if m3_res and m3_res.get('state') in LABELS:
            m3_matched_count += 1
            m3_state = m3_res.get('state')
        else:
            missing_m3_keys.append(pkey)
            m3_state = "FAILED/NO_PREDICTION"
        m3_preds.append(m3_state)

        # M4 Hybrid (Fusing M2 + cached M3)
        if m3_res and not m3_res.get('error'):
            m4_res = fuse_struggle_evidence(
                rule_result=m2_res,
                llm_result=m3_res,
                trajectory_data=traj_data
            )
        else:
            # Fallback if M3 missing/error
            m4_res = fuse_struggle_evidence(
                rule_result=m2_res,
                llm_result={'error': 'M3 unavailable'},
                trajectory_data=traj_data
            )

        m4_state = m4_res.get('state', 'UNCERTAIN')
        m4_preds.append(m4_state)

        # Disagreement and difference counters
        if m2_state != m3_state:
            m2_m3_disagreement_count += 1
        if m4_state != m2_state:
            m4_diff_m2_count += 1
        if m4_state != m3_state:
            m4_diff_m3_count += 1
        if m4_state != m2_state and m4_state != m3_state:
            m4_diff_both_count += 1

        m4_results_list.append({
            'prefix_id': pkey,
            'session_id': sid,
            'prefix_number': p_num,
            'reference_label': ref_label,
            'm2_state': m2_state,
            'm3_state': m3_state,
            'predicted_state': m4_state,
            'confidence': m4_res.get('confidence', 0.0),
            'reasoning': m4_res.get('reasoning', ''),
            'evidence': m4_res.get('evidence', {}),
            'recommended_action': m4_res.get('recommended_action', 'MONITOR')
        })

        detailed_comparison_rows.append({
            'Prefix ID': pkey,
            'Session ID': sid,
            'Prefix Number': p_num,
            'Human Reference Label': ref_label,
            'M1 Prediction': m1_state,
            'M2 Prediction': m2_state,
            'M3 Prediction': m3_state,
            'M4 Hybrid Prediction': m4_state,
            'M2-M3 Agree?': 'YES' if m2_state == m3_state else 'NO',
            'M4 Fusion Outcome': 'Consensus' if m2_state == m3_state else ('Conflict (-> UNCERTAIN)' if (m2_state in ['PRODUCTIVE','UNPRODUCTIVE'] and m3_state in ['PRODUCTIVE','UNPRODUCTIVE']) else 'Partial Evidence')
        })

    # Compute metrics for all 4 methods
    m1_metrics = compute_metrics(y_true, m1_preds, "M1 Snapshot Baseline")
    m2_metrics = compute_metrics(y_true, m2_preds, "M2 Rule-Based Feature Model")
    m3_metrics = compute_metrics(y_true, m3_preds, "M3 LLM Trajectory Reasoning (Full)")
    m4_metrics = compute_metrics(y_true, m4_preds, "M4 Hybrid Evidence-Fusion Model (Full)")

    # Save M4 Full Results
    m4_full_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'm4_full_evaluation_results.json')
    with open(m4_full_json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'metrics': m4_metrics,
            'audit_summary': {
                'm3_cache_records_matched': f"{m3_matched_count}/89",
                'missing_invalid_m3_records': missing_m3_keys,
                'm2_m3_disagreements': m2_m3_disagreement_count,
                'm4_differs_from_m2': m4_diff_m2_count,
                'm4_differs_from_m3': m4_diff_m3_count,
                'm4_differs_from_both': m4_diff_both_count,
                'improves_over_m3': m4_metrics['macro_f1'] > m3_metrics['macro_f1']
            },
            'predictions': m4_results_list
        }, f, indent=2)

    # Also update m4_evaluation_results.json
    m4_eval_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'm4_evaluation_results.json')
    with open(m4_eval_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metrics': m4_metrics,
            'predictions': m4_results_list
        }, f, indent=2)

    # Detailed CSV output
    m4_full_csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'm4_full_detailed_results.csv')
    fieldnames = [
        'Prefix ID', 'Session ID', 'Prefix Number', 'Human Reference Label',
        'M1 Prediction', 'M2 Prediction', 'M3 Prediction', 'M4 Hybrid Prediction',
        'M2-M3 Agree?', 'M4 Fusion Outcome'
    ]
    with open(m4_full_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(detailed_comparison_rows)

    # Save comparison summary
    summary_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'struggle_methods_comparison_summary.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'total_evaluated_prefixes': 89,
            'm1_metrics': m1_metrics,
            'm2_metrics': m2_metrics,
            'm3_metrics': m3_metrics,
            'm4_metrics': m4_metrics
        }, f, indent=2)

    print("\n" + "=" * 80)
    print("M4 HYBRID FULL EVALUATION COMPLETED")
    print("=" * 80)
    print(f"M3 Cache Records Matched: {m3_matched_count}/89")
    print(f"Missing M3 Records: {len(missing_m3_keys)}")
    print(f"M2 and M3 Disagreements: {m2_m3_disagreement_count} / 89")
    print(f"M4 Differs from M2: {m4_diff_m2_count} / 89")
    print(f"M4 Differs from M3: {m4_diff_m3_count} / 89")
    print(f"M4 Differs from Both: {m4_diff_both_count} / 89")
    print("-" * 50)
    print(f"Accuracy: {m4_metrics['accuracy']}")
    print(f"Balanced Accuracy: {m4_metrics['balanced_accuracy']}")
    print(f"Macro Precision: {m4_metrics['precision_macro']}")
    print(f"Macro Recall: {m4_metrics['recall_macro']}")
    print(f"Macro F1 Score: {m4_metrics['macro_f1']}")
    print(f"Per-Class F1s -> Productive: {m4_metrics['productive_f1']} | Unproductive: {m4_metrics['unproductive_f1']} | Uncertain: {m4_metrics['uncertain_f1']}")
    print(f"Confusion Matrix [PRODUCTIVE, UNPRODUCTIVE, UNCERTAIN]:\n{m4_metrics['confusion_matrix']}")
    print("=" * 80)

if __name__ == '__main__':
    main()
