import csv
import os
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.conf import settings
from .models import Attempt, Problem, HumanAnnotation

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

class AnnotationPrefixesView(APIView):
    """
    Returns trajectory prefixes for the 15 valid research sessions.
    GET /api/human-annotation/prefixes/?annotator_id=Annotator+1
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        annotator_id = request.query_params.get('annotator_id', 'Annotator 1').strip()

        # Fetch attempt objects for valid sessions
        attempts = list(Attempt.objects.filter(session_id__in=VALID_SESSION_IDS).select_related('problem').order_by('created_at'))

        sessions_map = {}
        for sid in VALID_SESSION_IDS:
            sessions_map[sid] = []

        for att in attempts:
            if att.session_id in sessions_map:
                sessions_map[att.session_id].append(att)

        # Pre-fetch existing annotations for this annotator_id
        existing_annotations = {}
        if annotator_id:
            annot_qs = HumanAnnotation.objects.filter(annotator_id=annotator_id)
            for ann in annot_qs:
                key = f"{ann.session_id}_prefix_{ann.prefix_number}"
                existing_annotations[key] = {
                    'human_label': ann.human_label,
                    'evidence': ann.evidence,
                    'confidence': ann.confidence,
                    'updated_at': ann.updated_at.isoformat()
                }

        prefixes_list = []
        global_prefix_index = 0

        for sid in VALID_SESSION_IDS:
            att_list = sessions_map[sid]
            if len(att_list) < 2:
                continue

            att_list.sort(key=lambda x: x.created_at)
            n_atts = len(att_list)

            student_user = att_list[0].user_id or "Student"
            problem_title = att_list[0].problem.title if att_list[0].problem else "Problem"
            problem_id = att_list[0].problem.problem_id if att_list[0].problem else "problem"

            # Create prefixes for steps A1..A2, A1..A3, ..., A1..An
            for prefix_num in range(1, n_atts):
                global_prefix_index += 1
                prefix_step_limit = prefix_num + 1  # prefix 1 is steps 1..2, prefix 2 is steps 1..3
                prefix_attempts = att_list[:prefix_step_limit]

                attempts_payload = []
                for idx, a in enumerate(prefix_attempts, 1):
                    attempts_payload.append({
                        'attempt_number': idx,
                        'created_at': a.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
                        'source': a.source,
                        'code': a.code,
                        'status': a.status,
                        'execution_time': a.execution_time,
                        'evaluation_details': a.evaluation_details
                    })

                key = f"{sid}_prefix_{prefix_num}"
                existing_ann = existing_annotations.get(key, None)

                prefixes_list.append({
                    'global_prefix_index': global_prefix_index,
                    'session_id': sid,
                    'prefix_number': prefix_num,
                    'total_prefixes_in_session': n_atts - 1,
                    'student_user': student_user,
                    'problem_title': problem_title,
                    'problem_id': problem_id,
                    'total_session_attempts': n_atts,
                    'current_prefix_attempts_count': prefix_step_limit,
                    'attempts': attempts_payload,
                    'existing_annotation': existing_ann
                })

        return Response({
            'annotator_id': annotator_id,
            'valid_sessions_count': len(valid_sessions_map_keys := [s for s in VALID_SESSION_IDS if len(sessions_map[s]) >= 2]),
            'total_prefixes': len(prefixes_list),
            'prefixes': prefixes_list
        }, status=status.HTTP_200_OK)


class SubmitAnnotationView(APIView):
    """
    Submits or updates a human annotation for a specific session prefix.
    POST /api/human-annotation/submit/
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        session_id = data.get('session_id')
        prefix_number = data.get('prefix_number')
        annotator_id = data.get('annotator_id', 'Annotator 1').strip()
        human_label = data.get('human_label')
        evidence = data.get('evidence', [])
        confidence = data.get('confidence', 'Medium')

        if not session_id or prefix_number is None or not human_label:
            return Response(
                {'error': 'Missing required fields: session_id, prefix_number, human_label'},
                status=status.HTTP_400_BAD_REQUEST
            )

        annotation, created = HumanAnnotation.objects.update_or_create(
            session_id=session_id,
            prefix_number=prefix_number,
            annotator_id=annotator_id,
            defaults={
                'human_label': human_label,
                'evidence': evidence,
                'confidence': confidence
            }
        )

        return Response({
            'status': 'success',
            'created': created,
            'annotation': {
                'id': annotation.id,
                'session_id': annotation.session_id,
                'prefix_number': annotation.prefix_number,
                'annotator_id': annotation.annotator_id,
                'human_label': annotation.human_label,
                'evidence': annotation.evidence,
                'confidence': annotation.confidence,
                'updated_at': annotation.updated_at.isoformat()
            }
        }, status=status.HTTP_200_OK)
