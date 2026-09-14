import hashlib
import json
import csv
import io
from typing import List, Dict, Tuple, Optional, Any
from django.utils import timezone
from hints.models import Attempt
from struggle_analysis.trajectory import build_trajectory

ANNOTATION_PROTOCOL_VERSION = "TASK_2F_B_PROTOCOL_V1"
ALLOWED_LABELS = {"PRODUCTIVE", "UNPRODUCTIVE", "UNCERTAIN"}
ALLOWED_CONFIDENCE = {"LOW", "MEDIUM", "HIGH"}
SALT = "struggle_research_salt_v1"


def pseudonymize_id(raw_id: str, prefix: str = "anon") -> str:
    """
    Generates a privacy-preserving pseudonymous hash for student or problem IDs.
    """
    if not raw_id:
        return f"{prefix}_unknown"
    if str(raw_id).startswith("anon_"):
        return str(raw_id)
    hashed = hashlib.sha256(f"{SALT}_{raw_id}".encode('utf-8')).hexdigest()[:12]
    return f"{prefix}_{hashed}"


def validate_annotation_record(record: dict) -> Tuple[bool, List[str]]:
    """
    Validates a single human annotation record against protocol rules.
    """
    errors = []
    required_keys = ["annotation_id", "student_id", "problem_id", "prefix_length", "label", "confidence", "annotator_id", "annotation_version"]
    for key in required_keys:
        if key not in record or record[key] is None or record[key] == "":
            errors.append(f"Missing required field: '{key}'")

    if record.get("label") not in ALLOWED_LABELS:
        errors.append(f"Invalid label '{record.get('label')}'. Must be one of {sorted(list(ALLOWED_LABELS))}")

    if record.get("confidence") not in ALLOWED_CONFIDENCE:
        errors.append(f"Invalid confidence '{record.get('confidence')}'. Must be one of {sorted(list(ALLOWED_CONFIDENCE))}")

    prefix_len = record.get("prefix_length")
    if not isinstance(prefix_len, int) or prefix_len <= 0:
        errors.append("Field 'prefix_length' must be a positive integer > 0")

    # Verify no model predictions are stored inside human record label
    for forbidden_key in ["model_prediction", "rule_output", "llm_output", "hybrid_output"]:
        if forbidden_key in record:
            errors.append(f"Forbidden model field '{forbidden_key}' found inside human annotation record")

    return (len(errors) == 0, errors)


def generate_prefix_annotation_material(user_id: str, problem_id: str, prefix_length: int, session_id: str = None) -> dict:
    """
    Generates privacy-preserving annotation material for a trajectory prefix strictly up to attempt t.
    Strips all future attempts (At+1..AN) and ALL model predictions (M1..M4).
    """
    full_trajectory = build_trajectory(user_id, problem_id, session_id=session_id)
    attempts = full_trajectory.get("attempts", [])
    
    if not attempts:
        raise ValueError(f"No trajectory attempts found for user '{user_id}' and problem '{problem_id}'.")

    # Clamp prefix length to actual available attempts
    t = min(max(1, prefix_length), len(attempts))
    prefix_attempts = attempts[:t]

    # Build prefix-isolated attempt payloads without future information or model outputs
    clean_attempts = []
    for idx, att in enumerate(prefix_attempts, start=1):
        clean_attempts.append({
            "step": idx,
            "attempt_id": att.get("attempt_id"),
            "timestamp": att.get("created_at"),
            "time_delta_seconds": att.get("time_delta"),
            "status": att.get("status"),
            "code": att.get("code"),
            "tests_passed": att.get("tests_passed"),
            "tests_total": att.get("tests_total"),
            "test_pass_ratio": att.get("tests_pass_ratio"),
            "errors": att.get("errors", []),
            "interaction_type": att.get("interaction_type", "CODE_CHANGE"),
            "observable_signals": att.get("observable_signals", {})
        })

    mat = {
        "material_id": f"mat_{pseudonymize_id(user_id)}_{pseudonymize_id(problem_id)}_t{t}",
        "student_id": pseudonymize_id(user_id, prefix="anon_user"),
        "problem_id": pseudonymize_id(problem_id, prefix="anon_prob"),
        "prefix_length": t,
        "total_available_attempts_in_db": len(attempts),
        "status": "awaiting_human_annotation",
        "attempts": clean_attempts,
        "annotation_protocol_version": ANNOTATION_PROTOCOL_VERSION
    }
    if session_id:
        mat["session_id"] = session_id
    return mat


