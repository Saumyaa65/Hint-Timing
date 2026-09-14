from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import TrajectoryFeature
from .serializers import TrajectoryFeatureSerializer
from .trajectory import build_trajectory
from .assessment import assess_prefix
from .llm_assessment import assess_prefix_with_llm
from .hybrid import assess_prefix_hybrid
from .comparison import compare_struggle_assessments
from .experiment import run_prefix_experiment, run_controlled_experiment, assess_with_method
from .annotation import generate_pilot_annotation_batch, export_annotation_batch, import_annotation_batch
from .evaluation import evaluate_model_performance

class TrajectoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Expose trajectory features for analysis purposes."""
    queryset = TrajectoryFeature.objects.all().order_by('created_at')
    serializer_class = TrajectoryFeatureSerializer
    permission_classes = [permissions.AllowAny]

class TrajectoryAnalysisView(APIView):
    """
    Research Trajectory Analysis Endpoint:
    GET /api/struggle-analysis/trajectory/<problem_id>/?user_id=<user_id>&max_attempts=<t>
    
    Returns structured interaction trajectory object representing the chronological
    attempt history, transition features across 6 research dimensions, and summary statistics.
    Supports online prefix temporal validity via optional max_attempts parameter (1 ... t).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, problem_id=None):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'Missing required query parameter: user_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not problem_id:
            return Response(
                {'error': 'Missing problem_id URL parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        max_attempts_param = request.query_params.get('max_attempts')
        max_attempts = None
        if max_attempts_param:
            try:
                max_attempts = int(max_attempts_param)
            except ValueError:
                return Response(
                    {'error': 'Invalid max_attempts parameter; must be an integer'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        trajectory_data = build_trajectory(
            user_id=user_id,
            problem_id_or_obj=problem_id,
            max_attempts=max_attempts
        )
        if "error" in trajectory_data:
            return Response(trajectory_data, status=status.HTTP_404_NOT_FOUND)

        return Response(trajectory_data, status=status.HTTP_200_OK)


class StruggleAssessmentView(APIView):
    """
    Research Struggle Assessment Baseline Endpoint:
    GET /api/struggle-analysis/assess/<problem_id>/?user_id=<user_id>&max_attempts=<t>
    
    Evaluates trajectory prefix (1 ... t) against the operational research baseline methodology,
    returning structured, explainable assessment (PRODUCTIVE | UNPRODUCTIVE | UNCERTAIN),
    heuristic confidence, evidence signals, and natural language reasoning.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, problem_id=None):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'Missing required query parameter: user_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not problem_id:
            return Response(
                {'error': 'Missing problem_id URL parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        max_attempts_param = request.query_params.get('max_attempts')
        max_attempts = None
        if max_attempts_param:
            try:
                max_attempts = int(max_attempts_param)
            except ValueError:
                return Response(
                    {'error': 'Invalid max_attempts parameter; must be an integer'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        assessment_result = assess_prefix(
            user_id=user_id,
            problem_id_or_obj=problem_id,
            max_attempts=max_attempts
        )
        if "error" in assessment_result:
            return Response(assessment_result, status=status.HTTP_404_NOT_FOUND)

        return Response(assessment_result, status=status.HTTP_200_OK)


class StruggleLLMAssessmentView(APIView):
    """
    Research LLM Trajectory Reasoning Endpoint:
    GET /api/struggle-analysis/llm-assess/<problem_id>/?user_id=<user_id>&max_attempts=<t>
    
    Evaluates trajectory prefix (1 ... t) using LLM trajectory reasoning,
    returning structured JSON assessment (PRODUCTIVE | UNPRODUCTIVE | UNCERTAIN),
    evidence observations, reasoning, and recommended action.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, problem_id=None):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'Missing required query parameter: user_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not problem_id:
            return Response(
                {'error': 'Missing problem_id URL parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        max_attempts_param = request.query_params.get('max_attempts')
        max_attempts = None
        if max_attempts_param:
            try:
                max_attempts = int(max_attempts_param)
            except ValueError:
                return Response(
                    {'error': 'Invalid max_attempts parameter; must be an integer'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        model_name = request.query_params.get('model')

        llm_result = assess_prefix_with_llm(
            user_id=user_id,
            problem_id_or_obj=problem_id,
            max_attempts=max_attempts,
            model_name=model_name
        )
        if "error" in llm_result and "trajectory_prefix" not in llm_result:
            return Response(llm_result, status=status.HTTP_404_NOT_FOUND if "not found" in str(llm_result.get("error")).lower() else status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(llm_result, status=status.HTTP_200_OK)


class StruggleComparisonView(APIView):
    """
    Research Assessment Comparison Utility Endpoint:
    GET /api/struggle-analysis/compare/<problem_id>/?user_id=<user_id>&max_attempts=<t>
    
    Runs BOTH Rule-Based Baseline and LLM Trajectory Reasoning methods on the exact same
    trajectory prefix (1 ... t) and compares operational outputs and agreement status.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, problem_id=None):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'Missing required query parameter: user_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not problem_id:
            return Response(
                {'error': 'Missing problem_id URL parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        max_attempts_param = request.query_params.get('max_attempts')
        max_attempts = None
        if max_attempts_param:
            try:
                max_attempts = int(max_attempts_param)
            except ValueError:
                return Response(
                    {'error': 'Invalid max_attempts parameter; must be an integer'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        model_name = request.query_params.get('model')

        comparison_result = compare_struggle_assessments(
            user_id=user_id,
            problem_id_or_obj=problem_id,
            max_attempts=max_attempts,
            model_name=model_name
        )
        if "error" in comparison_result:
            return Response(comparison_result, status=status.HTTP_404_NOT_FOUND)

        return Response(comparison_result, status=status.HTTP_200_OK)


class StruggleExperimentView(APIView):
    """
    Research Trajectory Prefix Experiment Endpoint:
    GET /api/struggle-analysis/experiment/<problem_id>/?user_id=<user_id>&model=<model>&include_llm=<true/false>
    
    Evaluates trajectory prefixes t=1...N across M1 (Snapshot), M2 (Rule-Based), and M3 (LLM Reasoning),
    returning structured temporal prefix evaluation matrix and method agreement summary.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, problem_id=None):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'Missing required query parameter: user_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not problem_id:
            return Response(
                {'error': 'Missing problem_id URL parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        model_name = request.query_params.get('model')
        include_llm_param = request.query_params.get('include_llm', 'true').lower()
        include_llm = include_llm_param not in ['false', '0', 'no']

        experiment_result = run_prefix_experiment(
            user_id=user_id,
            problem_id_or_obj=problem_id,
            model_name=model_name,
            include_llm=include_llm
        )
        if "error" in experiment_result:
            return Response(experiment_result, status=status.HTTP_404_NOT_FOUND)

        return Response(experiment_result, status=status.HTTP_200_OK)


class ControlledPatternView(APIView):
    """
    Research Controlled Trajectory Pattern Endpoint:
    GET /api/struggle-analysis/patterns/?pattern_id=<P1..P10>&include_llm=<true/false>
    
    Evaluates controlled behavioral trajectory scenarios P1..P10 against active methods.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        pattern_id = request.query_params.get('pattern_id')
        model_name = request.query_params.get('model')
        include_llm_param = request.query_params.get('include_llm', 'false').lower()
        include_llm = include_llm_param in ['true', '1', 'yes']

        pattern_result = run_controlled_experiment(
            pattern_id=pattern_id,
            include_llm=include_llm,
            model_name=model_name
        )
        if "error" in pattern_result:
            return Response(pattern_result, status=status.HTTP_400_BAD_REQUEST)

        return Response(pattern_result, status=status.HTTP_200_OK)


class StruggleHybridAssessmentView(APIView):
    """
    Research Hybrid Struggle Assessment Endpoint (Condition M4):
    GET /api/struggle-analysis/hybrid/<problem_id>/?user_id=<user_id>&max_attempts=<t>&model=<model>
    
    Evaluates trajectory prefix (1 ... t) using Hybrid Feature + LLM struggle assessment,
    fusing objective trajectory features & rule baseline signals (M2) with LLM trajectory reasoning (M3).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, problem_id=None):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'Missing required query parameter: user_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not problem_id:
            return Response(
                {'error': 'Missing problem_id URL parameter'},
                status=status.HTTP_400_BAD_REQUEST
            )

        max_attempts_param = request.query_params.get('max_attempts')
        max_attempts = None
        if max_attempts_param:
            try:
                max_attempts = int(max_attempts_param)
            except ValueError:
                return Response(
                    {'error': 'Invalid max_attempts parameter; must be an integer'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        model_name = request.query_params.get('model')

        hybrid_result = assess_prefix_hybrid(
            user_id=user_id,
            problem_id_or_obj=problem_id,
            max_attempts=max_attempts,
            model_name=model_name
        )
        if "error" in hybrid_result:
            return Response(hybrid_result, status=status.HTTP_404_NOT_FOUND)

        return Response(hybrid_result, status=status.HTTP_200_OK)


class ExportAnnotationBatchView(APIView):
    """
    Research Annotation Export Endpoint:
    GET /api/struggle-analysis/annotation/export-batch/?max_trajectories=10&format=json
    Generates unlabelled pilot annotation batch containing pseudonymized trajectory prefix materials.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        max_trajectories = int(request.query_params.get('max_trajectories', 10))
        fmt = request.query_params.get('format', 'json').lower()
        
        batch = generate_pilot_annotation_batch(max_trajectories=max_trajectories)
        if fmt == 'csv':
            csv_str = export_annotation_batch(batch, format_type='csv')
            return Response(csv_str, content_type='text/csv', status=status.HTTP_200_OK)
        return Response(batch, status=status.HTTP_200_OK)


class SubmitAnnotationView(APIView):
    """
    Research Annotation Submission Endpoint:
    POST /api/struggle-analysis/annotation/submit/
    Submits completed human annotation records for storage/evaluation.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data
        if not data:
            return Response({'error': 'Empty annotation submission body'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            if isinstance(data, str):
                records = import_annotation_batch(data, format_type='json')
            elif isinstance(data, list):
                records = [import_annotation_batch(json.dumps(r))[0] for r in data]
            elif isinstance(data, dict) and 'records' in data:
                records = [import_annotation_batch(json.dumps(r))[0] for r in data['records']]
            elif isinstance(data, dict):
                records = import_annotation_batch(json.dumps(data))
            else:
                return Response({'error': 'Unsupported payload structure'}, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'status': 'success',
                'message': f'Successfully validated and received {len(records)} human annotation record(s).',
                'count': len(records)
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class EvaluateModelsView(APIView):
    """
    Research Model Evaluation Endpoint:
    GET /api/struggle-analysis/annotation/evaluate/
    Evaluates M1..M4 models against submitted human ground truth reference annotations.
    Returns no_reference_labels if human annotations are absent.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        res = evaluate_model_performance(human_records=[], model_predictions=[])
        return Response(res, status=status.HTTP_200_OK)



