# Trajectory Representation and Feature Definitions (Research Validity Audit)

This document details the research-grade **Observation and Representation Layer** for the capstone project:  
**"Personalized Contextual Hint Generation System: An Adaptive LLM-Based Hinting Framework for Programming Practice."**

The primary research question driving this framework is:
> *"Can we distinguish productive struggle from unproductive struggle, and use that distinction to decide whether the student should be left to continue or receive help?"*

---

## 1. Research Validity Principles & Audit Refinement

During initial system evaluation on live interaction trajectories, key research considerations were established to ensure logical consistency and scientific defensibility:

1. **Struggle as a Process**: Trajectories are analyzed as an ordered sequence of interaction states ($A_1 \to A_2 \to \dots \to A_N$), rather than isolated snapshots.
2. **Strict Observation Layer**: Features describe observed interactions strictly without assigning target labels (`productive` / `unproductive`) or hardcoding intervention thresholds into the representation.
3. **No Target Leakage (Online Prefix Validity)**: Interventions at time step $t$ must be evaluated using strictly the trajectory prefix $1 \dots t$. Trajectory generation supports `max_attempts=t` to prevent future information leakage ($t+1 \dots N$).
4. **Complete State Stagnation**: A `repeated_state` requires complete stagnation across code, error, and evaluation test outcomes. If code is re-submitted but execution error resolves or test pass count changes, the state has materially changed and is **not** stagnant.
5. **Interaction Type Taxonomy**: Differentiates raw interaction button re-clicks (`REPEAT_EXECUTION`) from code edits (`CODE_CHANGE`) and evaluation state shifts (`OUTCOME_CHANGE`).

---

## 2. Trajectory Abstraction Schema

A trajectory represents the ordered sequence of attempts made by a specific **User + Problem** pair:

$$\text{Trajectory}(U, P, t) = \langle A_1, A_2, A_3, \dots, A_t \rangle \quad (1 \le t \le N)$$

Ordering is strictly chronological based on `Attempt.created_at`.

```json
{
  "user_id": "user_3JH0gS...",
  "problem_id": "1",
  "problem_title": "Two Sum",
  "trajectory_length": 4,
  "attempts": [
    {
      "index": 1,
      "attempt_id": 101,
      "timestamp": "2026-09-14T00:10:00Z",
      "status": "failed",
      "language": "python",
      "code": "...",
      "execution_time": "0.12s",
      "tests_passed": 2,
      "tests_failed": 8,
      "total_tests": 10,
      "pass_rate": 0.2,
      "error_message": "IndexError: list index out of range",
      "evaluation_details": {...}
    }
  ],
  "transitions": [
    {
      "from_attempt_index": 1,
      "to_attempt_index": 2,
      "from_attempt_id": 101,
      "to_attempt_id": 102,
      "temporal": {...},
      "code_evolution": {...},
      "error_evolution": {...},
      "performance": {...},
      "exploration": {...},
      "repetition": {
        "interaction_type": "CODE_CHANGE",
        "repeated_code": false,
        "reverts_to_prior_code": false,
        "repeated_error": false,
        "repeated_test_outcome": false,
        "repeated_state": false,
        "consecutive_unchanged_attempts": 0,
        "stagnation_length": 0
      }
    }
  ],
  "trajectory_summary": {
    "total_attempts": 4,
    "total_duration_seconds": 185.0,
    "overall_test_improvement": 8,
    "peak_test_improvement": 8,
    "overall_pass_rate_improvement": 0.8,
    "peak_pass_rate_improvement": 0.8,
    "number_of_repeat_executions": 0,
    "number_of_code_changes": 3,
    "number_of_outcome_changes": 0,
    "number_of_repeated_states": 0,
    "number_of_error_changes": 2,
    "stagnation_indicators": {
      "max_stagnation_length": 0,
      "is_currently_stagnant": false
    }
  }
}
```

---

## 3. Granular Transition Feature Catalog

For every transition between consecutive attempts ($A_{i-1} \to A_i$), features are extracted across 6 conceptual research dimensions.

---

### Group A: CODE EVOLUTION

#### 1. `code_similarity`
- **Definition**: String similarity ratio between normalized code of $A_{i-1}$ and $A_i$.
- **Calculation**: Python `difflib.SequenceMatcher(None, norm(code_{i-1}), norm(code_i)).ratio()`.
- **Research Relevance**: Quantifies code edit distance between consecutive attempts.
- **Status**: Direct Measurable Proxy.
- **Limitations**: Textual similarity does not equal semantic similarity.