from struggle_analysis.config import is_research_valid_session

def generate_pilot_annotation_batch(max_trajectories: int = 10) -> dict:
    """
    Generates a pilot annotation batch from real database user-problem sessions.
    Filters at the SESSION level using is_research_valid_session.
    Does NOT fabricate labels or run model predictions.
    """
    distinct_session_ids = (
        Attempt.objects.exclude(session_id__isnull=True)
        .exclude(session_id="")
        .values_list('session_id', flat=True)
        .distinct()
    )
    
    valid_sessions = []
    for s_id in distinct_session_ids:
        attempts = list(Attempt.objects.filter(session_id=s_id).order_by('created_at', 'id'))
        if is_research_valid_session(attempts):
            valid_sessions.append((s_id, attempts))
            if len(valid_sessions) >= max_trajectories:
                break

    batch_materials = []
    for s_id, attempts in valid_sessions:
        u_id = attempts[0].user_id
        prob_obj = attempts[0].problem
        p_id_str = prob_obj.problem_id if getattr(prob_obj, 'problem_id', None) else str(prob_obj.id)
        try:
            traj = build_trajectory(u_id, prob_obj, session_id=s_id)
            n_attempts = len(traj.get("attempts", []))
            if n_attempts > 0:
                mat = generate_prefix_annotation_material(u_id, p_id_str, prefix_length=n_attempts, session_id=s_id)
                batch_materials.append(mat)
        except Exception:
            continue

    return {
        "batch_id": f"batch_pilot_{timezone.now().strftime('%Y%m%d_%H%M%S')}",
        "protocol_version": ANNOTATION_PROTOCOL_VERSION,
        "trajectory_count": len(batch_materials),
        "status": "awaiting_human_annotation",
        "materials": batch_materials
    }


def export_annotation_batch(batch_data: dict, format_type: str = "json") -> str:
    """
    Exports annotation batch or records to JSON or CSV string.
    """
    if format_type.lower() == "json":
        return json.dumps(batch_data, indent=2)
    elif format_type.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Check if batch_data contains records or materials
        records = batch_data.get("records") or batch_data.get("materials") or []
        if records:
            header = list(records[0].keys())
            writer.writerow(header)
            for rec in records:
                writer.writerow([json.dumps(rec[k]) if isinstance(rec[k], (dict, list)) else rec[k] for k in header])
        return output.getvalue()
    else:
        raise ValueError(f"Unsupported format_type: '{format_type}'. Must be 'json' or 'csv'.")


def import_annotation_batch(data_str: str, format_type: str = "json") -> List[dict]:
    """
    Imports and validates human annotation records from JSON or CSV data string.
    """
    imported_records = []
    if format_type.lower() == "json":
        parsed = json.loads(data_str)
        if isinstance(parsed, dict) and "records" in parsed:
            raw_list = parsed["records"]
        elif isinstance(parsed, list):
            raw_list = parsed
        else:
            raw_list = [parsed]
            
        for rec in raw_list:
            valid, errs = validate_annotation_record(rec)
            if not valid:
                raise ValueError(f"Annotation record validation failed for id '{rec.get('annotation_id')}': {errs}")
            imported_records.append(rec)
            
    elif format_type.lower() == "csv":
        reader = csv.DictReader(io.StringIO(data_str))
        for row in reader:
            # Parse prefix_length if string
            if "prefix_length" in row:
                row["prefix_length"] = int(row["prefix_length"])
            valid, errs = validate_annotation_record(row)
            if not valid:
                raise ValueError(f"CSV Annotation record validation failed: {errs}")
            imported_records.append(dict(row))
    else:
        raise ValueError(f"Unsupported format_type: '{format_type}'. Must be 'json' or 'csv'.")

    return imported_records
