import os
import sys
import json

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hint_system.settings')

import django
django.setup()

from hints.models import HumanAnnotation, Attempt

VALID_SESSION_IDS = [
    "sess_609d3fb5-b8fd-47be-b58b-477d5eb70157",
    "sess_11ac3d64-785b-45f5-8ce1-e32e2a5ece25",
    "sess_03787fdd-b97e-430b-b542-154f690c6c16",
    "sess_36262904-b141-47c4-b1ec-52886d9f7f19",
    "sess_82bb0a94-308c-4388-8a2a-5fc92a5347d6",
    "sess_66be4316-66d1-4d4f-98f5-a67b4cc1c08a",
    "sess_dc01ae80-4430-44d2-a011-3314a8822993",
    "sess_e788ae62-ff47-4e6a-bc8c-be55105fdc47",
    "sess_3dbfeb71-547f-49af-bdbe-94c6bfbfc792",
    "sess_f4e20c6b-c58a-42c0-aa40-b7f206aa2064",
    "sess_7e2ace9c-6b5a-41af-b23f-ce3e2d410c91",
    "sess_0f7e58ee-7e60-4830-acbe-4312aa6bfcc8",
    "sess_3df5dfba-c40b-4e08-a40c-64342b3503d6",
    "sess_37acefd7-b68d-4ac9-b574-60157405d126",
    "sess_e7390b18-e9db-4857-93c5-144e28ea666b"
]

def inspect_annotations():
    print("=" * 80)
    print("HUMAN ANNOTATIONS DATABASE INSPECTION")
    print("=" * 80)

    # Re-construct expected 89 prefixes list from DB attempts
    attempts = list(Attempt.objects.filter(session_id__in=VALID_SESSION_IDS).order_by('created_at'))
    sessions_map = {sid: [] for sid in VALID_SESSION_IDS}
    for att in attempts:
        if att.session_id in sessions_map:
            sessions_map[att.session_id].append(att)

    expected_prefixes = []
    global_idx = 0
    for sid in VALID_SESSION_IDS:
        att_list = sessions_map[sid]
        if len(att_list) < 2:
            continue
        n_atts = len(att_list)
        for p_num in range(1, n_atts):
            global_idx += 1
            expected_prefixes.append({
                'global_idx': global_idx,
                'session_id': sid,
                'prefix_number': p_num,
                'prefix_id': f"{sid}_prefix_{p_num}",
                'display_name': f"Prefix {global_idx} (Session {sid[:12]}... P{p_num})"
            })

    total_expected_prefixes = len(expected_prefixes)
    expected_annotations_count = total_expected_prefixes * 2

    # Fetch ALL HumanAnnotation objects from DB
    all_annots = list(HumanAnnotation.objects.all().order_by('session_id', 'prefix_number', 'annotator_id'))
    total_stored = len(all_annots)

    # Group by (session_id, prefix_number) and annotator_id
    annot_map = {} # prefix_key -> { annotator_id -> object }
    annotator_counts = {}
    unique_prefixes_annotated = set()
    duplicates = []

    seen_keys = set()
    for ann in all_annots:
        prefix_key = f"{ann.session_id}_prefix_{ann.prefix_number}"
        unique_prefixes_annotated.add(prefix_key)
        
        aid = ann.annotator_id.strip()
        annotator_counts[aid] = annotator_counts.get(aid, 0) + 1

        dedup_key = (ann.session_id, ann.prefix_number, aid)
        if dedup_key in seen_keys:
            duplicates.append(ann)
        else:
            seen_keys.add(dedup_key)

        if prefix_key not in annot_map:
            annot_map[prefix_key] = {}
        annot_map[prefix_key][aid] = ann

    ann1_count = annotator_counts.get('Annotator 1', 0)
    ann2_count = annotator_counts.get('Annotator 2', 0)

    # Check completeness
    prefixes_with_both = 0
    missing_annotations = 0

    prefix_comparison_table = []

    for pref in expected_prefixes:
        pkey = pref['prefix_id']
        a1 = annot_map.get(pkey, {}).get('Annotator 1')
        a2 = annot_map.get(pkey, {}).get('Annotator 2')

        if a1 and a2:
            prefixes_with_both += 1
        
        if not a1:
            missing_annotations += 1
        if not a2:
            missing_annotations += 1

        prefix_comparison_table.append({
            'global_idx': pref['global_idx'],
            'prefix_id': pkey,
            'session_id': pref['session_id'],
            'prefix_number': pref['prefix_number'],
            'a1_label': a1.human_label if a1 else "MISSING",
            'a1_confidence': a1.confidence if a1 else "N/A",
            'a1_evidence': ", ".join(a1.evidence) if (a1 and a1.evidence) else "None",
            'a2_label': a2.human_label if a2 else "MISSING",
            'a2_confidence': a2.confidence if a2 else "N/A",
            'a2_evidence': ", ".join(a2.evidence) if (a2 and a2.evidence) else "None",
            'status': "COMPLETE BOTH" if (a1 and a2) else ("PARTIAL" if (a1 or a2) else "MISSING BOTH")
        })

    print(f"1. Total annotation records stored: {total_stored}")
    print(f"2. Number of unique prefixes annotated: {len(unique_prefixes_annotated)} / {total_expected_prefixes}")
    print(f"3. Number of annotations by Annotator 1: {ann1_count}")
    print(f"4. Number of annotations by Annotator 2: {ann2_count}")
    print(f"5. Every one of the {total_expected_prefixes} prefixes has both annotations: {'YES' if prefixes_with_both == total_expected_prefixes else 'NO'}")
    print(f"   (Prefixes with both Annotator 1 & Annotator 2: {prefixes_with_both} / {total_expected_prefixes})")
    print(f"6. Missing records: {missing_annotations}, Duplicates: {len(duplicates)}")

    print("\n" + "=" * 80)
    print("FINAL SUMMARY REPORT")
    print("=" * 80)
    print(f"{total_expected_prefixes} prefixes × 2 annotators = {expected_annotations_count} expected annotations")
    print(f"{total_stored} found")
    print(f"{missing_annotations} missing")
    print(f"{len(duplicates)} duplicates")
    print("=" * 80)

    # Output detailed per-prefix comparison table
    print("\nPREFIX-BY-PREFIX ANNOTATION SUMMARY:")
    print("-" * 120)
    print(f"{'#':<4} | {'Prefix ID':<45} | {'Annotator 1 Label (Conf)':<28} | {'Annotator 2 Label (Conf)':<28} | Status")
    print("-" * 120)
    for r in prefix_comparison_table:
        a1_str = f"{r['a1_label']} ({r['a1_confidence']})" if r['a1_label'] != "MISSING" else "MISSING"
        a2_str = f"{r['a2_label']} ({r['a2_confidence']})" if r['a2_label'] != "MISSING" else "MISSING"
        print(f"{r['global_idx']:<4} | {r['prefix_id']:<45} | {a1_str:<28} | {a2_str:<28} | {r['status']}")

    # Save to a json snapshot for downstream evaluation if needed
    output_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'human_annotations_inspection.json')
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({
            'total_stored': total_stored,
            'unique_prefixes_annotated': len(unique_prefixes_annotated),
            'expected_prefixes': total_expected_prefixes,
            'ann1_count': ann1_count,
            'ann2_count': ann2_count,
            'prefixes_with_both': prefixes_with_both,
            'missing_annotations': missing_annotations,
            'duplicates_count': len(duplicates),
            'prefix_records': prefix_comparison_table
        }, f, indent=2)

    print(f"\nInspection results exported to: {output_json}")

if __name__ == '__main__':
    inspect_annotations()
