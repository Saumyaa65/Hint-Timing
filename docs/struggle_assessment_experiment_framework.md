# Research Experimentation Framework for Struggle Assessment

This document specifies the research experimentation framework designed to systematically compare and evaluate multiple struggle-assessment methodologies within the capstone project:

> *"Personalized Contextual Hint Generation System: An Adaptive LLM-Based Hinting Framework for Programming Practice."*

---

## 1. Experimental Hypotheses

We formulate five core research hypotheses regarding interaction dynamics and struggle assessment:

- **H1 (Trajectory Information Gain)**: Trajectory-level interaction analysis ($A_1 \dots A_t$) captures significantly richer pedagogical information about learner struggle than a single latest-attempt snapshot ($A_t$).
- **H2 (Productive Struggle Dynamics)**: Productive struggle is characterized by measurable state evolution across trajectory prefixes, including combinations of performance progression, error shift/resolution, active approach exploration, and escape from stagnation loops.
- **H3 (Unproductive Struggle Dynamics)**: Unproductive struggle is characterized by sustained repetition/stagnation patterns (e.g. repeated executions of identical code, static error loop, cyclic code reversion) and an absence of state evolution.
- **H4 (Methodological Disagreement Scenarios)**: LLM-based trajectory reasoning and transparent rule-based heuristics will exhibit measurable disagreement when evaluating ambiguous, short, or mixed trajectory prefixes (e.g. code exploration without evaluation feedback).
- **H5 (Hybrid Modeling Hypothesis)**: A hybrid methodology combining objective trajectory feature extraction with LLM reasoning will yield superior agreement and alignment with human pedagogical assessments compared to either method independently. *(Note: H5 is a hypothesis for future empirical testing, NOT a pre-implementation assumption).*

---

## 2. Methodological Conditions to Compare

We define four methodological conditions:

| Condition | Method | Scope | Input Representation | Objective Features | LLM Reasoning | Status |
|-----------|--------|-------|----------------------|-------------------|-|--------|
| **M1** | Single-Attempt Snapshot | $A_t$ only | Latest attempt state | Partial (local state) | No | Active (Baseline) |
| **M2** | Rule-Based Trajectory | $A_1 \dots A_t$ | Chronological prefix | Yes (6 feature groups) | No | Active (Baseline) |
| **M3** | LLM Trajectory Reasoning | $A_1 \dots A_t$ | Chronological prompt | Injected into prompt | Yes | Active (Independent) |
| **M4** | Hybrid Feature + LLM | $A_1 \dots A_t$ | Objective Features + LLM Reasoning | Yes | Yes | Active (Implemented) |

> [!NOTE]
> The inclusion of **M1 (Snapshot Baseline)** is essential to empirically test whether historical trajectory information adds measurable value over assessing only the latest code attempt.

---

## 3. Single-Attempt Snapshot Baseline (M1)

### Rationale & Design
The single-attempt snapshot baseline evaluates ONLY attempt $A_t$ at step $t$, with zero access to prior attempts $A_1 \dots A_{t-1}$. It uses observable local attempt metrics:
- `test_pass_rate` and `tests_failed`
- `status` (`ACCEPTED`, `WRONG_ANSWER`, `COMPILE_ERROR`, `RUNTIME_ERROR`)
- `error_message`
- `code_length`

### Conservative Classification Strategy
Because a single attempt snapshot lacks temporal and evolutionary evidence:
1. `ACCEPTED` ($pass\_rate = 1.0$) $\rightarrow$ `PRODUCTIVE` struggle state (solved).
2. Unsolved with partial pass rate ($0.0 < pass\_rate < 1.0$) $\rightarrow$ `UNCERTAIN` (cannot distinguish if student is progressing or stuck without history).
3. Unsolved with 0 pass rate or execution/syntax error $\rightarrow$ `UNCERTAIN` or `UNPRODUCTIVE` (conservative threshold; high test failure with zero historical context defaults to `UNCERTAIN` unless code is trivially empty).

### Snapshot Limitations
Snapshot-only assessment cannot:
- Distinguish between a student's 1st failed attempt and 10th identical failed attempt.
- Detect error shifts (e.g., syntax error $\rightarrow$ runtime error $\rightarrow$ test failure).
- Identify code exploration or stagnation escape.
- Detect cyclic code reversions.

---

## 3.B. Hybrid Feature + LLM Struggle Assessment (M4)

### Evidence-Fusion Architecture
Condition M4 implements an interpretable evidence-fusion layer combining objective trajectory features & rule-based baseline signals (M2) with LLM trajectory reasoning (M3):

