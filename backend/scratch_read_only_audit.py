import os
import sys
import json
import csv
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hint_system.settings')
import django
django.setup()

from django.db import connection
from django.apps import apps
from django.contrib.auth.models import User
from hints.models import UserProfile, Problem, ProblemSheet, SheetProblem, DailyProblem, UserProgress, Attempt, Hint, HintDelivery
from struggle_analysis.config import is_research_valid_session, is_research_valid_user

AUDIT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db_audit")
os.makedirs(AUDIT_DIR, exist_ok=True)

print("=" * 80)
print("STARTING READ-ONLY FORENSIC DATABASE AUDIT")
print("=" * 80)

# 1. Model and Table Counts
table_counts = {}
with connection.cursor() as cursor:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]

print("\n--- RAW SQLITE TABLES & ROW COUNTS ---")
for t_name in sorted(tables):
    with connection.cursor() as cursor:
        cursor.execute(f'SELECT COUNT(*) FROM "{t_name}"')
        count = cursor.fetchone()[0]
        table_counts[t_name] = count
        print(f"Table: {t_name:40s} | Row Count: {count}")

# 2. Export Django Models to CSV & JSON Snapshot
snapshot_data = {}

def export_queryset_to_csv(filename, fieldnames, rows_data):
    filepath = os.path.join(AUDIT_DIR, filename)
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows_data:
            # Convert non-string objects (dicts, lists, datetimes) to json/str
            formatted_row = {}
            for k, v in row.items():
                if isinstance(v, (dict, list)):
                    formatted_row[k] = json.dumps(v, default=str)
                elif isinstance(v, datetime):
                    formatted_row[k] = v.isoformat()
                else:
                    formatted_row[k] = v if v is not None else ""
            writer.writerow(formatted_row)
    print(f"Exported {len(rows_data)} rows to {filename}")

# --- Export Users ---
user_rows = []
for u in User.objects.all():
    user_rows.append({
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'first_name': u.first_name,
        'last_name': u.last_name,
        'is_staff': u.is_staff,
        'is_superuser': u.is_superuser,
        'is_active': u.is_active,
        'date_joined': u.date_joined,
        'last_login': u.last_login
    })
export_queryset_to_csv('users.csv', ['id', 'username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'is_active', 'date_joined', 'last_login'], user_rows)
snapshot_data['users'] = user_rows

# --- Export UserProfiles ---
profile_rows = []
for p in UserProfile.objects.all():
    profile_rows.append({
        'id': p.id,
        'user_id': p.user_id,
        'username': p.user.username if p.user else "",
        'clerk_id': p.clerk_id,
        'bio': p.bio,
        'total_score': p.total_score,
        'global_rank': p.global_rank,
        'is_test_account': p.is_test_account,
        'current_streak': p.current_streak,
        'longest_streak': p.longest_streak,
        'last_potd_attempt_date': p.last_potd_attempt_date,
        'created_at': p.created_at,
        'updated_at': p.updated_at
    })
export_queryset_to_csv('user_profiles.csv', ['id', 'user_id', 'username', 'clerk_id', 'bio', 'total_score', 'global_rank', 'is_test_account', 'current_streak', 'longest_streak', 'last_potd_attempt_date', 'created_at', 'updated_at'], profile_rows)
snapshot_data['user_profiles'] = profile_rows

# --- Export Problems ---
prob_rows = []
for pr in Problem.objects.all():
    prob_rows.append({
        'id': pr.id,
        'problem_id': pr.problem_id,
        'title': pr.title,
        'description': pr.description,
        'difficulty': pr.difficulty,
        'topic': pr.topic,
        'created_at': pr.created_at,
        'updated_at': pr.updated_at
    })
export_queryset_to_csv('problems.csv', ['id', 'problem_id', 'title', 'description', 'difficulty', 'topic', 'created_at', 'updated_at'], prob_rows)
snapshot_data['problems'] = prob_rows

# --- Export Attempts ---
att_rows = []
for a in Attempt.objects.all().order_by('created_at', 'id'):
    att_rows.append({
        'id': a.id,
        'user_id': a.user_id,
        'problem_id_fk': a.problem_id,
        'problem_id_str': a.problem.problem_id or str(a.problem.id),
        'problem_title': a.problem.title,
        'session_id': a.session_id or "",
        'source': a.source,
        'language': a.language,
        'status': a.status,
        'code': a.code,
        'execution_time': a.execution_time,
        'evaluation_details': a.evaluation_details,
        'created_at': a.created_at,
        'updated_at': a.updated_at
    })
export_queryset_to_csv('attempts.csv', ['id', 'user_id', 'problem_id_fk', 'problem_id_str', 'problem_title', 'session_id', 'source', 'language', 'status', 'code', 'execution_time', 'evaluation_details', 'created_at', 'updated_at'], att_rows)
snapshot_data['attempts'] = att_rows

# --- Export Hints ---
hint_rows = []
for h in Hint.objects.all():
    hint_rows.append({
        'id': h.id,
        'problem_id_fk': h.problem_id,
        'content': h.content,
        'level': h.level,
        'hint_type': h.hint_type,
        'created_at': h.created_at,
        'updated_at': h.updated_at
    })
export_queryset_to_csv('hints.csv', ['id', 'problem_id_fk', 'content', 'level', 'hint_type', 'created_at', 'updated_at'], hint_rows)
snapshot_data['hints'] = hint_rows

# --- Export HintDeliveries ---
delivery_rows = []
for hd in HintDelivery.objects.all():
    delivery_rows.append({
        'id': hd.id,
        'hint_id': hd.hint_id,
        'user_id': hd.user_id,
        'attempt_id': hd.attempt_id,
        'is_auto_triggered': hd.is_auto_triggered,
        'feedback': hd.feedback
    })
export_queryset_to_csv('hint_deliveries.csv', ['id', 'hint_id', 'user_id', 'attempt_id', 'is_auto_triggered', 'feedback'], delivery_rows)
snapshot_data['hint_deliveries'] = delivery_rows

# --- Export UserProgress ---
up_rows = []
for up in UserProgress.objects.all():
    up_rows.append({
        'id': up.id,
        'user_id': up.user_id,
        'problem_id_fk': up.problem_id,
        'attempts_count': up.attempts_count,
        'failed_attempts_count': up.failed_attempts_count,
        'current_hint_level': up.current_hint_level,
        'hints_requested': up.hints_requested,
        'last_activity': up.last_activity
    })
export_queryset_to_csv('user_progress.csv', ['id', 'user_id', 'problem_id_fk', 'attempts_count', 'failed_attempts_count', 'current_hint_level', 'hints_requested', 'last_activity'], up_rows)
snapshot_data['user_progress'] = up_rows

# Write full DB JSON snapshot
snapshot_path = os.path.join(AUDIT_DIR, "full_db_snapshot.json")
with open(snapshot_path, 'w', encoding='utf-8') as f:
    json.dump(snapshot_data, f, indent=2, default=str)
print(f"Full DB snapshot written to {snapshot_path}")

print("=" * 80)
print("AUDIT INITIALIZATION COMPLETE")
