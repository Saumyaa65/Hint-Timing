# Struggle Assessment Methodology (Rule-Based Baseline Operationalization)

This document describes the methodology for the first **Struggle Assessment Baseline** in the research framework:  
**"Personalized Contextual Hint Generation System: An Adaptive LLM-Based Hinting Framework for Programming Practice."**

The primary research question driving this methodology is:
> *"Can we distinguish productive struggle from unproductive struggle, and use that distinction to decide whether the student should be left to continue or receive help?"*

---

## 1. Research Position & Operationalization Philosophy

> **IMPORTANT**: `PRODUCTIVE`, `UNPRODUCTIVE`, and `UNCERTAIN` are **not** ground-truth labels. The baseline implemented in this module is a provisional, rule-based operationalization designed for scientific baseline comparison against future LLM trajectory reasoning, hybrid models, and expert human annotations.

Key principles:
1. **Struggle as a Process**: Assessment is computed over a trajectory prefix ($A_1 \to A_2 \to \dots \to A_t$) using strictly information available up to attempt $t$.
2. **Zero Future Information Leakage**: Attempting assessment at step $t$ uses `build_trajectory(..., max_attempts=t)`. Attempts $t+1 \dots N$ are completely invisible to step $t$.
3. **Transparent & Explainable**: Every state determination exposes granular positive, negative, and uncertainty evidence signals along with natural language reasoning.
4. **Research/Analysis Scope**: Baseline assessments are for measurement and logging. No automated hint delivery or intervention side-effects are triggered in the live environment during this phase.

---

## 2. The Three Assessment States

### A. PRODUCTIVE STRUGGLE
- **Definition**: The learner is experiencing difficulty, but the trajectory prefix contains evidence that their attempts are meaningfully evolving toward a solution.
- **Evidence Signals**:
  - Test performance improvement (`delta_tests_passed > 0`, `delta_pass_rate > 0`).
  - Error state evolution (e.g., resolving compilation errors or progressing from syntax to logical errors).
  - Active exploration (`is_approach_change == True` or high exploration score without regressing).
  - Escaping a stagnant loop into an outcome change or test pass gain.
  - Prefix-level test progress relative to initial attempts.
- **Important Distinction**: Intermediate failing attempts and new errors are **not** inherently negative if accompanied by progress through problem-solving stages.

### B. UNPRODUCTIVE STRUGGLE
- **Definition**: The learner is struggling with little or no evidence of meaningful state evolution.
- **Evidence Signals**:
  - Repeated execution of identical code with identical outcomes (`REPEAT_EXECUTION`).
  - Encountering identical execution errors repeatedly without code modification.
  - Complete state stagnation (`repeated_state == True`).
  - Sustained performance stagnation ($ \ge 2 $ consecutive stagnant transitions).
  - High consecutive failures ($ \ge 3 $) with zero test gain.
  - Cyclic code reversion to earlier attempted states without performance improvement.
- **Important Distinction**: Failure alone does **not** equal unproductive struggle. Unproductive struggle requires evidence of **stagnation and lack of meaningful evolution**.

### C. UNCERTAIN
- **Definition**: The available trajectory prefix does not provide sufficient evidence to confidently assign a productive or unproductive state.
- **Evidence Signals**:
  - Very short trajectory prefix ($t < 2$).
  - Equal or conflicting signals of both progress and stagnation.
  - Code edits occurring without evaluation feedback (e.g., custom runs without test suite details).
  - Changing error states with zero performance resolution.

---

## 3. Feature-to-Signal Mapping Catalog

### Productive Signals ($P_1 \dots P_5$)

| Signal ID | Name | Weight | Trigger Condition |
| :--- | :--- | :--- | :--- |
| **P1** | `PERFORMANCE_IMPROVEMENT` | 1.0 | $\Delta \text{pass\_rate} \ge 0.15$ or $\Delta \text{tests\_passed} \ge 1$ in latest transition. |
| **P2** | `ERROR_EVOLUTION` | 0.8 / 0.6 | Execution error resolved (`error_resolved == True`) or error type shifted accompanied by overall progress. |
| **P3** | `EXPLORATION` | 0.6 / 0.4 | Substantial code/approach modification (`is_approach_change == True`) or high exploration score without regression. |
| **P4** | `STAGNATION_ESCAPE` | 0.9 | Transition out of prior stagnation into test pass gain or outcome change. |
| **P5** | `OVERALL_TRAJECTORY_PROGRESS` | 0.9 | Net test gain ($\text{peak\_test\_improvement} \ge 1$) over initial attempt in prefix. |

