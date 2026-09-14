import json
import logging
import re
from typing import Dict, Any
from django.conf import settings
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from .trajectory import build_trajectory

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """
You are an expert Educational Data Science & Intelligent Tutoring Research Assistant evaluating student programming struggle trajectories.

Your task is to analyze a student's chronological programming interaction TRAJECTORY PREFIX (from attempt 1 up to attempt t) and assess their struggle state.

==================================================
CONCEPTUAL DEFINITIONS
==================================================

1. PRODUCTIVE STRUGGLE:
The student is experiencing difficulty, but the interaction trajectory contains clear evidence that their attempts are meaningfully evolving towards a solution.
Evidence includes: improving test pass counts/rates, resolving compilation/runtime errors, shifting from one error type to another (e.g. syntax error -> runtime error -> test failure), active code/approach exploration, escaping a prior stagnation loop, or net overall test progress over early attempts.

2. UNPRODUCTIVE STRUGGLE:
The student is struggling with sustained stagnation, repetition, or lack of meaningful state evolution.
Evidence includes: repeated executions of identical code with identical outcomes, encountering the same execution error repeatedly without modification, complete state stagnation across code + errors + test results, sustained performance stagnation over multiple attempts, or cyclic reversion to prior unworking states without progress.

3. UNCERTAIN:
The available trajectory prefix does not contain enough evidence to confidently distinguish productive from unproductive struggle.
Evidence includes: very short trajectory (only 1 or 2 attempts), conflicting signals of progress and stagnation, code modifications made without test suite evaluation feedback, or changing error states with zero performance resolution.

==================================================
CRITICAL RESEARCH INSTRUCTIONS
==================================================

- PROCESS OVER OUTCOME: Assess the interaction PROCESS demonstrated in the trajectory up to attempt t. Do not assess based on whether the final attempt is solved or unsolved.
- NO FUTURE LEAKAGE: You are evaluating strictly attempts 1 to t. You must NOT infer or guess future attempts (t+1 onwards).
- FAILURE IS NORMAL: Intermediate failed attempts or high failure counts do NOT automatically imply unproductive struggle.
- NEW ERRORS MAY BE PROGRESS: Shifting from a compilation error to a runtime error or wrong answer indicates progress through execution stages. Do NOT treat new error types as inherently negative.
- CODE CHANGES ALONE ARE NOT PROOF: Changing code indicates exploration, but is not proof of productive learning unless accompanied by evaluation progress or meaningful error evolution.
- DO NOT CHEAT OR INVENT EVIDENCE: Cite ONLY observable metrics provided in the trajectory (test pass rates, error messages, diff ratios, attempt frequency). Do NOT claim unobservable student thoughts, psychological states, or unrecorded code changes.
- DO NOT FORCES A BINARY ANSWER: Use UNCERTAIN if evidence is ambiguous or insufficient.

==================================================
REQUIRED JSON OUTPUT FORMAT
==================================================

You MUST respond strictly with a single valid JSON object formatted exactly as follows:

{
  "state": "PRODUCTIVE" | "UNPRODUCTIVE" | "UNCERTAIN",
  "confidence": 0.85,
  "evidence": {
    "observation": "Direct observed metrics (e.g., pass rate gained from 0.0 to 0.5 across 3 attempts)",
    "interpretation": "Pedagogical interpretation of observed process",
    "progression": ["Specific test or score progression details"],
    "exploration": ["Specific code modification or approach change details"],
    "error_evolution": ["Error shift or resolution details"],
    "stagnation": ["Repeated execution or stagnant state details"],
    "temporal": ["Attempt frequency or struggle duration details"]
  },
  "positive_signals": ["List of identified productive signal IDs (e.g. P1_PERFORMANCE_IMPROVEMENT, P2_ERROR_EVOLUTION, P3_EXPLORATION, P4_STAGNATION_ESCAPE, P5_OVERALL_PROGRESS)"],
  "negative_signals": ["List of identified unproductive signal IDs (e.g. U1_REPEATED_EXECUTION, U2_REPEATED_ERROR, U3_REPEATED_STATE, U4_PERFORMANCE_STAGNATION, U5_REPEATED_FAILED_ATTEMPTS, U6_REVERSION_CYCLIC)"],
  "uncertainty_signals": ["List of uncertainty factors if any (e.g. UNCERTAIN_SHORT_TRAJECTORY, UNCERTAIN_CONFLICTING_EVIDENCE)"],
  "reasoning": "Concise natural language explanation citing trajectory evidence",
  "recommended_action": "CONTINUE" | "MONITOR" | "CONSIDER_INTERVENTION"
}

Respond ONLY with the JSON object. Do not include markdown code block backticks or conversational preamble.
"""


