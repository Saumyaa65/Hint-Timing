import difflib
import re
from django.utils import timezone
from hints.models import Attempt, Problem


def normalize_code(code: str) -> str:
    """Normalize code by stripping whitespace and empty lines for comparison."""
    if not code:
        return ""
    return "\n".join(line.strip() for line in code.splitlines() if line.strip())


def normalize_error(error_text: str) -> str:
    """
    Normalize error messages by stripping dynamic line numbers, specific memory addresses,
    and extra whitespace to allow similarity calculation.
    """
    if not error_text:
        return ""
    text = re.sub(r'line \d+', '', error_text, flags=re.IGNORECASE)
    text = re.sub(r'0x[0-9a-fA-F]+', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip().lower()


def extract_attempt_info(attempt: Attempt, index: int) -> dict:
    """
    Extract raw attempt details preserved for research analysis.
    """
    eval_details = attempt.evaluation_details or {}
    results = eval_details.get('results') or []
    errors = eval_details.get('errors') or []

    tests_passed = sum(1 for r in results if r.get('passed'))
    total_tests = len(results)
    tests_failed = total_tests - tests_passed if total_tests > 0 else 0
    pass_rate = round(tests_passed / total_tests, 4) if total_tests > 0 else 0.0

    first_error_msg = ""
    if errors:
        first_error_msg = errors[0].get('message', '')
    elif not results and attempt.status != 'success':
        first_error_msg = "Execution/Compilation failed"

    return {
        "index": index,
        "attempt_id": attempt.id,
        "user_id": attempt.user_id,
        "problem_id": attempt.problem.id,
        "timestamp": attempt.created_at.isoformat() if attempt.created_at else None,
        "created_at_dt": attempt.created_at,
        "status": attempt.status,
        "language": attempt.language,
        "code": attempt.code or "",
        "execution_time": attempt.execution_time or "0.00s",
        "tests_passed": tests_passed,
        "tests_failed": tests_failed,
        "total_tests": total_tests,
        "pass_rate": pass_rate,
        "error_message": first_error_msg,
        "normalized_error": normalize_error(first_error_msg),
        "evaluation_details": eval_details,
    }


def categorize_code_change(similarity: float) -> str:
    """Categorize code change magnitude using similarity threshold ranges."""
    if similarity >= 0.98:
        return "none"
    elif similarity >= 0.90:
        return "almost_identical"
    elif similarity >= 0.70:
        return "small_modification"
    else:
        return "substantial_modification"


def check_structural_change(code1: str, code2: str) -> bool:
    """
    Approximate proxy for structural pattern changes based on keyword/control structure
    presence and substantial line count changes.
    """
    lines1 = [l.strip() for l in code1.splitlines() if l.strip()]
    lines2 = [l.strip() for l in code2.splitlines() if l.strip()]

    line_ratio_diff = abs(len(lines1) - len(lines2)) / max(len(lines1), 1)
    if line_ratio_diff > 0.35:
        return True

    keywords = {'for', 'while', 'if', 'else', 'def', 'class', 'return', 'function', 'import', 'try', 'catch', 'switch'}
    kw1 = {w for line in lines1 for w in line.split() if w in keywords}
    kw2 = {w for line in lines2 for w in line.split() if w in keywords}

    return kw1 != kw2


def compute_transition(
    prev: dict,
    curr: dict,
    prev_transitions: list,
    first_dt=None,
    all_prior_attempt_codes=None
) -> dict:
    """
    Compute features for transition between consecutive attempts (prev -> curr).
    """
    # E. TEMPORAL BEHAVIOUR
    if prev.get("created_at_dt") and curr.get("created_at_dt"):
        time_delta = max(0.0, (curr["created_at_dt"] - prev["created_at_dt"]).total_seconds())
    else:
        time_delta = 0.0

    initial_dt = first_dt or prev.get("created_at_dt")
    if initial_dt and curr.get("created_at_dt"):
        total_duration = max(0.0, (curr["created_at_dt"] - initial_dt).total_seconds())
    else:
        total_duration = 0.0

    curr_index = curr["index"]
    attempt_freq = round((curr_index / (total_duration / 60.0)), 2) if total_duration > 1.0 else round(float(curr_index), 2)

    if curr["status"] != 'success':
        prev_consec = prev_transitions[-1]["temporal"]["consecutive_failed_attempts"] if prev_transitions else (1 if prev["status"] != 'success' else 0)
        consecutive_failures = prev_consec + 1
    else:
        consecutive_failures = 0

    struggle_duration = 0.0
    if prev_transitions:
        struggle_duration = prev_transitions[-1]["temporal"]["struggle_duration"]
        if curr["status"] != 'success':
            struggle_duration += time_delta
    elif prev["status"] != 'success' and curr["status"] != 'success':
        struggle_duration = time_delta

    temporal = {
        "time_delta": round(time_delta, 2),
        "total_trajectory_duration": round(total_duration, 2),
        "attempt_frequency_per_min": attempt_freq,
        "attempt_number": curr_index,
        "consecutive_failed_attempts": consecutive_failures,
        "struggle_duration": round(struggle_duration, 2),
    }

    # A. CODE EVOLUTION
    norm_prev_code = normalize_code(prev["code"])
    norm_curr_code = normalize_code(curr["code"])
    code_seq = difflib.SequenceMatcher(None, norm_prev_code, norm_curr_code)
    code_sim = round(code_seq.ratio(), 4)
    code_change_ratio = round(1.0 - code_sim, 4)
    repeated_code = code_sim >= 0.98
    changed_code = not repeated_code
    magnitude = categorize_code_change(code_sim)

    code_evolution = {
        "code_similarity": code_sim,
        "code_change_ratio": code_change_ratio,
        "repeated_code": repeated_code,
        "changed_code": changed_code,
        "code_change_magnitude": magnitude,
    }

    # B. ERROR EVOLUTION
    prev_err = prev["normalized_error"]
    curr_err = curr["normalized_error"]
    has_prev_err = bool(prev_err)
    has_curr_err = bool(curr_err)

    if has_prev_err and has_curr_err:
        err_seq = difflib.SequenceMatcher(None, prev_err, curr_err)
        err_sim = round(err_seq.ratio(), 4)
    elif not has_prev_err and not has_curr_err:
        err_sim = 1.0
    else:
        err_sim = 0.0

    repeated_error = has_prev_err and has_curr_err and err_sim >= 0.85
    error_changed = (has_prev_err and has_curr_err and err_sim < 0.85) or (has_prev_err != has_curr_err)
    error_resolved = has_prev_err and not has_curr_err
    error_introduced = not has_prev_err and has_curr_err

    error_evolution = {
        "prev_normalized_error": prev_err,
        "curr_normalized_error": curr_err,
        "error_similarity": err_sim,
        "repeated_error": repeated_error,
        "error_changed": error_changed,
        "error_resolved": error_resolved,
        "error_introduced": error_introduced,
    }

    # C. PERFORMANCE / TEST PROGRESSION
    tests_passed_prev = prev["tests_passed"]
    tests_passed_curr = curr["tests_passed"]
    tests_failed_prev = prev["tests_failed"]
    tests_failed_curr = curr["tests_failed"]
    total_tests = max(prev["total_tests"], curr["total_tests"])
    pass_rate_prev = prev["pass_rate"]
    pass_rate_curr = curr["pass_rate"]

    delta_tests_passed = tests_passed_curr - tests_passed_prev
    delta_pass_rate = round(pass_rate_curr - pass_rate_prev, 4)

    if delta_tests_passed > 0 or delta_pass_rate > 0:
        trend = "improved"
    elif delta_tests_passed < 0 or delta_pass_rate < 0:
        trend = "regressed"
    else:
        trend = "unchanged"

    performance = {
        "tests_passed_prev": tests_passed_prev,
        "tests_passed_curr": tests_passed_curr,
        "tests_failed_prev": tests_failed_prev,
        "tests_failed_curr": tests_failed_curr,
        "total_tests": total_tests,
        "pass_rate_prev": pass_rate_prev,
        "pass_rate_curr": pass_rate_curr,
        "delta_tests_passed": delta_tests_passed,
        "delta_pass_rate": delta_pass_rate,
        "performance_trend": trend,
    }

    # D. EXPLORATION / APPROACH CHANGE
    structural_changed = check_structural_change(norm_prev_code, norm_curr_code)
    is_approach_change = magnitude == "substantial_modification" or (code_sim < 0.70 and structural_changed)
    exploration_score = round(min(1.0, (1.0 - code_sim) * 0.6 + (0.4 if error_changed else 0.0)), 4)

    exploration = {
        "is_approach_change": is_approach_change,
        "structural_pattern_changed": structural_changed,
        "exploration_score": exploration_score,
    }

    # F. REPETITION / STAGNATION & INTERACTION TAXONOMY
    repeated_test_outcome = (tests_passed_curr == tests_passed_prev) and (tests_failed_curr == tests_failed_prev)
    
    prior_codes = all_prior_attempt_codes or []
    reverts_to_prior_code = norm_curr_code in prior_codes

    # Research Audit Refinement:
    # A repeated state requires COMPLETE state stagnation across code AND error AND performance!
    is_code_stagnant = repeated_code or reverts_to_prior_code
    is_error_stagnant = repeated_error or (not has_prev_err and not has_curr_err)
    is_outcome_stagnant = repeated_test_outcome and (trend == "unchanged")

    repeated_state = is_code_stagnant and is_error_stagnant and is_outcome_stagnant

    # Interaction Type Taxonomy:
    # Distinguishes REPEAT_EXECUTION (button re-click with identical code and outcome)
    # from OUTCOME_CHANGE (identical code but execution status/tests changed)
    # and CODE_CHANGE (student modified solution code).
    if not changed_code:
        if error_changed or not repeated_test_outcome or trend != "unchanged":
            interaction_type = "OUTCOME_CHANGE"
        else:
            interaction_type = "REPEAT_EXECUTION"
    else:
        interaction_type = "CODE_CHANGE"

    if prev_transitions:
        prev_consec_stagnant = prev_transitions[-1]["repetition"]["stagnation_length"]
    else:
        prev_consec_stagnant = 0

    if interaction_type == "REPEAT_EXECUTION" or repeated_state:
        stagnation_length = prev_consec_stagnant + 1
    else:
        stagnation_length = 0

    repetition = {
        "interaction_type": interaction_type,
        "repeated_code": repeated_code,
        "reverts_to_prior_code": reverts_to_prior_code,
        "repeated_error": repeated_error,
        "repeated_test_outcome": repeated_test_outcome,
        "repeated_state": repeated_state,
        "consecutive_unchanged_attempts": stagnation_length,
        "stagnation_length": stagnation_length,
    }

    return {
        "from_attempt_index": prev["index"],
        "to_attempt_index": curr["index"],
        "from_attempt_id": prev["attempt_id"],
        "to_attempt_id": curr["attempt_id"],
        "temporal": temporal,
        "code_evolution": code_evolution,
        "error_evolution": error_evolution,
        "performance": performance,
        "exploration": exploration,
        "repetition": repetition,
    }


def build_trajectory(user_id: str, problem_id_or_obj, max_attempts: int = None, session_id: str = None) -> dict:
    """
    Construct a complete research trajectory representation for USER + PROBLEM.
    Reconstructed chronologically from raw Attempt database records.
    
    Supports online prefix temporal validity via max_attempts parameter (1 ... t)
    and session boundary isolation via optional session_id parameter.
    """
    if isinstance(problem_id_or_obj, Problem):
        problem = problem_id_or_obj
    else:
        try:
            problem = Problem.objects.get(problem_id=str(problem_id_or_obj))
        except Problem.DoesNotExist:
            try:
                problem = Problem.objects.get(pk=problem_id_or_obj)
            except (Problem.DoesNotExist, ValueError):
                return {
                    "error": f"Problem with ID {problem_id_or_obj} not found",
                    "user_id": user_id,
                    "problem_id": str(problem_id_or_obj),
                    "trajectory_length": 0,
                    "attempts": [],
                    "transitions": [],
                    "trajectory_summary": {}
                }

    attempt_qs = Attempt.objects.filter(
        user_id=user_id,
        problem=problem
    ).order_by('created_at', 'id')

    if session_id:
        attempt_qs = attempt_qs.filter(session_id=session_id)

    if max_attempts and max_attempts > 0:
        attempt_qs = attempt_qs[:max_attempts]

    raw_attempts = []
    attempt_info_list = []
    for idx, att in enumerate(attempt_qs, start=1):
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

    # Research Audit Refinement for Performance Aggregation:
    # Extract test-evaluating attempts (where total_tests > 0)
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
        "problem_id": problem.problem_id or str(problem.id),
        "problem_title": problem.title,
        "trajectory_length": total_attempts,
        "attempts": raw_attempts,
        "transitions": transitions,
        "trajectory_summary": summary,
    }


def build_trajectory_from_dicts(attempts_list: list, user_id: str = "test_user", problem_id: str = "test_problem", problem_title: str = "Test Problem") -> dict:
    """
    Construct a complete trajectory representation from raw attempt dicts without DB access.
    Used for controlled trajectory pattern benchmarks (P1..P10).
    """
    attempt_info_list = []
    raw_attempts = []
    now = timezone.now()

    for idx, att in enumerate(attempts_list, start=1):
        dt = now + timezone.timedelta(seconds=idx * 20)
        info = {
            "attempt_id": att.get("attempt_id", idx),
            "index": idx,
            "code": att.get("code", ""),
            "language": att.get("language", "python"),
            "status": att.get("status", "WRONG_ANSWER"),
            "execution_time": att.get("execution_time", "0.10s"),
            "tests_passed": att.get("tests_passed", 0),
            "total_tests": att.get("total_tests", 0),
            "tests_failed": att.get("tests_failed", 0),
            "pass_rate": att.get("pass_rate", 0.0),
            "error_message": att.get("error_message", ""),
            "normalized_error": normalize_error(att.get("error_message", "")),
            "created_at_dt": dt
        }
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