#### 2. `code_change_ratio`
- **Definition**: Proportion of code altered between $A_{i-1}$ and $A_i$.
- **Calculation**: $1.0 - \text{code\_similarity}$.
- **Research Relevance**: Measures code edit intensity.
- **Status**: Direct Measurable Proxy.

#### 3. `repeated_code`
- **Definition**: Boolean flag indicating near-identical or identical code submission.
- **Calculation**: $\text{code\_similarity} \ge 0.98$.
- **Research Relevance**: Primary indicator of identical code re-execution.
- **Status**: Directly Observed Rule.

#### 4. `changed_code`
- **Definition**: Complement of `repeated_code`.
- **Calculation**: $\text{not } \text{repeated\_code}$.
- **Research Relevance**: Confirms active code modification occurred.
- **Status**: Directly Observed Rule.

#### 5. `code_change_magnitude`
- **Definition**: Categorical scale of code edit magnitude (`none`, `almost_identical`, `small_modification`, `substantial_modification`).
- **Calculation**: 
  - `none`: $\text{similarity} \ge 0.98$
  - `almost_identical`: $0.90 \le \text{similarity} < 0.98$
  - `small_modification`: $0.70 \le \text{similarity} < 0.90$
  - `substantial_modification`: $\text{similarity} < 0.70$
- **Status**: Categorical Proxy.

---

### Group B: ERROR EVOLUTION

#### 1. `normalized_error`
- **Definition**: Sanitized string representation of execution error.
- **Calculation**: Regex transformation stripping line numbers, hexadecimal memory addresses, and normalizing whitespace to lowercase.
- **Status**: Direct Measurable Proxy.

#### 2. `error_similarity`
- **Definition**: String similarity ratio between consecutive normalized error messages.
- **Calculation**: `SequenceMatcher` ratio on normalized error strings. Returns `1.0` if both attempts are error-free.
- **Status**: Direct Measurable Proxy.

#### 3. `repeated_error`
- **Definition**: True if student encountered the same error repeatedly.
- **Calculation**: Both attempts have errors and $\text{error\_similarity} \ge 0.85$.
- **Status**: Measurable Indicator.

#### 4. `error_changed`
- **Definition**: Indicates a change in error output between attempts.
- **Calculation**: $\text{error\_similarity} < 0.85$ or transition between error and non-error states.
- **Research Relevance**: **CRITICAL RESEARCH NOTE**: A new error is **NOT** inherently negative. Shifting from a compilation error to a logical/runtime error indicates progress through execution stages.
- **Status**: Measurable Indicator.

#### 5. `error_resolved`
- **Definition**: True if $A_{i-1}$ had an error and $A_i$ produced no execution errors.
- **Calculation**: `prev_normalized_error != ""` and `curr_normalized_error == ""`.
- **Status**: Directly Observed Signal.

#### 6. `error_introduced`
- **Definition**: True if $A_{i-1}$ had no error and $A_i$ produced an execution error.
- **Calculation**: `prev_normalized_error == ""` and `curr_normalized_error != ""`.
- **Status**: Directly Observed Signal.

---

### Group C: PERFORMANCE / TEST PROGRESSION

#### 1. `delta_tests_passed`
- **Definition**: Net change in passed unit test count.
- **Calculation**: $\text{tests\_passed}_i - \text{tests\_passed}_{i-1}$.
- **Status**: Directly Observed Metric.

#### 2. `delta_pass_rate`
- **Definition**: Net change in test pass ratio ($0.0 \to 1.0$).
- **Calculation**: $\text{pass\_rate}_i - \text{pass\_rate}_{i-1}$.
- **Status**: Directly Observed Metric.

#### 3. `performance_trend`
- **Definition**: Categorical direction of test progress (`improved`, `unchanged`, `regressed`).
- **Calculation**: 
  - `improved`: $\Delta \text{tests\_passed} > 0$ or $\Delta \text{pass\_rate} > 0$
  - `regressed`: $\Delta \text{tests\_passed} < 0$ or $\Delta \text{pass\_rate} < 0$
  - `unchanged`: $\Delta \text{tests\_passed} = 0$
- **Status**: Directly Observed Categorical Signal.

---

### Group D: EXPLORATION / APPROACH CHANGE

#### 1. `is_approach_change`
- **Definition**: Approximate proxy indicating whether the student drastically altered their solution approach.
- **Calculation**: `code_change_magnitude == "substantial_modification"` or ($\text{code\_similarity} < 0.70$ and `structural_pattern_changed`).
- **Status**: Approximate Proxy Signal.

