import os
import sys
import json
import csv
import time
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
from struggle_analysis.trajectory import build_trajectory, extract_attempt_info, normalize_code, compute_transition
from struggle_analysis.snapshot_baseline import assess_snapshot_trajectory
from struggle_analysis.assessment import assess_trajectory
from struggle_analysis.llm_assessment import assess_trajectory_with_llm
from struggle_analysis.hybrid import assess_hybrid_trajectory

LABELS = ['PRODUCTIVE', 'UNPRODUCTIVE', 'UNCERTAIN']

def compute_metrics(y_true, y_pred, method_name):
    # Filter valid pairs (excluding FAILED/NO_PREDICTION)
    valid_pairs = [(t, p) for t, p in zip(y_true, y_pred) if p in LABELS]
    
    if not valid_pairs:
        return {
            'method_name': method_name,
            'total_prefixes': len(y_true),
            'valid_count': 0,
            'failed_count': len(y_true),
            'accuracy': 0.0,
            'balanced_accuracy': 0.0,
            'precision_macro': 0.0,
            'recall_macro': 0.0,
            'macro_f1': 0.0,
            'productive_f1': 0.0,
            'unproductive_f1': 0.0,
            'uncertain_f1': 0.0,
            'confusion_matrix': [[0,0,0],[0,0,0],[0,0,0]]
        }

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

