# Forensic Database Audit Report

**Audit Timestamp**: 2026-09-15T03:28:25.709786  
**Database Backend**: PostgreSQL (Django ORM `psycopg2`)  
**Audit Mode**: STRICT READ-ONLY (No data deleted, modified, or re-seeded)

---

## 1. Executive Database Summary

### Raw Database Tables & Row Counts

| Table Name | Description / Django Model | Exact Row Count |
|---|---|---|
| `auth_user` | Django User accounts | `1` |
| `hints_userprofile` | User Profiles (`UserProfile`) | `1` |
| `hints_problem` | Coding Problems (`Problem`) | `1618` |
| `hints_attempt` | Attempt Trajectory Records (`Attempt`) | `163` |
| `hints_hint` | System Hints (`Hint`) | `5141` |
| `hints_hintdelivery` | Hint Deliveries (`HintDelivery`) | `17` |
| `hints_userprogress` | User Progress (`UserProgress`) | `20` |
| `hints_problemsheet` | Problem Sheets (`ProblemSheet`) | `3` |
| `hints_sheetproblem` | Sheet Problems (`SheetProblem`) | `15` |
| `hints_dailyproblem` | Daily Problem (`DailyProblem`) | `2` |
| `auth_group` | Django Groups | `0` |
| `auth_permission` | Permissions | `84` |

---

## 2. Trajectory & Session Analysis

- **Total Attempt Records**: `163`
- **Total Distinct Session IDs**: `19`
- **Total Valid Research Sessions**: `15`
- **Total Orphaned / Disconnected Attempts**: `54`

### Inventory Breakdown by User

#### A. Saumya's Data (`user_3JH0gS2vXtbFlXI4VTQhLXXJG2m`)
- Total Sessions Recorded: `12`
- Authentic End-to-End Session (`sess_609d3fb5-b8fd-47be-58b-477d5eb70157`): **EXISTS & FULLY PRESERVED** (10 attempts, Java, chronological progression 13:18:50 to 13:24:41).
- Classification Breakdown:
  - **KEEP — newer research (~7–8)**: `sess_609d3fb5-b8fd-47be-58b-477d5eb70157` and valid research trajectories.
  - **KEEP — older Java testing (~2)**: Legacy attempt blocks (e.g. 20 attempts on `find-the-number-of-even-elements-in-an-array` and 8 attempts on `find-the-sum-of-all-positive-numbers-in-an-array`).
  - **LIKELY TEST/IRRELEVANT**: Single-attempt or starter-code-only test sessions (`sess_41212405...`, `sess_340708d6...`, `sess_3e64b548...`, `sess_3ad01ed2...`).

#### B. Kavya's Data (`user_3JKJBm2yRaTXc77M6Z6vy0DtFAx`)
- Total Sessions Recorded: `10`
- Valid Student Research Sessions: `10`
- Classification: **KEEP** (Contains genuine problem-solving trajectories across multiple C++ problems).

---

## 3. Disconnected & Orphaned Data Audit

- **Orphaned Attempt Count**: `54`
- **Primary Reason**: Attempts recorded prior to the implementation of `Attempt.session_id` column (e.g., fallback user `"1"`, test user `"123"`, and early testing attempts).
- **Action Taken**: **NONE**. (All records preserved untouched in database and cataloged in `orphaned_attempts.csv`).

---

## 4. Audit Artifacts Generated in `db_audit/`

The following export files were generated in `backend/db_audit/`:

1. `users.csv`
2. `user_profiles.csv`
3. `problems.csv`
4. `attempts.csv`
5. `hints.csv`
6. `hint_deliveries.csv`
7. `user_progress.csv`
8. `problem_sheets.csv`
9. `sheet_problems.csv`
10. `daily_problems.csv`
11. `full_db_snapshot.json`
12. `session_trajectory_inventory.csv`
13. `orphaned_attempts.csv`
14. `saumya_trajectory_inventory.csv`
15. `kavya_trajectory_inventory.csv`
16. `DB_FORENSIC_AUDIT_REPORT.md`

---

## 5. Verification of Known Session `sess_609d3fb5-b8fd-47be-58b-477d5eb70157`

- **Status**: **EXISTS IN DATABASE**
- **User**: `user_3JH0gS2vXtbFlXI4VTQhLXXJG2m` (Saumya)
- **Problem**: `find-the-number-of-negative-numbers-in-an-array`
- **Total Attempts**: 10 attempts ($A_1 \dots A_10$)
- **Chronological Sequence**:
  - $A_1$: ID 59 | `RUN`          | 0/4 passed | `java`
  - $A_2$: ID 60 | `HINT_REQUEST` | 0/4 passed | `javascript`
  - $A_3$: ID 61 | `RUN`          | 0/4 passed | `java`
  - $A_4$: ID 62 | `RUN`          | 0/4 passed | `java`
  - $A_5$: ID 63 | `RUN`          | 2/4 passed | `java`
  - $A_6$: ID 64 | `SUBMIT`       | 2/4 passed | `java`
  - $A_7$: ID 65 | `HINT_REQUEST` | 2/4 passed | `javascript`
  - $A_8$: ID 66 | `RUN`          | 4/4 passed | `java`
  - $A_9$: ID 67 | `SUBMIT`       | 4/4 passed | `java` (SUCCESS)
  - $A_10$: ID 68 | `HINT_REQUEST`| 4/4 passed | `javascript`

No data is missing or corrupted. All records remain 100% preserved.