```
Trajectory Prefix (A_1 ... A_t)
        │
        ├───> Objective Trajectory Features ───> Rule-Based Assessment (M2) ───┐
        │                                                                        │
        │                                                                        ▼
        │                                                              Evidence Fusion Layer
        │                                                                        ▲
        │                                                                        │
        └───> Chronological Prompt ────────────> LLM Trajectory Reasoning (M3) ──┘
                                                                                 │
                                                                                 ▼
                                                                        HYBRID ASSESSMENT
                                                                     (PRODUCTIVE/UNPRODUCTIVE/UNCERTAIN)
```

### Fusion Decision Principles
1. **Full Consensus (Rule == LLM)**: When both methods agree on `PRODUCTIVE` or `UNPRODUCTIVE`, the hybrid asserts that state with a confidence boost (`+0.15`).
2. **Partial Consensus**: When one method is directional (`PRODUCTIVE`/`UNPRODUCTIVE`) and the other is `UNCERTAIN`, the hybrid asserts the directional state with a conservative scale (`*0.85`).
3. **Strong Conflict (Rule vs. LLM Disagreement)**: When one method asserts `PRODUCTIVE` and the other asserts `UNPRODUCTIVE`, the hybrid flags explicit conflict, penalizes confidence (`-0.30`), and conservatively defaults to `UNCERTAIN`.
4. **Short Trajectories ($t < 2$)**: Yields `UNCERTAIN` state.

> [!IMPORTANT]
> **Methodological Candidate Disclaimer**:
> The hybrid method is a methodological candidate, NOT a validated superior method. Its effectiveness must be evaluated against human/expert annotations in a later empirical study.

### Provisional Configuration Parameters (`HYBRID_CONFIG`)
```python
HYBRID_CONFIG = {
    'VERSION': '2E_HYBRID_PROVISIONAL_V1',
    'PROMPT_VERSION': 'TASK_2C_SYSTEM_V1',
    'CONSENSUS_BOOST': 0.15,
    'CONFLICT_PENALTY': 0.30,
    'DEFAULT_UNCERTAIN_CONFIDENCE': 0.50,
    'HIGH_CONFIDENCE_THRESHOLD': 0.80,
    'MIN_CONFIDENCE_THRESHOLD': 0.40,
}
```

### Normalized Hybrid Schema
```json
{
  "method": "hybrid",
  "assessment_attempt": 5,
  "state": "PRODUCTIVE | UNPRODUCTIVE | UNCERTAIN",
  "confidence": 0.95,
  "evidence": {
    "objective": ["Objective Positive: P1_PERFORMANCE_IMPROVEMENT"],
    "llm": ["LLM Positive: P1_PERFORMANCE_IMPROVEMENT"],
    "agreement": ["Full Consensus: Both Rule Baseline and LLM Reasoning assessed state as PRODUCTIVE."],
    "conflict": []
  },
  "positive_signals": ["P1_PERFORMANCE_IMPROVEMENT"],
  "negative_signals": [],
  "uncertainty_signals": [],
  "reasoning": "Hybrid assessment reached consensus (PRODUCTIVE, confidence: 0.95)...",
  "recommended_action": "CONTINUE | MONITOR | INTERVENE",
  "metadata": {
    "trajectory_length": 5,
    "rule_state": "PRODUCTIVE",
    "rule_confidence": 0.80,
    "llm_state": "PRODUCTIVE",
    "llm_confidence": 0.85,
    "llm_model": "meta-llama/llama-3.3-70b-instruct",
    "config_version": "2E_HYBRID_PROVISIONAL_V1",
    "prompt_version": "TASK_2C_SYSTEM_V1"
  }
}
```

---

## 4. Common Assessment Interface & Normalized Output

All assessment methods (M1, M2, M3) consume the exact same trajectory prefix $A_1 \dots A_t$ and output a normalized structure:

```json
{
  "method": "Snapshot Baseline | Rule-Based Baseline | LLM Trajectory Reasoning",
  "assessment_attempt": 20,
  "state": "PRODUCTIVE | UNPRODUCTIVE | UNCERTAIN",
  "confidence": 0.85,
  "evidence": {
    "positive_signals": ["P1_PERFORMANCE_IMPROVEMENT", "P4_STAGNATION_ESCAPE"],
    "negative_signals": ["U1_REPEATED_EXECUTION"],
    "uncertainty_signals": []
  },
  "reasoning": "Explainable natural language justification citing observable evidence"
}
```

---

## 5. Temporal Prefix Experiment Framework

To evaluate how struggle assessment evolves over time, the experimentation framework evaluates trajectory prefixes dynamically for $t = 1 \dots N$:

```
Prefix Trajectory Evaluation:
Attempt t=1:  [M1 Snapshot]  [M2 Rule-Based]  [M3 LLM]
Attempt t=2:  [M1 Snapshot]  [M2 Rule-Based]  [M3 LLM]
Attempt t=3:  [M1 Snapshot]  [M2 Rule-Based]  [M3 LLM]
...
Attempt t=N:  [M1 Snapshot]  [M2 Rule-Based]  [M3 LLM]
```

