import math
from typing import List, Dict, Tuple, Any

LABELS = ["PRODUCTIVE", "UNPRODUCTIVE", "UNCERTAIN"]


def calculate_cohens_kappa(records_annotator_a: List[dict], records_annotator_b: List[dict]) -> dict:
    """
    Calculates Cohen's Kappa for 2 annotators rating identical trajectory prefixes.
    Treats UNCERTAIN as a legitimate 3rd primary class.
    """
    map_a = {}
    for r in records_annotator_a:
        key = (r["student_id"], r["problem_id"], r["prefix_length"])
        map_a[key] = r["label"]

    paired_labels_a = []
    paired_labels_b = []
    
    for r in records_annotator_b:
        key = (r["student_id"], r["problem_id"], r["prefix_length"])
        if key in map_a:
            paired_labels_a.append(map_a[key])
            paired_labels_b.append(r["label"])

    N = len(paired_labels_a)
    if N == 0:
        return {
            "paired_count": 0,
            "cohens_kappa": 0.0,
            "raw_agreement_pct": 0.0,
            "confusion_matrix": {l1: {l2: 0 for l2 in LABELS} for l1 in LABELS},
            "per_class_counts_a": {l: 0 for l in LABELS},
            "per_class_counts_b": {l: 0 for l in LABELS},
            "message": "No matching trajectory prefix pairs found between annotators."
        }

    # Confusion matrix: rows = Annotator A, cols = Annotator B
    matrix = {l1: {l2: 0 for l2 in LABELS} for l1 in LABELS}
    counts_a = {l: 0 for l in LABELS}
    counts_b = {l: 0 for l in LABELS}
    agreed_count = 0

    for la, lb in zip(paired_labels_a, paired_labels_b):
        matrix[la][lb] += 1
        counts_a[la] += 1
        counts_b[lb] += 1
        if la == lb:
            agreed_count += 1

    po = agreed_count / N

    # Chance agreement pe
    pe = sum((counts_a[l] / N) * (counts_b[l] / N) for l in LABELS)

    if pe == 1.0:
        kappa = 1.0
    else:
        kappa = (po - pe) / (1.0 - pe)

    return {
        "paired_count": N,
        "cohens_kappa": round(kappa, 4),
        "raw_agreement_pct": round(po * 100.0, 2),
        "chance_agreement_pe": round(pe, 4),
        "confusion_matrix": matrix,
        "per_class_counts_a": counts_a,
        "per_class_counts_b": counts_b
    }


def calculate_fleiss_kappa(ratings_matrix: List[Dict[str, int]]) -> dict:
    """
    Calculates Fleiss' Kappa for arbitrary number of annotators rating trajectory prefixes.
    ratings_matrix is a list of category count dicts per subject:
    e.g. [{"PRODUCTIVE": 2, "UNPRODUCTIVE": 1, "UNCERTAIN": 0}, ...]
    """
    N = len(ratings_matrix)
    if N == 0:
        return {"subjects_count": 0, "fleiss_kappa": 0.0}

    # Total annotators per subject n
    first_sub = ratings_matrix[0]
    n = sum(first_sub.values())
    if n <= 1:
        return {"subjects_count": N, "fleiss_kappa": 1.0, "message": "Fewer than 2 annotators per subject"}

    k = len(LABELS)
    pj = {l: 0.0 for l in LABELS}

    for sub in ratings_matrix:
        for l in LABELS:
            pj[l] += sub.get(l, 0)

    total_ratings = N * n
    for l in LABELS:
        pj[l] /= total_ratings

    Pi_list = []
    for sub in ratings_matrix:
        sum_sq = sum(sub.get(l, 0) ** 2 for l in LABELS)
        Pi = (sum_sq - n) / (n * (n - 1))
        Pi_list.append(Pi)

    P_bar = sum(Pi_list) / N
    Pe_bar = sum(pj[l] ** 2 for l in LABELS)

    if Pe_bar == 1.0:
        kappa = 1.0
    else:
        kappa = (P_bar - Pe_bar) / (1.0 - Pe_bar)

    return {
        "subjects_count": N,
        "annotators_per_subject": n,
        "fleiss_kappa": round(kappa, 4),
        "p_bar": round(P_bar, 4),
        "pe_bar": round(Pe_bar, 4)
    }