def run_evaluation():
    print("=" * 80)
    print("STARTING EVALUATION OF STRUGGLE METHODS (M1, M2, M3, M4)")
    print("=" * 80)

    # 1. Load Ground Truth Human Reference Labels
    gt_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'human_annotations_with_final_label.json')
    if not os.path.exists(gt_json_path):
        raise FileNotFoundError(f"Reference file not found: {gt_json_path}")

    with open(gt_json_path, 'r', encoding='utf-8') as f:
        gt_data = json.load(f)

    prefix_records = gt_data.get('records', [])
    print(f"Loaded {len(prefix_records)} ground truth reference prefixes.")

    # Cache file for M3 LLM calls
    m3_cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'm3_llm_cache.json')
    m3_cache = {}
    if os.path.exists(m3_cache_path):
        try:
            with open(m3_cache_path, 'r', encoding='utf-8') as f:
                m3_cache = json.load(f)
            print(f"Loaded {len(m3_cache)} cached M3 LLM predictions.")
        except Exception as e:
            print(f"Warning loading M3 cache: {e}")

    # Pre-fetch all attempts for unique valid sessions in 1 single fast DB query
    prefix_trajectories = []
    y_true = []

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

    for idx, rec in enumerate(prefix_records, 1):
        sid = rec['session_id']
        p_num = rec['prefix_number']
        ref_label = rec['final_human_label']
        pkey = rec['prefix_id']

        step_limit = p_num + 1
        session_atts = attempts_by_session.get(sid, [])[:step_limit]
        traj_data = build_trajectory_from_attempts(session_atts)

        prefix_trajectories.append({
            'prefix_id': pkey,
            'session_id': sid,
            'prefix_number': p_num,
            'reference_label': ref_label,
            'trajectory_data': traj_data
        })
        y_true.append(ref_label)

    print(f"Built trajectories for all {len(prefix_trajectories)} prefixes in memory.", flush=True)

    # -------------------------------------------------------------------------
    # METHOD 1: M1 SNAPSHOT BASELINE
    # -------------------------------------------------------------------------
    print("\n" + "=" * 50)
    print("EVALUATING METHOD 1: M1 SNAPSHOT BASELINE")
    print("=" * 50)

    m1_predictions = []
    m1_results_list = []

    for item in prefix_trajectories:
        res = assess_snapshot_trajectory(item['trajectory_data'])
        pred_state = res.get('state', 'UNCERTAIN')
        m1_predictions.append(pred_state)
        m1_results_list.append({
            'prefix_id': item['prefix_id'],
            'reference_label': item['reference_label'],
            'predicted_state': pred_state,
            'confidence': res.get('confidence', 0.0),
            'reasoning': res.get('reasoning', '')
        })

    m1_metrics = compute_metrics(y_true, m1_predictions, "M1 Snapshot Baseline")
    
    m1_eval_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'm1_evaluation_results.json')
    with open(m1_eval_file, 'w', encoding='utf-8') as f:
        json.dump({'metrics': m1_metrics, 'predictions': m1_results_list}, f, indent=2)

    print(f"[OK] M1 Completed: Macro F1 = {m1_metrics['macro_f1']} (Accuracy: {m1_metrics['accuracy']})", flush=True)

    # -------------------------------------------------------------------------
    # METHOD 2: M2 RULE-BASED FEATURE MODEL
    # -------------------------------------------------------------------------
    print("\n" + "=" * 50)
    print("EVALUATING METHOD 2: M2 RULE-BASED FEATURE MODEL")
    print("=" * 50)

    m2_predictions = []
    m2_results_list = []

    for item in prefix_trajectories:
        res = assess_trajectory(item['trajectory_data'])
        pred_state = res.get('state', 'UNCERTAIN')
        m2_predictions.append(pred_state)
        m2_results_list.append({
            'prefix_id': item['prefix_id'],
            'reference_label': item['reference_label'],
            'predicted_state': pred_state,
            'confidence': res.get('confidence', 0.0),
            'reasoning': res.get('reasoning', '')
        })

    m2_metrics = compute_metrics(y_true, m2_predictions, "M2 Rule-Based Feature Model")

    m2_eval_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'm2_evaluation_results.json')
    with open(m2_eval_file, 'w', encoding='utf-8') as f:
        json.dump({'metrics': m2_metrics, 'predictions': m2_results_list}, f, indent=2)

    print(f"[OK] M2 Completed: Macro F1 = {m2_metrics['macro_f1']} (Accuracy: {m2_metrics['accuracy']})", flush=True)

    # -------------------------------------------------------------------------
    # METHOD 3: M3 LLM TRAJECTORY REASONING
    # -------------------------------------------------------------------------
    print("\n" + "=" * 50)
    print("EVALUATING METHOD 3: M3 LLM TRAJECTORY REASONING")
    print("=" * 50)

    m3_predictions = []
    m3_results_list = []
    m3_status_list = []

    for idx, item in enumerate(prefix_trajectories, 1):
        pkey = item['prefix_id']

        if pkey in m3_cache and m3_cache[pkey].get('state') in LABELS:
            res = m3_cache[pkey]
            pred_state = res.get('state')
            err_info = None
            print(f"[{idx}/89] M3 {pkey}: Cached -> {pred_state}")
        else:
            # Call LLM with retry loop & backoff
            retries = 3
            res = None
            err_info = None

            for attempt_num in range(1, retries + 1):
                try:
                    res = assess_trajectory_with_llm(item['trajectory_data'])
                    if res.get('error'):
                        err_info = res.get('error')
                        print(f"[{idx}/89] M3 {pkey} Attempt {attempt_num} API Error: {err_info}")
                        if "402" in str(err_info) or "429" in str(err_info) or "failed on all candidate models" in str(err_info):
                            break
                        time.sleep(2 * attempt_num)
                    else:
                        break
                except Exception as e:
                    err_info = str(e)
                    print(f"[{idx}/89] M3 {pkey} Attempt {attempt_num} Exception: {err_info}")
                    time.sleep(2 * attempt_num)

            if res and not res.get('error') and res.get('state') in LABELS:
                pred_state = res.get('state')
                m3_cache[pkey] = res
                with open(m3_cache_path, 'w', encoding='utf-8') as f:
                    json.dump(m3_cache, f, indent=2)
                print(f"[{idx}/89] M3 {pkey}: Success -> {pred_state}", flush=True)
            else:
                pred_state = "FAILED/NO_PREDICTION"
                print(f"[{idx}/89] M3 {pkey}: FAILED -> {err_info}")

        m3_predictions.append(pred_state)
        m3_status_list.append(err_info if err_info else "OK")
        m3_results_list.append({
            'prefix_id': pkey,
            'reference_label': item['reference_label'],
            'predicted_state': pred_state,
            'confidence': res.get('confidence', 0.0) if res else 0.0,
            'error': err_info,
            'reasoning': res.get('reasoning', '') if res else ''
        })

    m3_metrics = compute_metrics(y_true, m3_predictions, "M3 LLM Trajectory Reasoning")

    m3_eval_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'm3_evaluation_results.json')
    with open(m3_eval_file, 'w', encoding='utf-8') as f:
        json.dump({'metrics': m3_metrics, 'predictions': m3_results_list}, f, indent=2)

    print(f"[OK] M3 Completed: Valid = {m3_metrics['valid_count']}/89 | Macro F1 = {m3_metrics['macro_f1']} (Accuracy: {m3_metrics['accuracy']})", flush=True)

    # -------------------------------------------------------------------------
    # METHOD 4: M4 HYBRID MODEL
    # -------------------------------------------------------------------------
    print("\n" + "=" * 50)
    print("EVALUATING METHOD 4: M4 HYBRID MODEL")
    print("=" * 50)

    m4_predictions = []
    m4_results_list = []

    for item in prefix_trajectories:
        res = assess_hybrid_trajectory(item['trajectory_data'])
        pred_state = res.get('state', 'UNCERTAIN')
        m4_predictions.append(pred_state)
        m4_results_list.append({
            'prefix_id': item['prefix_id'],
            'reference_label': item['reference_label'],
            'predicted_state': pred_state,
            'confidence': res.get('confidence', 0.0),
            'reasoning': res.get('reasoning', '')
        })

    m4_metrics = compute_metrics(y_true, m4_predictions, "M4 Hybrid Model")

    m4_eval_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'm4_evaluation_results.json')
    with open(m4_eval_file, 'w', encoding='utf-8') as f:
        json.dump({'metrics': m4_metrics, 'predictions': m4_results_list}, f, indent=2)

    print(f"[OK] M4 Completed: Macro F1 = {m4_metrics['macro_f1']} (Accuracy: {m4_metrics['accuracy']})", flush=True)

    # -------------------------------------------------------------------------
    # GENERATE DETAILED COMPARISON CSV
    # -------------------------------------------------------------------------
    detailed_csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'struggle_methods_evaluation_detailed.csv')
    fieldnames = [
        'Prefix ID', 'Session ID', 'Prefix Number', 'Human Reference Label',
        'M1 Prediction', 'M2 Prediction', 'M3 Prediction', 'M4 Prediction', 'M3 Status/Error'
    ]

    detailed_rows = []
    for i, item in enumerate(prefix_trajectories):
        detailed_rows.append({
            'Prefix ID': item['prefix_id'],
            'Session ID': item['session_id'],
            'Prefix Number': item['prefix_number'],
            'Human Reference Label': y_true[i],
            'M1 Prediction': m1_predictions[i],
            'M2 Prediction': m2_predictions[i],
            'M3 Prediction': m3_predictions[i],
            'M4 Prediction': m4_predictions[i],
            'M3 Status/Error': m3_status_list[i]
        })

    with open(detailed_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(detailed_rows)

    print(f"\nSaved detailed comparison CSV to: {detailed_csv_path}")

    # Determine Best Performing Method based on Macro F1
    all_metrics = [m1_metrics, m2_metrics, m3_metrics, m4_metrics]
    best_method = max(all_metrics, key=lambda m: (m['macro_f1'], m['valid_count']))

    summary_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'struggle_methods_comparison_summary.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            'best_method': best_method['method_name'],
            'best_macro_f1': best_method['macro_f1'],
            'm1_metrics': m1_metrics,
            'm2_metrics': m2_metrics,
            'm3_metrics': m3_metrics,
            'm4_metrics': m4_metrics
        }, f, indent=2)

    print("\n" + "=" * 80)
    print("EVALUATION COMPLETED SUCCESSFULLY")
    print(f"Best Performing Method (by Macro F1): {best_method['method_name']} (Macro F1 = {best_method['macro_f1']})")
    print("=" * 80)

if __name__ == '__main__':
    run_evaluation()