### Unproductive Signals ($U_1 \dots U_6$)

| Signal ID | Name | Weight | Trigger Condition |
| :--- | :--- | :--- | :--- |
| **U1** | `REPEATED_EXECUTION` | 0.7 | Button re-click with identical code and outcome (`interaction_type == "REPEAT_EXECUTION"`). |
| **U2** | `REPEATED_ERROR` | 0.8 | Identical error encountered repeatedly (`repeated_error == True`). |
| **U3** | `REPEATED_STATE` | 0.9 | Complete state (code, error, test count) stagnant (`repeated_state == True`). |
| **U4** | `PERFORMANCE_STAGNATION` | 0.7 / 1.0 | $ \ge 2 $ consecutive stagnant transitions with zero net test gain. |
| **U5** | `REPEATED_FAILED_ATTEMPTS` | 0.7 | $ \ge 3 $ consecutive failing attempts with zero test gain. |
| **U6** | `REVERSION_CYCLIC` | 0.8 | Code reverted to an earlier attempt (`reverts_to_prior_code == True`) without test gain. |

---

## 4. Evidence Aggregation & State Decision Logic

Let $W_P = \sum w_i$ for active productive signals, and $W_U = \sum w_j$ for active unproductive signals.

1. **Short Trajectory Rule**: If $t < \text{MIN\_TRAJECTORY\_LENGTH}$ ($t < 2$), state is automatically **`UNCERTAIN`**.
2. **Conflict Rule**: If $|W_P - W_U| < 0.35$ and both $W_P > 0$ and $W_U > 0$, state is **`UNCERTAIN`**.
3. **Productive Dominance**: If $W_P > W_U$ and $(W_P - W_U) \ge 0.30$, state is **`PRODUCTIVE`**.
4. **Unproductive Dominance**: If $W_U > W_P$ and $(W_U - W_P) \ge 0.30$, state is **`UNPRODUCTIVE`**.
5. **Default**: Otherwise, state is **`UNCERTAIN`**.

---

## 5. Heuristic Evidence Confidence Calculation

Confidence $C \in [0.0, 1.0]$ reflects evidence strength and signal consistency (explicitly non-calibrated):

$$\text{Margin} = \frac{|W_P - W_U|}{W_P + W_U}$$

$$\text{LengthFactor} = \min(1.0, 0.5 + 0.1 \times t)$$

$$C = \max\left(0.30, \min\left(0.95, \left(0.5 \times \text{Margin} + 0.5 \times \min\left(1.0, \frac{W_P + W_U}{2.0}\right)\right) \times \text{LengthFactor} - \text{Penalty}\right)\right)$$

Where $\text{Penalty} = 0.20$ if uncertainty signals are present.

---

## 6. Threshold Configuration (`struggle_analysis/config.py`)

```python
BASELINE_CONFIG = {
    'MIN_TRAJECTORY_LENGTH': 2,
    'MEANINGFUL_PASS_RATE_IMPROVEMENT': 0.15,
    'MEANINGFUL_TESTS_IMPROVEMENT': 1,
    'STAGNATION_THRESHOLD': 2,
    'HIGH_STAGNATION_THRESHOLD': 3,
    'CONSECUTIVE_FAILURES_THRESHOLD': 3,
    'MIN_CONFIDENCE_THRESHOLD': 0.40,
    'HIGH_CONFIDENCE_THRESHOLD': 0.75,
}
```

---

## 7. Future Expert Human-in-the-Loop Validation Protocol

To transition from provisional heuristic operationalization to scientific validation:
1. Collect interaction trajectory prefixes from programming sessions.
2. Annotate prefixes independently using multiple domain experts (CS educators/TAs).
3. Measure Inter-Rater Reliability (Cohen's / Fleiss' $\kappa$).
4. Benchmark **Rule-Based Baseline** vs **LLM Trajectory Reasoning** vs **Supervised Classifiers** against the expert ground-truth benchmark.
