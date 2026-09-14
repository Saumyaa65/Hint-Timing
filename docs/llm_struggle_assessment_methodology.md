# LLM Trajectory Reasoning for Struggle Assessment (Methodology & Design)

This document describes the design and methodology of the **LLM-Based Trajectory Reasoning System** in our research framework:  
**"Personalized Contextual Hint Generation System: An Adaptive LLM-Based Hinting Framework for Programming Practice."**

The primary research question driving this methodology is:
> *"Can we distinguish productive struggle from unproductive struggle, and use that distinction to decide whether the student should be left to continue or receive help?"*

---

## 1. Purpose & Research Positioning

> **IMPORTANT RESEARCH DISCLOSURE**: The LLM assessment is an alternative model-based operationalization of the research hypothesis and is **not** treated as ground truth or a human-validated gold standard. Empirical validity requires comparison against independently obtained human/expert annotations.

Key principles:
1. **Independent Assessment Methodology**: The LLM reasoning module operates independently from the rule-based baseline. Neither method relies on, calls, or copies the other.
2. **Trajectory Prefix Input ($1 \dots t$)**: The LLM receives strictly the ordered trajectory prefix up to attempt $t$. **Zero future information leakage** ($t+1 \dots N$).
3. **Process over Outcome**: The LLM is instructed to reason over the interaction process demonstrated in the trajectory, rather than evaluating whether the problem was eventually solved.
4. **Structured & Grounded Reasoning**: The LLM must separate direct observations from pedagogical interpretations and final state assessments.

---

## 2. Input Trajectory Representation

The LLM input is constructed via `format_trajectory_for_llm(trajectory_data)` in [`struggle_analysis/llm_assessment.py`](file:///d:/VIT%20Projects/Hint%20Generation/Coding_Platform/backend/struggle_analysis/llm_assessment.py):

- **Problem Context**: Title, difficulty, problem ID.
- **Ordered Attempt Snapshots ($A_1 \dots A_t$)**: Attempt index, timestamp, execution status, language, tests passed/failed/total, pass rate, normalized error messages, truncated code snippets.
- **Transition Features ($A_{i-1} \to A_i$)**: Interaction type (`INITIAL`, `REPEAT_EXECUTION`, `CODE_CHANGE`, `OUTCOME_CHANGE`), code similarity ratio, code change magnitude, error shift indicators, performance trend, state stagnation flags, cyclic reversion flags.
- **Trajectory Summary up to $t$**: Cumulative attempts, total duration, peak test pass improvement, repeat execution counts, code change counts, outcome change counts.

---

## 3. System Prompt Design & Evidence Grounding

The system prompt explicitly enforces pedagogical trajectory reasoning rules:

1. **Productive Struggle**: Difficulty accompanied by meaningful process evolution (test pass gains, error shifts, code exploration, escaping stagnation).
2. **Unproductive Struggle**: Difficulty accompanied by sustained stagnation, repeated identical executions, identical error loops, or cyclic state reversions without progress.
3. **Uncertain State**: Insufficient trajectory length ($t < 2$), conflicting evidence signals, or code edits without test suite evaluation feedback.
4. **Non-Penalization Rules**:
   - Failure alone does **not** imply unproductive struggle.
   - High attempt counts alone do **not** imply unproductive struggle.
   - Shifting from a compilation error to a runtime error indicates progress through execution stages.
   - Code changes indicate exploration, but do not prove learning without evaluation progress.
   - Reverting to prior code without progress is evidence of cyclic stagnation.

---

## 4. Structured JSON Output Schema

```json
{
  "state": "PRODUCTIVE" | "UNPRODUCTIVE" | "UNCERTAIN",
  "confidence": 0.85,
  "evidence": {
    "observation": "Pass rate increased from 0.0 to 1.0 across attempts 1 to 5.",
    "interpretation": "Learner actively experimented with algorithm logic, resolving compilation errors into a full solve.",
    "progression": ["Gained +4 unit tests on attempt 5"],
    "exploration": ["Substantial code modification on transition 3->4"],
    "error_evolution": ["Syntax error resolved on attempt 3"],
    "stagnation": [],
    "temporal": ["Attempts spaced 20-30s apart"]
  },
  "positive_signals": ["P1_PERFORMANCE_IMPROVEMENT", "P4_STAGNATION_ESCAPE"],
  "negative_signals": [],
  "uncertainty_signals": [],
  "reasoning": "Assessed as PRODUCTIVE struggle at attempt 5 (confidence: 0.85). Primary evidence: Gained +4 unit tests on attempt 5.",
  "recommended_action": "CONTINUE" | "MONITOR" | "CONSIDER_INTERVENTION"
}
```

---

## 5. Temporal Isolation & Zero Future Leakage

Assessment at attempt step $t$ uses `build_trajectory(user_id, problem, max_attempts=t)`. Attempts $A_{t+1} \dots A_N$ are completely excluded from the prompt text, ensuring strict temporal isolation for online intervention research.

---

## 6. Robust Failure Handling

If the LLM API fails, times out, or returns invalid JSON:
- The service returns a structured research error object:
  ```json
  {
    "error": "LLM assessment failed: API timeout / invalid JSON",
    "status": "failed"
  }
  ```
- **No silent fallback**: The system does **not** silently convert an LLM failure into a rule-based baseline result, preserving method independence.

---

## 7. Baseline Comparison Methodology

The utility `compare_struggle_assessments(user_id, problem_id, max_attempts=t)` runs both methods on the exact same prefix:
- Evaluates `rule_based` baseline result vs `llm` trajectory reasoning result.
- Computes `agreement: true/false` (`rule_state == llm_state`).
- **Research Note**: Agreement measures operational state overlap between models. It is **not** an empirical accuracy metric.

---

## 8. Limitations & Future Validation

- LLM confidence scores ($0.0 \to 1.0$) represent self-reported model certainty and are **not** statistically calibrated probabilities.
- Model outputs depend on LLM provider availability and prompt structure.
- Future empirical validation requires benchmarking both Rule Baseline and LLM Trajectory Reasoning against independent expert human annotations.
