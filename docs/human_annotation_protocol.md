# Human/Expert Annotation Protocol for Programming Trajectory Struggle Assessment

**Protocol Version**: `TASK_2F_B_PROTOCOL_V1`  
**Research Focus**: Assessing Productive vs. Unproductive Struggle from Student Interaction Trajectories ($A_1 \dots A_t$).

---

## A. Research Objective

Our central research question is:
> *"Can we distinguish productive struggle from unproductive struggle, while appropriately representing uncertain or ambiguous cases, based on a student's programming interaction trajectory?"*

Struggle is evaluated as a **process over time**, not as a single code snapshot. Annotators evaluate trajectory prefixes $A_1 \rightarrow A_2 \rightarrow \dots \rightarrow A_t$, judging only the evidence available up to attempt $t$.

---

## B. Primary Labels Definition

Annotators must assign exactly one primary label to each trajectory prefix:

### 1. `PRODUCTIVE`
The trajectory provides evidence that the student's struggle is generating meaningful process evolution, such as:
- Meaningful progression in tests passed or test pass ratio.
- Error evolution (e.g., syntax error resolved to runtime/logical error) or error resolution.
- Active exploration of alternative algorithmic or syntactic approaches.
- Escaping previous code or state stagnation.
- Meaningful structural code evolution even if the final solution is not yet reached.

### 2. `UNPRODUCTIVE`
The trajectory provides evidence of sustained, ineffective struggle, such as:
- Repeated execution with little or no meaningful code change (trivial edits/whitespace).
- Repeated identical errors across consecutive attempts without adaptation.
- Persistent performance stagnation across multiple failure cycles.
- Cyclic/repetitive toggling between identical broken states without useful evolution.

### 3. `UNCERTAIN`
The trajectory provides insufficient or conflicting evidence for a clear judgment, such as:
- Crucial feedback or execution details are missing.
- Signals conflict (e.g., test score improved, but error recurred repeatedly).
- The trajectory length is too short to establish a process trend ($t=1$).
- The annotator cannot reliably distinguish productive from unproductive struggle.

> [!IMPORTANT]
> `UNCERTAIN` is a legitimate, first-class primary label—not a fallback for careless or incomplete annotation.

---

## C. Inclusion / Exclusion Rules

1. **Information Horizon**: Annotators MUST ONLY inspect interactions up to attempt $t$. Future attempts ($A_{t+1} \dots A_N$) or ultimate problem outcomes are strictly excluded to prevent hindsight bias.
2. **Model Masking**: Model predictions (Rule-Based, LLM, Hybrid, Snapshot) are strictly masked from annotators.
3. **Context Completeness**: A prefix payload must include code changes/diffs, test execution details, error messages, interaction types, and elapsed times.

---

## D. Examples of Productive Struggle
- **Scenario A**: Student starts with a Syntax Error ($A_1$), fixes syntax and gets 2/10 tests ($A_2$), refactors logic and gets 6/10 tests ($A_3$).
- **Scenario B**: Student remains stuck on 0/10 tests for 3 attempts, but code diffs show complete restructuring of the approach (looping logic $\rightarrow$ recursive strategy) with distinct error messages ($A_1 \dots A_3$).

## E. Examples of Unproductive Struggle
- **Scenario C**: Student submits code with `IndexError`, changes a single comment or variable name, re-runs 5 times receiving the exact same `IndexError` ($A_1 \dots A_5$).
- **Scenario D**: Student alternates between adding and removing the same `if` condition across 4 attempts with 0/10 tests passing continuously ($A_1 \dots A_4$).

## F. Examples of Ambiguous / Uncertain Struggle
- **Scenario E**: Student makes 1 attempt with a logical error. Too short to establish whether struggle is productive or unproductive ($A_1$).
- **Scenario F**: Test pass ratio increases from 2/10 to 5/10. But execution time explodes by $10\times$ and introduces a recursion depth warning ($A_1 \dots A_3$).

---

## G. Guidelines for Interpreting Trajectory Signals

### 1. Code Evolution
- **Significant Change**: Substantial structural edits or new helper methods indicate active problem-solving.
- **Trivial Edits**: Changing spacing, comments, or print statements during error states indicates stagnation.

### 2. Error Evolution
- **Resolving Errors**: Moving from compilation/syntax errors to logical errors indicates progress.
- **Persistent Error**: Receiving the exact same error on identical lines over multiple attempts indicates unproductive loop.

### 3. Test Pass & Performance Dynamics
- **Test Improvement**: Increasing pass ratio is strong positive evidence, but not strictly required for productive struggle.
- **Stagnation**: Constant test pass ratio across major code edits requires checking if the error or approach evolved.

### 4. Exploration & Stagnation
- **Approach Change**: Low similarity ($<0.5$) with new logic indicates productive exploration.
- **Stagnation Count**: $>3$ consecutive attempts with high similarity ($>0.85$) and zero test improvement indicates unproductive struggle.

---

## H. Explicit Hindsight & Bias Warnings

- > [!WARNING]
  > **Failure $\neq$ Unproductive**: A trajectory ending in a failed test at step $t$ can be `PRODUCTIVE` if the student is actively evolving their approach.

- > [!WARNING]
  > **Success $\neq$ Productive**: A trajectory where the student randomly guesses or hardcodes test cases might pass tests without productive learning.

- > [!WARNING]
  > **Code Editing $\neq$ Productive**: Modifying code lines without addressing the root error does not constitute productive effort.

- > [!WARNING]
  > **Zero Hindsight Bias**: Judge the trajectory strictly as it appears at step $t$. Do NOT assume what the student "would have done next."

---

## I. Structured Annotation Output Format

Annotators record their judgment using the following schema:

```json
{
  "annotation_id": "ann_20260914_001",
  "student_id": "anon_user_a7f9b2",
  "problem_id": "anon_prob_c4e1d3",
  "prefix_length": 4,
  "label": "PRODUCTIVE",
  "confidence": "HIGH",
  "rationale": "Student resolved IndexError in step 2 and increased test pass ratio from 0/10 to 7/10 in step 4 with active approach refactoring.",
  "evidence": {
    "progression": ["Test pass ratio improved from 0.0 to 0.7"],
    "error_evolution": ["IndexError resolved at step 2"],
    "exploration": ["Significant code edit at step 3 (similarity 0.42)"],
    "stagnation": [],
    "uncertainty": []
  },
  "annotator_id": "expert_reviewer_1",
  "annotation_version": "TASK_2F_B_PROTOCOL_V1",
  "timestamp": "2026-09-14T01:40:00Z"
}
```