def format_trajectory_for_llm(trajectory_data: dict) -> str:
    """
    Format a structured trajectory prefix object into a clear, evidence-grounded text prompt.
    Ensures ZERO future attempts exist in the prompt text.
    """
    user_id = trajectory_data.get("user_id", "")
    problem_id = trajectory_data.get("problem_id", "")
    problem_title = trajectory_data.get("problem_title", "")
    trajectory_length = trajectory_data.get("trajectory_length", 0)
    attempts = trajectory_data.get("attempts", [])
    transitions = trajectory_data.get("transitions", [])
    summary = trajectory_data.get("trajectory_summary", {})

    prompt_lines = [
        f"TRAJECTORY PREFIX FOR ASSESSMENT (Attempt 1 to {trajectory_length}):",
        f"Problem: {problem_title} (ID: {problem_id})",
        f"Trajectory Length (Prefix): {trajectory_length} attempts",
        "",
        "--- ATTEMPT SNAPSHOTS ---"
    ]

    for att in attempts:
        idx = att.get("index")
        status = att.get("status")
        lang = att.get("language")
        passed = att.get("tests_passed", 0)
        failed = att.get("tests_failed", 0)
        total = att.get("total_tests", 0)
        pass_rate = att.get("pass_rate", 0.0)
        err = att.get("error_message", "")
        code = att.get("code", "")

        if len(code) > 400:
            code_snippet = code[:350] + "\n... [code truncated]"
        else:
            code_snippet = code

        prompt_lines.append(f"\nAttempt #{idx}:")
        prompt_lines.append(f"  Status: {status} | Language: {lang}")
        prompt_lines.append(f"  Test Results: {passed}/{total} passed (Pass Rate: {round(pass_rate*100, 1)}%)")
        if err:
            prompt_lines.append(f"  Error Message: {err}")
        prompt_lines.append(f"  Code:\n{code_snippet}")

    prompt_lines.append("\n--- TRANSITION FEATURES (CONSECUTIVE ATTEMPTS) ---")
    for trans in transitions:
        f_idx = trans.get("from_attempt_index")
        t_idx = trans.get("to_attempt_index")
        itype = trans.get("repetition", {}).get("interaction_type")
        code_sim = trans.get("code_evolution", {}).get("code_similarity")
        magnitude = trans.get("code_evolution", {}).get("code_change_magnitude")
        err_changed = trans.get("error_evolution", {}).get("error_changed")
        err_resolved = trans.get("error_evolution", {}).get("error_resolved")
        perf_trend = trans.get("performance", {}).get("performance_trend")
        delta_passed = trans.get("performance", {}).get("delta_tests_passed")
        rep_state = trans.get("repetition", {}).get("repeated_state")
        stagnation = trans.get("repetition", {}).get("stagnation_length")
        reverts = trans.get("repetition", {}).get("reverts_to_prior_code")

        prompt_lines.append(f"\nTransition Attempt #{f_idx} -> #{t_idx}:")
        prompt_lines.append(f"  Interaction Type: {itype}")
        prompt_lines.append(f"  Code Similarity: {code_sim} (Magnitude: {magnitude})")
        if reverts:
            prompt_lines.append(f"  Code Reversion: Reverted to an earlier attempted code state!")
        prompt_lines.append(f"  Error Evolution: Changed={err_changed}, Resolved={err_resolved}")
        prompt_lines.append(f"  Performance Trend: {perf_trend} (Delta Tests Passed: {delta_passed})")
        prompt_lines.append(f"  State Stagnation: Repeated State={rep_state}, Consecutive Stagnant Length={stagnation}")

    prompt_lines.append("\n--- TRAJECTORY PREFIX SUMMARY ---")
    prompt_lines.append(f"Total Attempts in Prefix: {summary.get('total_attempts')}")
    prompt_lines.append(f"Total Elapsed Duration: {summary.get('total_duration_seconds')}s")
    prompt_lines.append(f"Peak Test Pass Improvement: +{summary.get('peak_test_improvement')} tests")
    prompt_lines.append(f"Net Pass Rate Improvement: +{round(summary.get('overall_pass_rate_improvement', 0)*100, 1)}%")
    prompt_lines.append(f"Repeat Executions: {summary.get('number_of_repeat_executions')}")
    prompt_lines.append(f"Code Changes: {summary.get('number_of_code_changes')}")
    prompt_lines.append(f"Outcome Changes: {summary.get('number_of_outcome_changes')}")
    prompt_lines.append(f"Repeated States: {summary.get('number_of_repeated_states')}")
    prompt_lines.append(f"Currently Stagnant: {summary.get('stagnation_indicators', {}).get('is_currently_stagnant')}")

    return "\n".join(prompt_lines)


