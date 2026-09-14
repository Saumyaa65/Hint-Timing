import random
from typing import List, Dict, Tuple, Any

LABELS = ["PRODUCTIVE", "UNPRODUCTIVE", "UNCERTAIN"]


def evaluate_model_performance(human_records: List[dict], model_predictions: List[dict]) -> dict:
    """
    Evaluates model predictions (M1, M2, M3, or M4) against Human Reference annotations.
    Explicitly fails/notifies if human reference annotations are missing, preventing fabricated metrics.
    """
    if not human_records:
        return {
            "status": "no_reference_labels",
            "message": "Evaluation aborted: No human reference annotations exist. Empirical metrics cannot be computed without human ground truth."
        }

    # Index model predictions by (student_id, problem_id, prefix_length)
    model_map = {}
    for p in model_predictions:
        key = (p["student_id"], p["problem_id"], p["prefix_length"])
        model_map[key] = p.get("state") or p.get("label")

    paired_ref = []
    paired_pred = []

    for h in human_records:
        key = (h["student_id"], h["problem_id"], h["prefix_length"])
        if key in model_map and model_map[key] is not None:
            paired_ref.append(h["label"])
            paired_pred.append(model_map[key])

    N = len(paired_ref)
    if N == 0:
        return {
            "status": "no_matched_pairs",
            "message": "Evaluation aborted: Zero trajectory prefix matches between human reference annotations and model predictions."
        }

    # Confusion matrix: rows = Reference (Human), cols = Prediction (Model)
    matrix = {l1: {l2: 0 for l2 in LABELS} for l1 in LABELS}
    ref_counts = {l: 0 for l in LABELS}
    pred_counts = {l: 0 for l in LABELS}
    correct_count = 0

    for r, p in zip(paired_ref, paired_pred):
        if r in matrix and p in matrix[r]:
            matrix[r][p] += 1
        ref_counts[r] = ref_counts.get(r, 0) + 1
        pred_counts[p] = pred_counts.get(p, 0) + 1
        if r == p:
            correct_count += 1

    accuracy = correct_count / N

    # Per-class & Macro metrics
    per_class = {}
    recalls = []
    precisions = []
    f1s = []

    for l in LABELS:
        tp = matrix[l][l]
        fn = sum(matrix[l][l2] for l2 in LABELS if l2 != l)
        fp = sum(matrix[l1][l] for l1 in LABELS if l1 != l)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0

        per_class[l] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "support": ref_counts[l]
        }
        precisions.append(prec)
        recalls.append(rec)
        f1s.append(f1)

    macro_precision = sum(precisions) / len(LABELS)
    macro_recall = sum(recalls) / len(LABELS)
    macro_f1 = sum(f1s) / len(LABELS)
    balanced_accuracy = macro_recall  # Mean of per-class recall

    return {
        "status": "success",
        "sample_size": N,
        "accuracy": round(accuracy, 4),
        "balanced_accuracy": round(balanced_accuracy, 4),
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class": per_class,
        "confusion_matrix": matrix
    }


def split_students_train_test(records: List[dict], test_ratio: float = 0.3, seed: int = 42) -> Tuple[List[dict], List[dict]]:
    """
    Splits trajectory records into train and test sets strictly grouped by student_id.
    Prevents student-level data leakage across train/test splits.
    """
    if not records:
        return ([], [])

    unique_students = sorted(list(set(r["student_id"] for r in records)))
    rng = random.Random(seed)
    shuffled_students = list(unique_students)
    rng.shuffle(shuffled_students)

    n_test = max(1, int(len(shuffled_students) * test_ratio)) if len(shuffled_students) > 1 else 0
    test_students = set(shuffled_students[:n_test])
    train_students = set(shuffled_students[n_test:])

    train_records = [r for r in records if r["student_id"] in train_students]
    test_records = [r for r in records if r["student_id"] in test_students]

    return (train_records, test_records)
