import os
import sys
import json
import csv
import time
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
from struggle_analysis.llm_assessment import assess_trajectory_with_llm

LABELS = ['PRODUCTIVE', 'UNPRODUCTIVE', 'UNCERTAIN']
TARGET_MODEL = "meta-llama/llama-3.1-8b-instruct"

def run_m3_full_evaluation():
    print("=" * 80)
    print("STARTING M3 LLM FULL EVALUATION (ALL 89 PREFIXES)")
    print(f"Target Model: {TARGET_MODEL}")
    print("=" * 80)

    # 1. Load Ground Truth Human Reference Labels
    gt_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'human_annotations_with_final_label.json')
    if not os.path.exists(gt_json_path):
        raise FileNotFoundError(f"Reference file not found: {gt_json_path}")

    with open(gt_json_path, 'r', encoding='utf-8') as f:
        gt_data = json.load(f)

    all_prefix_records = gt_data.get('records', [])
    print(f"Loaded {len(all_prefix_records)} ground truth reference prefixes.")

    # 2. Load Existing Batch 1 Cache to preserve the 17 successful predictions
    batch1_cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'm3_batch1_cache.json')
    full_cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'm3_full_llm_cache.json')
    
    m3_cache = {}

    if os.path.exists(batch1_cache_path):
        try:
            with open(batch1_cache_path, 'r', encoding='utf-8') as f:
                b1_data = json.load(f)
                for k, v in b1_data.items():
                    if not v.get('error') and v.get('state') in LABELS:
                        m3_cache[k] = v
            print(f"Loaded {len(m3_cache)} valid successful predictions from Batch 1 cache.")
        except Exception as e:
            print(f"Warning loading Batch 1 cache: {e}")

    if os.path.exists(full_cache_path):
        try:
            with open(full_cache_path, 'r', encoding='utf-8') as f:
                full_data = json.load(f)
                for k, v in full_data.items():
                    if not v.get('error') and v.get('state') in LABELS:
                        m3_cache[k] = v
            print(f"Combined total cached valid predictions: {len(m3_cache)}.")
        except Exception as e:
            print(f"Warning loading Full cache: {e}")

    # Pre-fetch all attempts for unique valid sessions in 1 fast DB query
    unique_sids = set(rec['session_id'] for rec in all_prefix_records)
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

    prefix_trajectories = []
    y_true = []

    for idx, rec in enumerate(all_prefix_records, 1):
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

    print(f"Built trajectory prefixes for all {len(prefix_trajectories)} items.", flush=True)

    # -------------------------------------------------------------------------
    # RUN M3 LLM EVALUATION FOR ALL 89 PREFIXES
    # -------------------------------------------------------------------------
    m3_predictions = []
    m3_results_list = []
    m3_status_list = []
    failed_prefixes_list = []

    for idx, item in enumerate(prefix_trajectories, 1):
        pkey = item['prefix_id']

        if pkey in m3_cache and not m3_cache[pkey].get('error') and m3_cache[pkey].get('state') in LABELS:
            res = m3_cache[pkey]
            pred_state = res.get('state')
            err_info = None
            print(f"[{idx}/89] M3 {pkey}: Cached -> {pred_state} (Conf: {res.get('confidence')})", flush=True)
        else:
            retries = 3
            res = None
            err_info = None

            for attempt_num in range(1, retries + 1):
                try:
                    res = assess_trajectory_with_llm(
                        item['trajectory_data'],
                        model_name=TARGET_MODEL,
                        strict_model_pinning=True
                    )
                    if res.get('error'):
                        err_info = res.get('error')
                        print(f"[{idx}/89] M3 {pkey} Attempt {attempt_num} API Error: {err_info}", flush=True)
                        if "402" in str(err_info) or "429" in str(err_info) or "Insufficient credits" in str(err_info):
                            break
                        time.sleep(2 * attempt_num)
                    else:
                        break
                except Exception as e:
                    err_info = str(e)
                    print(f"[{idx}/89] M3 {pkey} Attempt {attempt_num} Exception: {err_info}", flush=True)
                    time.sleep(2 * attempt_num)

            if res and not res.get('error') and res.get('state') in LABELS:
                pred_state = res.get('state')
                m3_cache[pkey] = res
                with open(full_cache_path, 'w', encoding='utf-8') as f:
                    json.dump(m3_cache, f, indent=2)
                print(f"[{idx}/89] M3 {pkey}: Success -> {pred_state} (Conf: {res.get('confidence')})", flush=True)
            else:
                pred_state = "FAILED/NO_PREDICTION"
                failed_prefixes_list.append((pkey, err_info))
                print(f"[{idx}/89] M3 {pkey}: FAILED -> {err_info}", flush=True)

        m3_predictions.append(pred_state)
        m3_status_list.append(err_info if err_info else "OK")
        m3_results_list.append({
            'prefix_id': pkey,
            'session_id': item['session_id'],
            'prefix_number': item['prefix_number'],
            'reference_label': item['reference_label'],
            'predicted_state': pred_state,
            'status': 'SUCCESS' if pred_state in LABELS else 'FAILED',
            'model_used': TARGET_MODEL,
            'confidence': res.get('confidence', 0.0) if res else 0.0,
            'reasoning': res.get('reasoning', '') if res else '',
            'error_info': err_info
        })

    # -------------------------------------------------------------------------
    # COMPUTE METRICS OVER VALID PREDICTIONS FOR ALL 89 PREFIXES
    # -------------------------------------------------------------------------
    valid_pairs = [(t, p) for t, p in zip(y_true, m3_predictions) if p in LABELS]
    valid_count = len(valid_pairs)
    failed_count = len(m3_predictions) - valid_count

    if valid_count > 0:
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
    else:
        acc = bal_acc = prec_macro = rec_macro = macro_f1 = prod_f1 = unprod_f1 = uncert_f1 = 0.0
        cm = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

    metrics_summary = {
        'method_name': 'M3 LLM Trajectory Reasoning (Full Dataset: All 89 Prefixes)',
        'target_model': TARGET_MODEL,
        'total_evaluated_prefixes': 89,
        'successful_predictions': valid_count,
        'failed_predictions': failed_count,
        'failed_prefixes': [p[0] for p in failed_prefixes_list],
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

    # Save evaluation JSON
    eval_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'm3_full_evaluation_results.json')
    with open(eval_json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'metrics': metrics_summary,
            'predictions': m3_results_list
        }, f, indent=2)

    # Save detailed CSV
    detailed_csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'm3_full_detailed_results.csv')
    fieldnames = [
        'Prefix ID', 'Session ID', 'Prefix Number', 'Human Reference Label',
        'M3 Prediction', 'Status', 'Model Used', 'Confidence', 'Reasoning', 'Error Info'
    ]

    detailed_rows = []
    for r in m3_results_list:
        detailed_rows.append({
            'Prefix ID': r['prefix_id'],
            'Session ID': r['session_id'],
            'Prefix Number': r['prefix_number'],
            'Human Reference Label': r['reference_label'],
            'M3 Prediction': r['predicted_state'],
            'Status': r['status'],
            'Model Used': r['model_used'],
            'Confidence': r['confidence'],
            'Reasoning': r['reasoning'],
            'Error Info': r['error_info'] if r['error_info'] else ''
        })

    with open(detailed_csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(detailed_rows)

    print("\n" + "=" * 80)
    print("M3 FULL (ALL 89 PREFIXES) EVALUATION COMPLETED")
    print(f"Model Used: {TARGET_MODEL}")
    print(f"Successful Predictions: {valid_count} / 89")
    print(f"Failed Predictions: {failed_count} / 89")
    if failed_prefixes_list:
        print(f"Failed Prefixes: {[p[0] for p in failed_prefixes_list]}")
    print(f"Accuracy: {acc}")
    print(f"Balanced Accuracy: {bal_acc}")
    print(f"Macro Precision: {prec_macro}")
    print(f"Macro Recall: {rec_macro}")
    print(f"Macro F1 Score: {macro_f1}")
    print(f"Per-Class F1s -> Productive: {prod_f1} | Unproductive: {unprod_f1} | Uncertain: {uncert_f1}")
    print(f"Confusion Matrix [PRODUCTIVE, UNPRODUCTIVE, UNCERTAIN]:\n{cm}")
    print(f"Saved cache to: {full_cache_path}")
    print(f"Saved evaluation JSON to: {eval_json_path}")
    print(f"Saved detailed CSV to: {detailed_csv_path}")
    print("=" * 80)

if __name__ == '__main__':
    run_m3_full_evaluation()