def parse_llm_json_response(raw_response: str) -> dict:
    """
    Safely parse JSON from LLM output, stripping markdown fencing if present.
    """
    clean_text = raw_response.strip()
    match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', clean_text, re.DOTALL)
    if match:
        clean_text = match.group(1).strip()
    else:
        start = clean_text.find('{')
        end = clean_text.rfind('}')
        if start != -1 and end != -1:
            clean_text = clean_text[start:end+1]

    parsed = json.loads(clean_text)

    required_keys = ['state', 'confidence', 'reasoning']
    for k in required_keys:
        if k not in parsed:
            raise ValueError(f"Missing required key '{k}' in LLM JSON output")

    if parsed['state'] not in ['PRODUCTIVE', 'UNPRODUCTIVE', 'UNCERTAIN']:
        parsed['state'] = 'UNCERTAIN'

    return parsed


PROMPT_VERSION = "TASK_2C_SYSTEM_V1"


def assess_trajectory_with_llm(trajectory_data: dict, model_name: str = None, strict_model_pinning: bool = False) -> dict:
    """
    Core Research LLM Entry Point:
    Assess trajectory prefix using OpenRouter LLM trajectory reasoning.
    
    Supports model fallbacks for application runtime resilience, or strict model pinning
    (strict_model_pinning=True) for scientific research reproducibility.
    """
    api_key = getattr(settings, 'OPENROUTER_API_KEY', None)
    if not api_key:
        logger.warning("OPENROUTER_API_KEY missing in settings")
        return {
            "error": "LLM assessment unavailable: OPENROUTER_API_KEY is not configured.",
            "status": "failed",
            "prompt_version": PROMPT_VERSION
        }

    formatted_user_prompt = format_trajectory_for_llm(trajectory_data)

    primary_model = model_name or "meta-llama/llama-3.3-70b-instruct"

    if strict_model_pinning:
        models_to_try = [primary_model]
    else:
        candidate_models = [
            primary_model,
            "qwen/qwen-2.5-coder-32b-instruct",
            "google/gemini-2.0-flash-001",
            "openai/gpt-4o-mini",
            "openai/gpt-3.5-turbo"
        ]
        models_to_try = []
        for m in candidate_models:
            if m not in models_to_try:
                models_to_try.append(m)

    last_error = None

    for target_model in models_to_try:
        try:
            llm = ChatOpenAI(
                model=target_model,
                openai_api_key=api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=0.3,
                max_tokens=1000
            )

            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=formatted_user_prompt)
            ]

            response = llm.invoke(messages)
            raw_content = response.content

            parsed_json = parse_llm_json_response(raw_content)

            return {
                "method": "LLM Trajectory Reasoning",
                "model": target_model,
                "prompt_version": PROMPT_VERSION,
                "strict_model_pinning": strict_model_pinning,
                "state": parsed_json.get("state", "UNCERTAIN"),
                "confidence": float(parsed_json.get("confidence", 0.5)),
                "assessment_attempt": trajectory_data.get("trajectory_length", 0),
                "evidence": parsed_json.get("evidence", {}),
                "positive_signals": parsed_json.get("positive_signals", []),
                "negative_signals": parsed_json.get("negative_signals", []),
                "uncertainty_signals": parsed_json.get("uncertainty_signals", []),
                "reasoning": parsed_json.get("reasoning", ""),
                "recommended_action": parsed_json.get("recommended_action", "MONITOR"),
                "raw_prompt_length": len(formatted_user_prompt)
            }

        except Exception as e:
            last_error = e
            logger.warning(f"LLM model {target_model} failed: {e}. Trying next candidate...")

    return {
        "error": f"LLM assessment failed on model '{primary_model}': {str(last_error)}" if strict_model_pinning else f"LLM assessment failed on all candidate models: {str(last_error)}",
        "status": "failed",
        "model": primary_model,
        "prompt_version": PROMPT_VERSION,
        "strict_model_pinning": strict_model_pinning
    }


def assess_prefix_with_llm(user_id: str, problem_id_or_obj, max_attempts: int = None, model_name: str = None, strict_model_pinning: bool = False) -> dict:
    """
    Assess struggle state for a specific USER + PROBLEM trajectory prefix (1 ... t) using LLM reasoning.
    Guarantees online temporal validity (zero future information leakage).
    """
    trajectory_data = build_trajectory(
        user_id=user_id,
        problem_id_or_obj=problem_id_or_obj,
        max_attempts=max_attempts
    )

    if "error" in trajectory_data:
        return trajectory_data

    assessment = assess_trajectory_with_llm(trajectory_data, model_name=model_name, strict_model_pinning=strict_model_pinning)

    return {
        "trajectory_prefix": trajectory_data,
        "assessment": assessment
    }
