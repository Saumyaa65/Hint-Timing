import os
import sys
import json
import csv
from datetime import datetime, timezone

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hint_system.settings')

import django
django.setup()

from hints.models import Attempt, Problem, UserProfile, HintDelivery
from django.contrib.auth.models import User

def perform_audit():
    print("=" * 80)
    print("STARTING DATASET AUDIT")
    print("=" * 80)

    attempts = list(Attempt.objects.select_related('problem').all().order_by('created_at'))
    total_attempts_count = len(attempts)
    print(f"Total Attempt records in DB: {total_attempts_count}")

    # Fetch User Profiles to identify test accounts
    profiles = {p.clerk_id: p for p in UserProfile.objects.all() if p.clerk_id}
    test_user_ids = {p.clerk_id for p in UserProfile.objects.filter(is_test_account=True) if p.clerk_id}
    
    # Also check Django Users marked as test/staff if applicable
    staff_usernames = set(User.objects.filter(is_staff=True).values_list('username', flat=True))

    # Group attempts by session_id
    # If session_id is None or empty string, assign a synthetic key 'ORPHANED_<user_id>_<problem_id>' or 'ORPHANED_UNGROUPED'
    sessions_map = {}
    orphaned_count = 0

    for att in attempts:
        sid = att.session_id.strip() if att.session_id else ""
        if not sid:
            sid = f"LEGACY_ORPHANED_{att.user_id or 'UNKNOWN'}_{att.problem.problem_id if att.problem else 'UNKNOWN'}"
            orphaned_count += 1
        
        if sid not in sessions_map:
            sessions_map[sid] = []
        sessions_map[sid].append(att)

    print(f"Total Session groups formed: {len(sessions_map)}")

    # Audit individual sessions
    session_summaries = []
    data_quality_issues = []

    # Trackers for dataset-level metrics
    all_students = set()
    all_problems = set()
    
    valid_sessions = []
    invalid_sessions = []

    single_attempt_sessions = 0
    multi_attempt_sessions = 0

    student_valid_trajectories = {} # user_id -> count of valid sessions
    student_valid_problems = {}     # user_id -> set of problem_ids

    for sid, att_list in sessions_map.items():
        # Sort chronologically
        att_list.sort(key=lambda x: x.created_at)

        is_orphaned = sid.startswith("LEGACY_ORPHANED")
        
        # User details
        users_in_session = list(set(a.user_id for a in att_list if a.user_id))
        primary_user = users_in_session[0] if users_in_session else "MISSING_USER"
        if primary_user != "MISSING_USER":
            all_students.add(primary_user)
        
        # Data quality check: Multiple users in one session_id
        if len(users_in_session) > 1:
            data_quality_issues.append({
                'session_id': sid,
                'issue_type': 'Mixed Users in Session',
                'description': f"Session contains attempts from multiple users: {users_in_session}"
            })

        # Problem details
        problems_in_session = list(set(a.problem.problem_id if a.problem else "MISSING_PROBLEM" for a in att_list))
        primary_problem_id = problems_in_session[0] if problems_in_session else "MISSING_PROBLEM"
        primary_problem_title = att_list[0].problem.title if (att_list[0].problem) else "MISSING_PROBLEM"
        if primary_problem_id != "MISSING_PROBLEM":
            all_problems.add(primary_problem_id)

        # Data quality check: Mixed problems in one session_id
        if len(problems_in_session) > 1:
            data_quality_issues.append({
                'session_id': sid,
                'issue_type': 'Mixed Problems in Session',
                'description': f"Session contains attempts across multiple problems: {problems_in_session}"
            })

        # Timestamps and duration
        first_ts = att_list[0].created_at
        last_ts = att_list[-1].created_at
        duration_seconds = (last_ts - first_ts).total_seconds()

        mins = int(duration_seconds // 60)
        secs = int(duration_seconds % 60)
        duration_str = f"{mins}m {secs}s" if mins > 0 else f"{secs}s"

        # Action / Source sequence
        actions = [a.source for a in att_list]
        actions_seq_str = " -> ".join(actions)

        # Unique code versions
        codes = [a.code for a in att_list]
        unique_codes = set(codes)
        num_unique_codes = len(unique_codes)

        # Data quality checks per attempt
        has_missing_code = any(not a.code or not a.code.strip() for a in att_list)
        if has_missing_code:
            data_quality_issues.append({
                'session_id': sid,
                'issue_type': 'Missing Code Content',
                'description': f"One or more attempts in session have empty or missing code content."
            })

        has_missing_timestamp = any(a.created_at is None for a in att_list)
        if has_missing_timestamp:
            data_quality_issues.append({
                'session_id': sid,
                'issue_type': 'Missing Timestamp',
                'description': f"One or more attempts in session have missing timestamp."
            })

        # Duplicate attempt check (same code submitted multiple times within 2 seconds)
        duplicate_count = 0
        for i in range(1, len(att_list)):
            prev_a = att_list[i-1]
            curr_a = att_list[i]
            if prev_a.code == curr_a.code and (curr_a.created_at - prev_a.created_at).total_seconds() < 2:
                duplicate_count += 1
        if duplicate_count > 0:
            data_quality_issues.append({
                'session_id': sid,
                'issue_type': 'Rapid Duplicate Attempt',
                'description': f"Found {duplicate_count} rapid duplicate attempt submissions (< 2s interval with identical code)."
            })

        # Check attempt count breakdown
        att_count = len(att_list)
        if att_count == 1:
            single_attempt_sessions += 1
        else:
            multi_attempt_sessions += 1

        # Suspiciously short multi-attempt sessions check
        if att_count > 1 and duration_seconds == 0:
            data_quality_issues.append({
                'session_id': sid,
                'issue_type': 'Zero Duration Multi-Attempt',
                'description': f"Session has {att_count} attempts but total duration is 0 seconds."
            })

        # Validity & Classification Logic
        # Is user a test/developer account?
        is_test_user = (primary_user in test_user_ids) or (primary_user in staff_usernames) or ("test" in primary_user.lower())
        
        validity_status = "INVALID"
        classification = "UNKNOWN"

        if is_orphaned:
            validity_status = "INVALID"
            classification = "ORPHANED_LEGACY_SESSION"
            data_quality_issues.append({
                'session_id': sid,
                'issue_type': 'Missing session_id',
                'description': f"Legacy attempts ({att_count} attempts) missing session_id grouping."
            })
        elif is_test_user:
            validity_status = "INVALID"
            classification = "DEVELOPER_TEST_SESSION"
        elif att_count == 1:
            # Single attempt session: classified as single isolated attempt
            validity_status = "INVALID" # Only 1 attempt doesn't provide a multi-step problem-solving trajectory
            classification = "ISOLATED_SINGLE_ATTEMPT"
        elif att_count >= 2 and num_unique_codes >= 2:
            validity_status = "VALID"
            classification = "GENUINE_STUDENT_TRAJECTORY"
        elif att_count >= 2 and num_unique_codes == 1:
            # Multiple attempts with zero code change
            validity_status = "INVALID"
            classification = "REPETITIVE_NO_CODE_CHANGE_SESSION"
            data_quality_issues.append({
                'session_id': sid,
                'issue_type': 'No Code Variation',
                'description': f"Session has {att_count} attempts but only 1 unique code version."
            })
        else:
            validity_status = "INVALID"
            classification = "NON_RESEARCH_SESSION"

        # Record summary
        summary_entry = {
            'session_id': sid,
            'student_user': primary_user,
            'problem_id': primary_problem_id,
            'problem_title': primary_problem_title,
            'num_attempts': att_count,
            'first_timestamp': first_ts.isoformat(),
            'last_timestamp': last_ts.isoformat(),
            'duration_seconds': round(duration_seconds, 2),
            'duration_formatted': duration_str,
            'sequence_of_actions': actions_seq_str,
            'num_unique_code_versions': num_unique_codes,
            'validity_status': validity_status,
            'classification': classification
        }

        session_summaries.append(summary_entry)

        if validity_status == "VALID":
            valid_sessions.append(summary_entry)
            student_valid_trajectories[primary_user] = student_valid_trajectories.get(primary_user, 0) + 1
            if primary_user not in student_valid_problems:
                student_valid_problems[primary_user] = set()
            student_valid_problems[primary_user].add(primary_problem_id)
        else:
            invalid_sessions.append(summary_entry)

    # Calculate aggregate stats
    total_sessions_count = len(sessions_map)
    total_students_count = len(all_students)
    total_unique_problems_count = len(all_problems)
    
    valid_sessions_count = len(valid_sessions)
    invalid_sessions_count = len(invalid_sessions)

    valid_attempt_counts = [s['num_attempts'] for s in valid_sessions]
    avg_attempts_per_valid = (sum(valid_attempt_counts) / valid_sessions_count) if valid_sessions_count > 0 else 0
    min_attempts_valid = min(valid_attempt_counts) if valid_sessions_count > 0 else 0
    max_attempts_valid = max(valid_attempt_counts) if valid_sessions_count > 0 else 0

    print("\n" + "="*80)
    print("DATASET-LEVEL SUMMARY METRICS")
    print("="*80)
    print(f"Total Number of Sessions: {total_sessions_count}")
    print(f"Total Number of Students: {total_students_count}")
    print(f"Total Number of Unique Problems Attempted: {total_unique_problems_count}")
    print(f"Total Number of Attempts in DB: {total_attempts_count}")
    print(f"Number of VALID Sessions: {valid_sessions_count}")
    print(f"Number of INVALID / Test / Developer / Single Sessions: {invalid_sessions_count}")
    print(f"Number of Sessions with only 1 attempt: {single_attempt_sessions}")
    print(f"Number of Sessions with 2+ attempts: {multi_attempt_sessions}")
    print(f"Average Attempts per Valid Session: {avg_attempts_per_valid:.2f}")
    print(f"Minimum Attempts per Valid Session: {min_attempts_valid}")
    print(f"Maximum Attempts per Valid Session: {max_attempts_valid}")

    # Write Session-Level Summary CSV
    csv_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataset_audit_session_summary.csv')
    fieldnames = [
        'session_id', 'student_user', 'problem_id', 'problem_title', 'num_attempts',
        'first_timestamp', 'last_timestamp', 'duration_seconds', 'duration_formatted',
        'sequence_of_actions', 'num_unique_code_versions', 'validity_status', 'classification'
    ]

    with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(session_summaries)

    print(f"\nSaved session-level summary CSV to: {csv_file_path}")

    # Prepare Student-Level Summary Table Data
    student_summaries = []
    for stud in sorted(all_students):
        total_stud_sessions = sum(1 for s in session_summaries if s['student_user'] == stud)
        total_stud_attempts = sum(s['num_attempts'] for s in session_summaries if s['student_user'] == stud)
        valid_trajs = student_valid_trajectories.get(stud, 0)
        valid_probs = len(student_valid_problems.get(stud, set()))
        
        student_summaries.append({
            'student_user': stud,
            'total_sessions': total_stud_sessions,
            'valid_sessions': valid_trajs,
            'valid_problems_attempted': valid_probs,
            'total_attempts': total_stud_attempts
        })

    return {
        'total_sessions': total_sessions_count,
        'total_students': total_students_count,
        'total_problems': total_unique_problems_count,
        'total_attempts': total_attempts_count,
        'valid_sessions': valid_sessions_count,
        'invalid_sessions': invalid_sessions_count,
        'single_attempt_sessions': single_attempt_sessions,
        'multi_attempt_sessions': multi_attempt_sessions,
        'avg_attempts_per_valid': avg_attempts_per_valid,
        'min_attempts_valid': min_attempts_valid,
        'max_attempts_valid': max_attempts_valid,
        'session_summaries': session_summaries,
        'student_summaries': student_summaries,
        'data_quality_issues': data_quality_issues,
        'csv_file_path': csv_file_path
    }

if __name__ == '__main__':
    perform_audit()