This structure enables analyzing:
- Assessment stability over attempt sequences.
- Onset detection speed (at which attempt $t$ unproductive struggle is first flagged).
- State transitions (e.g. `UNCERTAIN` at $t=1 \rightarrow$ `PRODUCTIVE` at $t=3$).

---

## 6. Method Agreement & Disagreement Analysis

### Critical Distinction: Agreement $\neq$ Accuracy
In the absence of human gold-standard labels, overlapping assessments across methods represent **method agreement**, NOT empirical accuracy validation.

### Metrics & Disagreement Explanations
We calculate:
- Pairwise agreement rates: $\text{Agr}(M1, M2)$, $\text{Agr}(M1, M3)$, $\text{Agr}(M2, M3)$.
- 3-Way consensus agreement: $\text{Agr}(M1, M2, M3)$.
- Disagreement counts and location identification in attempt trajectories.
- Natural language disagreement explanations (e.g. *Rule detects static code repetition, whereas LLM identifies error resolution as positive progression*).

---

## 7. Controlled Trajectory Patterns (P1 .. P10)

To test expected methodological behaviors across edge cases, we define 10 controlled behavioral scenarios:

1. **P1 (Monotonic Progression)**: $0/10 \rightarrow 2/10 \rightarrow 5/10 \rightarrow 8/10 \rightarrow 10/10$.
2. **P2 (Persistent Stagnation)**: $0/10 \rightarrow 0/10 \rightarrow 0/10 \rightarrow 0/10 \rightarrow 0/10$ (identical code/error).
3. **P3 (Error Evolution)**: Compile Error $\rightarrow$ Runtime Error $\rightarrow$ Wrong Answer $\rightarrow 5/10 \rightarrow 8/10$.
4. **P4 (Exploration Without Feedback)**: Code A $\rightarrow$ Code B $\rightarrow$ Code C (no execution/test evaluations).
5. **P5 (Stagnation $\rightarrow$ Recovery)**: $0/10 \rightarrow 0/10 \rightarrow 0/10 \rightarrow 5/10 \rightarrow 8/10$.
6. **P6 (Cyclic Exploration)**: Code A $\rightarrow$ Code B $\rightarrow$ Code A $\rightarrow$ Code B (zero score gain).
7. **P7 (Mixed Evidence)**: Repeated error $\rightarrow$ major code change $\rightarrow$ same score $\rightarrow$ different error.
8. **P8 (Temporary Regression)**: $5/10 \rightarrow 3/10 \rightarrow 6/10 \rightarrow 8/10$ (temporary test dip during refactoring).
9. **P9 (Fast Success)**: $0/10 \rightarrow 10/10$ (2 attempts).
10. **P10 (Long Failure With Exploration)**: $0/10 \rightarrow 0/10 \rightarrow 1/10 \rightarrow 0/10 \rightarrow 2/10 \rightarrow 3/10$ (weak, slow progress).

### Expected Methodological Behaviors
- **P1**: High positive progression signals across M2/M3.
- **P2**: High repetition/stagnation negative signals across M2/M3; M1 remains static.
- **P3**: Changing error types must NOT be penalized as unproductive struggle.
- **P4**: Lack of outcome feedback must output `UNCERTAIN` rather than assuming productive learning.
- **P5**: Early prefix ($t=3$) should assess `UNPRODUCTIVE`, later prefix ($t=5$) should assess `PRODUCTIVE` (stagnation escape).
- **P8**: Temporary score regression during active code modification should avoid immediate `UNPRODUCTIVE` classification.

---

## 8. Human Annotation Schema (Future Study)

When human/expert pedagogical annotations are collected, each prefix assessment will adhere to the following schema:

```json
{
  "annotation_id": "ann_20260914_001",
  "annotator_id": "expert_pedagogue_01",
  "user_id": "user_3JH0gS2vXtbFlXI4VTQhLXXJG2m",
  "problem_id": "find-the-number-of-even-elements-in-an-array",
  "assessment_attempt": 5,
  "label": "PRODUCTIVE | UNPRODUCTIVE | UNCERTAIN",
  "confidence": 4,
  "rationale": "Student resolved compilation error and introduced a valid loop structure, though logic is still incomplete."
}
```

---

## 9. Future Evaluation Metrics & Leakage Prevention

### Evaluation Metrics (Post-Annotation)
Upon availability of human ground truth labels:
- Multi-class **Macro F1**, **Per-Class F1** (`PRODUCTIVE`, `UNPRODUCTIVE`, `UNCERTAIN`), and **Balanced Accuracy**.
- **Confusion Matrix** analysis.
- Inter-annotator agreement using **Cohen's Kappa** ($\kappa$) or **Fleiss' Kappa** ($\kappa_{fleiss}$).

