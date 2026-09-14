from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
import logging
import time

from .models import Problem, Attempt
from struggle_analysis.services import handle_attempt

logger = logging.getLogger(__name__)

# Score awarded per difficulty on a successful submission
SCORE_MAP = {
    'easy': 10,
    'medium': 25,
    'hard': 50,
}


class CodeViewSet(viewsets.ViewSet):
    """
    ViewSet for handling code execution and submission.
    Uses the Piston API for real multi-language code execution.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info("🚀 Initializing CodeViewSet with Piston execution engine...")
        from .execution_service import piston_service
        self.executor = piston_service
        logger.info("✅ CodeViewSet initialized successfully")

    def _get_problem(self, problem_id):
        """Get problem by ID — tries problem_id field first, then pk."""
        try:
            return Problem.objects.get(problem_id=problem_id)
        except Problem.DoesNotExist:
            pass
        try:
            return Problem.objects.get(pk=problem_id)
        except (Problem.DoesNotExist, ValueError):
            logger.warning(f"Problem not found: {problem_id}")
            return None

    def _create_attempt(self, user_id, problem, code, language, exec_status='pending', execution_time=None, evaluation_details=None, source='SUBMIT', session_id=None):
        """Create an attempt record."""
        try:
            attempt = Attempt.objects.create(
                user_id=user_id,
                problem=problem,
                code=code,
                language=language,
                status=exec_status,
                source=source,
                session_id=session_id,
                execution_time=execution_time,
                evaluation_details=evaluation_details,
            )
            return attempt
        except Exception as e:
            logger.error(f"Failed to create attempt: {e}")
            return None

    def _execute_code(self, problem, code, language, custom_input=None):
        """
        Execute code using the Piston API.
        """
        start = time.time()

        if custom_input is not None:
            result = self.executor.execute(code, language, stdin=custom_input)
            elapsed = time.time() - start

            if not result['success'] and result.get('stderr'):
                return {
                    'success': False,
                    'results': [],
                    'errors': [{'message': result['stderr'].strip()[:500], 'line': None}],
                    'execution_time': f"{elapsed:.2f}s",
                }

            return {
                'success': result['success'],
                'results': [{
                    'input': custom_input,
                    'expected': '(custom)',
                    'output': result.get('stdout', '').strip() or '(no output)',
                    'passed': result['success'],
                }],
                'errors': [],
                'execution_time': f"{elapsed:.2f}s",
            }

        test_cases = self._extract_test_cases(problem)

        if not test_cases:
            result = self.executor.execute(code, language)
            elapsed = time.time() - start

            if not result['success'] and result.get('stderr'):
                return {
                    'success': False,
                    'results': [],
                    'errors': [{'message': result['stderr'].strip()[:500], 'line': None}],
                    'execution_time': f"{elapsed:.2f}s",
                }

            return {
                'success': result['success'],
                'results': [{
                    'input': '(no input)',
                    'expected': '(run mode)',
                    'output': result.get('stdout', '').strip() or '(no output)',
                    'passed': result['success'],
                }],
                'errors': [],
                'execution_time': f"{elapsed:.2f}s",
            }

        test_results = []
        all_passed = True
        total_elapsed = 0

        for i, tc in enumerate(test_cases):
            tc_input = tc.get('input', '')
            tc_expected = tc.get('expected', '').strip()

            result = self.executor.execute(code, language, stdin=tc_input)
            total_elapsed += result.get('execution_time', 0)

            if not result['success'] and result.get('stderr'):
                return {
                    'success': False,
                    'results': test_results,
                    'errors': [{'message': result['stderr'].strip()[:500], 'line': None}],
                    'execution_time': f"{total_elapsed:.2f}s",
                }

            actual = result.get('stdout', '').strip()
            passed = actual == tc_expected
            if not passed:
                all_passed = False

            test_results.append({
                'input': tc_input,
                'expected': tc_expected,
                'output': actual or '(no output)',
                'passed': passed,
            })

        return {
            'success': all_passed,
            'results': test_results,
            'errors': [],
            'execution_time': f"{total_elapsed:.2f}s",
        }

    def _extract_test_cases(self, problem):
        try:
            from .serializers import ProblemDetailSerializer
            serializer = ProblemDetailSerializer(problem)
            tests = serializer.data.get('tests', [])
            if tests:
                return tests
        except Exception:
            pass
        return []

    @action(detail=False, methods=['post'])
    def run(self, request):
        """Run code — executes and returns output without submission."""
        user_id = request.data.get('user_id')
        problem_id = request.data.get('problem_id')
        code = request.data.get('code')
        language = request.data.get('language', 'javascript')
        custom_input = request.data.get('custom_input')
        session_id = request.data.get('session_id')

        if user_id is None or problem_id is None or code is None:
            logger.warning(f"Validation failed. request.data: {request.data}")
            return Response(
                {'error': 'Missing required fields: user_id, problem_id, code'},
                status=status.HTTP_400_BAD_REQUEST
            )

        problem = self._get_problem(problem_id)
        if not problem:
            return Response(
                {'error': f'Problem with ID {problem_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        execution_result = self._execute_code(problem, code, language, custom_input)

        attempt_status = 'success' if execution_result['success'] else 'failed'
        attempt = self._create_attempt(
            user_id, problem, code, language, attempt_status,
            execution_time=execution_result.get('execution_time'),
            evaluation_details=execution_result,
            source='RUN',
            session_id=session_id
        )
        handle_attempt(attempt)
        return Response({
            'success': execution_result['success'],
            'results': execution_result['results'],
            'errors': execution_result['errors'],
            'attempt_id': attempt.id if attempt else None,
            'execution_time': execution_result['execution_time'],
            'language': language,
        })

    @action(detail=False, methods=['post'])
    def submit(self, request):
        """Submit solution — executes, records, awards score, and updates streak."""
        user_id = request.data.get('user_id')
        problem_id = request.data.get('problem_id')
        code = request.data.get('code')
        language = request.data.get('language', 'javascript')
        session_id = request.data.get('session_id')

        if user_id is None or problem_id is None or code is None:
            logger.warning(f"Validation failed in submit. request.data: {request.data}")
            return Response(
                {'error': 'Missing required fields: user_id, problem_id, code'},
                status=status.HTTP_400_BAD_REQUEST
            )

        problem = self._get_problem(problem_id)
        if not problem:
            return Response(
                {'error': f'Problem with ID {problem_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        execution_result = self._execute_code(problem, code, language)

        attempt_status = 'success' if execution_result['success'] else 'failed'
        attempt = self._create_attempt(
            user_id, problem, code, language, attempt_status,
            execution_time=execution_result.get('execution_time'),
            evaluation_details=execution_result,
            source='SUBMIT',
            session_id=session_id
        )
        handle_attempt(attempt)

        # --- Streak + Score update ---
        from .models import DailyProblem, UserProfile
        from datetime import timedelta

        today = timezone.now().date()
        is_potd = DailyProblem.objects.filter(problem=problem, date=today).exists()
        score_awarded = 0

        profile = UserProfile.objects.filter(clerk_id=user_id).first()

        if profile:
            # Award score for first successful solve of this problem
            if execution_result['success']:
                already_solved = Attempt.objects.filter(
                    user_id=user_id, problem=problem
                ).filter(status__in=['passed', 'success']).exclude(
                    pk=attempt.pk if attempt else None
                ).exists()
                if not already_solved:
                    score_awarded = SCORE_MAP.get(problem.difficulty, 0)
                    profile.total_score += score_awarded
                    logger.info(f"Awarded {score_awarded} pts to user {user_id} for {problem.title}")

            # Streak logic on POTD attempt (any attempt counts)
            if is_potd:
                if profile.last_potd_attempt_date == today:
                    pass  # already attempted today, no double count
                elif profile.last_potd_attempt_date == today - timedelta(days=1):
                    profile.current_streak += 1
                    profile.last_potd_attempt_date = today
                else:
                    profile.current_streak = 1
                    profile.last_potd_attempt_date = today

                profile.longest_streak = max(profile.longest_streak, profile.current_streak)

            profile.save()

        return Response({
            'success': execution_result['success'],
            'results': execution_result['results'],
            'errors': execution_result['errors'],
            'attempt_id': attempt.id if attempt else None,
            'execution_time': execution_result['execution_time'],
            'language': language,
            'isSubmission': True,
            'submission_id': f"sub_{attempt.id}" if attempt else None,
            'score_awarded': score_awarded,
        })

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Fetch submission history for a given user and problem."""
        user_id = request.query_params.get('user_id')
        problem_id = request.query_params.get('problem_id')

        if not user_id or not problem_id:
            return Response(
                {'error': 'Missing required parameters: user_id, problem_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        problem = self._get_problem(problem_id)
        if not problem:
            return Response(
                {'error': f'Problem with ID {problem_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        from .serializers import AttemptSerializer
        attempts = Attempt.objects.filter(user_id=user_id, problem=problem).order_by('-created_at')
        serializer = AttemptSerializer(attempts, many=True)
        return Response(serializer.data)