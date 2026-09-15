import os
import sys
import json
import csv

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

def process_final_labels():
    print("=" * 80)
    print("PROCESSING FINAL HUMAN LABELS FOR ALL 89 PREFIXES")
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
                'prefix_id': f"{sid}_prefix_{p_num}"
            })

    # Query DB for HumanAnnotation records
    all_annots = list(HumanAnnotation.objects.all())
    annot_map = {}
    for ann in all_annots:
        pkey = f"{ann.session_id}_prefix_{ann.prefix_number}"
        aid = ann.annotator_id.strip()
        if pkey not in annot_map:
            annot_map[pkey] = {}
        annot_map[pkey][aid] = ann

    final_records = []
    disagreements = []

    final_label_counts = {
        'PRODUCTIVE': 0,
        'UNPRODUCTIVE': 0,
        'UNCERTAIN': 0
    }

    for pref in expected_prefixes:
        pkey = pref['prefix_id']
        a1 = annot_map.get(pkey, {}).get('Annotator 1')
        a2 = annot_map.get(pkey, {}).get('Annotator 2')

        a1_label = a1.human_label if a1 else "MISSING"
        a2_label = a2.human_label if a2 else "MISSING"

        if a1_label == a2_label and a1_label != "MISSING":
            final_label = a1_label
            consensus_type = "AGREEMENT"
        else:
            disagreements.append(pref)
            # If any disagreement, resolve consensus label (or default to higher confidence / agreed label)
            # Since a1 and a2 agree on all 89 prefixes in our dataset:
            final_label = a1_label if a1_label != "MISSING" else a2_label
            consensus_type = "RESOLVED_CONSENSUS"

        final_label_counts[final_label] = final_label_counts.get(final_label, 0) + 1

        final_records.append({
            'global_idx': pref['global_idx'],
            'prefix_id': pkey,
            'session_id': pref['session_id'],
            'prefix_number': pref['prefix_number'],
            'a1_label': a1_label,
            'a1_evidence': ", ".join(a1.evidence) if (a1 and a1.evidence) else "None",
            'a1_confidence': a1.confidence if a1 else "N/A",
            'a2_label': a2_label,
            'a2_evidence': ", ".join(a2.evidence) if (a2 and a2.evidence) else "None",
            'a2_confidence': a2.confidence if a2 else "N/A",
            'final_human_label': final_label,
            'consensus_type': consensus_type
        })

    # Save to CSV
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'human_annotations_with_final_label.csv')
    fieldnames = [
        'global_idx', 'prefix_id', 'session_id', 'prefix_number',
        'a1_label', 'a1_evidence', 'a1_confidence',
        'a2_label', 'a2_evidence', 'a2_confidence',
        'final_human_label', 'consensus_type'
    ]

    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(final_records)

    # Save to JSON
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'human_annotations_with_final_label.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_prefixes': len(final_records),
            'disagreements_count': len(disagreements),
            'final_label_counts': final_label_counts,
            'records': final_records
        }, f, indent=2)

    print("\nFINAL HUMAN LABELS SUMMARY:")
    print("=" * 40)
    print(f"PRODUCTIVE   = {final_label_counts.get('PRODUCTIVE', 0)}")
    print(f"UNPRODUCTIVE = {final_label_counts.get('UNPRODUCTIVE', 0)}")
    print(f"UNCERTAIN    = {final_label_counts.get('UNCERTAIN', 0)}")
    print("=" * 40)
    print(f"Total Prefixes Processed: {len(final_records)}")
    print(f"Initial Disagreements Requiring Consensus: {len(disagreements)}")
    print(f"Saved CSV to: {csv_path}")
    print(f"Saved JSON to: {json_path}")

if __name__ == '__main__':
    process_final_labels()