### Train/Test Data Leakage Prevention
When training or validating supervised models in future tasks:
- **Student-Level Splitting**: Trajectory prefixes belonging to the same student MUST reside entirely in either the training set or testing set.
- **No Prefix Cross-Over**: Never split $t=3$ into train and $t=4$ into test for the same student trajectory.

---

## 10. Research JSON Export Schema

Research experiment exports are output in structured, pandas-friendly JSON format:

```json
{
  "experiment_id": "exp_20260914_011727",
  "timestamp": "2026-09-14T01:17:27Z",
  "user_id": "user_3JH0gS2vXtbFlXI4VTQhLXXJG2m",
  "problem_id": "find-the-number-of-even-elements-in-an-array",
  "trajectory_length": 20,
  "evaluations": [
    {
      "attempt": 1,
      "snapshot": { "state": "UNCERTAIN", "confidence": 0.5 },
      "rule_based": { "state": "UNCERTAIN", "confidence": 0.5 },
      "llm": { "state": "UNCERTAIN", "confidence": 0.5, "model": "meta-llama/llama-3.3-70b-instruct" }
    }
  ],
  "agreement_summary": {
    "overall_3way_agreement_rate": 0.75,
    "rule_vs_llm_agreement_rate": 0.85
  }
}
```

---

## 11. Research Reproducibility Standards (Audit Task 2F-A)

To ensure strict scientific reproducibility before human expert annotation:

1. **Strict Model Pinning (`strict_model_pinning=True`)**:
   - The application runtime path retains candidate model fallbacks for service resilience.
   - The **Research Experimentation Path** (`run_prefix_experiment`, `run_controlled_experiment`) enforces strict model pinning.
   - If the pinned research model (`meta-llama/llama-3.3-70b-instruct`) fails or is unavailable, the research path explicitly outputs an error dictionary without silently substituting alternate models.

2. **Explicit Prompt & Configuration Versioning**:
   - Every assessment output and exported JSON dataset records explicit version identifiers:
     - `rule_config_version`: `"TASK_2B_RULE_V1"`
     - `hybrid_config_version`: `"2E_HYBRID_PROVISIONAL_V1"`
     - `prompt_version`: `"TASK_2C_SYSTEM_V1"`
     - `llm_model`: Pinned model identifier string.
     - `strict_model_pinning`: `True`.

3. **Prefix Isolation Guarantee**:
   - Prefix evaluations at step $t$ consume strictly attempts $A_1 \dots A_t$.
   - Feature extraction, rule assessment, LLM prompt construction, and hybrid fusion guarantee zero access to attempts $A_{t+1} \dots A_N$.

4. **Same-Input Comparison Integrity**:
   - Methods M1 (Snapshot), M2 (Rule), M3 (LLM), and M4 (Hybrid) are evaluated on the exact same trajectory prefix payload $A_1 \dots A_t$.

---

## 12. System Limitations & Confidence Operational Bounds

1. **No Ground Truth Assumption**: None of M1, M2, M3, or M4 represent absolute truth or validated gold standards.
2. **Provisional Operational Status**: Current heuristics, prompts, and fusion rules are research candidates under evaluation.
3. **Operational Heuristic Bounds**: Heuristic confidence scores (e.g., `0.95` or `1.00` in hybrid consensus) represent the configured upper bound of the operational evidence heuristic, NOT calibrated statistical probabilities or empirical gold-standard certainty.
4. **Zero Platform Side-Effects**: Assessment APIs do NOT trigger automatic hint interventions or UI modifications.

---

## 13. Methodological Limitations & Human Reference Protocol (Task 2F-B)

1. **Human Annotation as Reference Standard**: Human expert annotation serves as the reference standard for planned empirical validation, but human labels do not constitute infallible ground truth.
2. **Annotator Agreement Expectations**: Inter-rater disagreement is expected, particularly on short ($t=1$) or structurally complex trajectory prefixes.
3. **Legitimate `UNCERTAIN` Class**: `UNCERTAIN` is intentionally retained as a distinct 3rd primary class across all datasets, agreement metrics (Cohen's $\kappa$, Fleiss' $\kappa$), and evaluation matrices to explicitly capture trajectory ambiguity and missing feedback.
4. **Student-Level Grouping & Split Isolation**: All future empirical train/test evaluations MUST split at the student level (`student_id`), ensuring no trajectory prefixes from the same student appear across both splits.
5. **Separation of Annotation and Model Datasets**: Human annotation records are strictly stored and exported independently from model predictions (M1..M4), preventing label contamination.