#### 2. `structural_pattern_changed`
- **Definition**: Proxy detecting changes in control flow keywords (`for`, `while`, `if`, `def`, `try`) or line count variance ($> 35\%$).
- **Status**: Heuristic Proxy.

#### 3. `exploration_score`
- **Definition**: Combined numerical rating ($0.0 \to 1.0$) of code and error divergence.
- **Calculation**: $(1.0 - \text{code\_similarity}) \times 0.6 + (0.4 \text{ if error\_changed else } 0.0)$.
- **Status**: Composite Heuristic Proxy.

---

### Group E: TEMPORAL BEHAVIOUR

#### 1. `time_delta`
- **Definition**: Wall-clock duration in seconds between consecutive attempts.
- **Calculation**: $\text{created\_at}_i - \text{created\_at}_{i-1}$.
- **Research Relevance**: Reflects reflection/editing time between runs.
- **Limitations**: **CRITICAL RESEARCH NOTE**: Long time deltas do NOT automatically imply unproductive struggle (e.g., student stepped away to think or draft on paper). Temporal features are evidence, not labels.

#### 2. `total_trajectory_duration`
- **Definition**: Total elapsed seconds from initial attempt $A_1$ to $A_i$.
- **Calculation**: $\text{created\_at}_i - \text{created\_at}_1$.
- **Status**: Directly Observed Metric.

#### 3. `attempt_frequency_per_min`
- **Definition**: Average attempt velocity over total trajectory duration.
- **Calculation**: $i / (\text{total\_duration} / 60.0)$.
- **Status**: Derived Ratio.

#### 4. `consecutive_failed_attempts`
- **Definition**: Count of uninterrupted non-success attempts up to $A_i$.
- **Status**: Directly Observed Counter.

#### 5. `struggle_duration`
- **Definition**: Accumulated time spent in a failing state up to current attempt.
- **Status**: Derived Temporal Metric.

---

### Group F: REPETITION, STAGNATION & TAXONOMY

#### 1. `interaction_type`
- **Definition**: Categorical classification of the transition type:
  - `INITIAL`: First attempt ($A_1$).
  - `REPEAT_EXECUTION`: Unchanged code (`code_sim >= 0.98`) AND unchanged evaluation outcome.
  - `CODE_CHANGE`: Solution code modified (`code_sim < 0.98`).
  - `OUTCOME_CHANGE`: Unchanged code (`code_sim >= 0.98`) BUT execution status, error, or test pass count changed.
  - `SUBMISSION`: Explicit solution submission.
- **Research Relevance**: Allows filtering button re-clicks when analyzing code evolution vs evaluation evolution.
- **Status**: Directly Observed Taxonomy.

#### 2. `reverts_to_prior_code`
- **Definition**: True if current attempt code matches any attempt code prior to $A_{i-1}$ in the trajectory ($A_1 \dots A_{i-2}$).
- **Status**: Directly Observed Trajectory Metric.

#### 3. `repeated_state`
- **Definition**: Complete learner state stagnation.
- **Calculation**: 
  $$\text{repeated\_state} = (\text{repeated\_code} \lor \text{reverts\_to\_prior\_code}) \land \text{is\_error\_stagnant} \land \text{repeated\_test\_outcome} \land (\text{trend} = \text{"unchanged"})$$
- **Research Relevance**: Prevents false positive stagnation when execution errors resolve or test scores improve.
- **Status**: Directly Observed Stagnation Signal.

#### 4. `stagnation_length`
- **Definition**: Count of consecutive transitions with `REPEAT_EXECUTION` or `repeated_state`. Resets to `0` whenever `CODE_CHANGE`, `OUTCOME_CHANGE`, or `performance_trend == "improved"` occurs.
- **Status**: Derived Stagnation Counter.

---

## 4. Performance Summary Aggregation Formulas

To eliminate anomalies caused by custom runs or non-evaluating attempts:

- `initial_tests_passed`: Passed test count on the first test-evaluating attempt.
- `latest_evaluating_tests_passed`: Passed test count on the latest test-evaluating attempt.
- `max_tests_passed`: Maximum passed test count across all attempts in trajectory.
- `overall_test_improvement`: $\text{latest\_evaluating\_tests\_passed} - \text{initial\_tests\_passed}$.
- `peak_test_improvement`: $\text{max\_tests\_passed} - \text{initial\_tests\_passed}$.
- `overall_pass_rate_improvement`: $\text{latest\_pass\_rate} - \text{initial\_pass\_rate}$.
- `peak_pass_rate_improvement`: $\text{max\_pass\_rate} - \text{initial\_pass\_rate}$.
