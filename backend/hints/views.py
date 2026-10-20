from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
import logging
import json

from .models import Problem, Hint, Attempt, HintDelivery, HintEvaluation, UserProgress
from .orchestrator import AgentOrchestrator
from .hint_chain import HintChain

logger = logging.getLogger(__name__)

class HintViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info("🚀 Initializing HintViewSet...")
        self.orchestrator = AgentOrchestrator()
        self.hint_chain = HintChain()
        logger.info("✅ HintViewSet initialized successfully")

    def _get_or_create_problem(self, problem_id, problem_data=None):
        """Get existing problem or create new one if needed"""
        logger.info(f"🔍 Looking up problem with ID: {problem_id}")
        
        # First try to get existing problem by user-provided problem_id
        try:
            problem = Problem.objects.get(problem_id=problem_id)
            logger.info(f"✅ Found existing problem by problem_id: {problem.title}")
            return problem
        except Problem.DoesNotExist:
            logger.info(f"❌ Problem {problem_id} not found by problem_id")
        
        # If problem doesn't exist and we have problem data, create it
        if problem_data:
            logger.info("📝 Creating new problem from provided data")
            problem = Problem.objects.create(
                problem_id=problem_id,  # Store the user-provided problem_id
                title=problem_data.get('title', 'Untitled Problem'),
                description=problem_data.get('description', ''),
                difficulty='medium'  # Set a default difficulty
            )
            logger.info(f"✅ Created new problem: {problem.title} (problem_id: {problem.problem_id}, db_id: {problem.id})")
            return problem
        
        logger.warning("⚠️  No problem data provided and problem not found")
        return None

    def _get_user_progress(self, user_id, problem):
        """Get or create user progress, synchronizing attempt counts with database"""
        logger.info(f"👤 Getting user progress for user {user_id} on problem {problem.id}")
        progress, created = UserProgress.objects.get_or_create(
            user_id=user_id,
            problem=problem,
            defaults={
                'attempts_count': 0,
                'failed_attempts_count': 0,
                'current_hint_level': 1
            }
        )
        attempts = Attempt.objects.filter(user_id=user_id, problem=problem)
        actual_attempts = attempts.count()
        actual_failed = attempts.filter(status='failed').count()
        if progress.attempts_count != actual_attempts or progress.failed_attempts_count != actual_failed:
            progress.attempts_count = actual_attempts
            progress.failed_attempts_count = actual_failed
            progress.save()
        logger.info(f"✅ Found progress: {progress.attempts_count} attempts, {progress.failed_attempts_count} failed")
        return progress

    def _get_previous_hints(self, user_id, problem):
        """Get previous hints for this user and problem"""
        logger.info(f"📚 Getting previous hints for user {user_id} on problem {problem.id}")
        hints = HintDelivery.objects.filter(
            user_id=user_id,
            hint__problem=problem
        ).select_related('hint').order_by('-created_at')
        logger.info(f"✅ Found {hints.count()} previous hints")
        return hints

    def _get_previous_attempts(self, user_id, problem):
        """Get previous attempts for the user on this problem"""
        attempts = Attempt.objects.filter(
            user_id=user_id,
            problem=problem
        ).order_by('-created_at')
        logger.info(f"✅ Found {attempts.count()} previous attempts")
        return attempts

    def _create_attempt(self, user_id: str, problem: Problem, user_code: str, source: str = 'HINT_REQUEST', session_id: str = None) -> Attempt:
        """Create an attempt record for the user and record progress"""
        logger.info(f"📝 Creating attempt record for user {user_id} on problem {problem.id}")
        
        # Evaluate the attempt
        attempt_evaluation = self.orchestrator.evaluate_attempt(
            problem_description=problem.description,
            user_code=user_code
        )
        
        # Create attempt record
        attempt = Attempt.objects.create(
            user_id=user_id,
            problem=problem,
            code=user_code,
            status='failed' if not attempt_evaluation.get('is_correct', False) else 'success',
            evaluation_details=attempt_evaluation,
            source=source,
            session_id=session_id
        )
        
        # Keep user progress in sync
        from struggle_analysis.services import handle_attempt
        handle_attempt(attempt)
        
        logger.info(f"✅ Created attempt record (ID: {attempt.id}, Status: {attempt.status})")
        return attempt

    @action(detail=False, methods=['post'])
    def request_hint(self, request):
        """Request a hint for a problem"""
        logger.info("🎯 Received hint request")
        logger.info(f"📥 Request data: {json.dumps(request.data, indent=2)}")
        
        user_id = request.data.get('user_id')
        problem_id = request.data.get('problem_id')
        user_code = request.data.get('user_code')
        problem_data = request.data.get('problem_data')
        session_id = request.data.get('session_id')
        
        # ... (rest of hint view logic)
        # Note: at attempt creation in request_hint:
        # attempt = Attempt.objects.create(
        #     user_id=user_id,
        #     problem=problem,
        #     code=user_code,
        #     status='failed' if not result['attempt_evaluation'].get('is_correct', False) else 'success',
        #     evaluation_details=result['attempt_evaluation'],
        #     source='HINT_REQUEST',
        #     session_id=session_id
        # )

        logger.info(f"📋 Request parameters:")
        logger.info(f"   - User ID: {user_id}")
        logger.info(f"   - Problem ID: {problem_id}")
        logger.info(f"   - User code length: {len(user_code) if user_code else 0} characters")
        logger.info(f"   - Problem data provided: {'✅ Yes' if problem_data else '❌ No'}")

        if not all([user_id, problem_id, user_code]):
            logger.error("❌ Missing required fields in request")
            return Response(
                {'error': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create problem
        problem = self._get_or_create_problem(problem_id, problem_data)
        if not problem:
            logger.error("❌ Problem not found and no problem data provided")
            return Response(
                {'error': 'Problem not found and no problem data provided'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Rate Limiting Logic: Max 3 hints per 5 minutes per problem per user
        time_threshold = timezone.now() - timedelta(minutes=5)
        recent_hints_count = HintDelivery.objects.filter(
            user_id=user_id,
            hint__problem=problem,
            created_at__gte=time_threshold
        ).count()

        if recent_hints_count >= 3:
            logger.warning(f"⚠️ Rate limit exceeded for user {user_id} on problem {problem_id}")
            return Response(
                {'error': 'Too many hint requests. Please wait 5 minutes before requesting again.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Get or create user progress
        progress = self._get_user_progress(user_id, problem)
        
        # Calculate time since last attempt
        time_since_last_attempt = 0
        if progress.last_activity:
            time_since_last_attempt = (timezone.now() - progress.last_activity).total_seconds()
            logger.info(f"⏱️  Time since last attempt: {time_since_last_attempt:.2f} seconds")
        progress.last_activity = timezone.now()
        progress.save()
        logger.info("💾 User progress saved")

        # Escalate hint level if user is inactive for 5+ minutes
        if time_since_last_attempt > 300:
            logger.info("⏫ User inactive for 5+ minutes, escalating hint level")
            progress.current_hint_level = min(progress.current_hint_level + 1, 5)
            progress.save()

        # Get previous hints (last 5)
        previous_hints = list(self._get_previous_hints(user_id, problem)[:5])
        previous_hints_text = [hint.hint.content for hint in previous_hints]

        # Extract execution details from latest attempt or run code directly
        last_attempt = Attempt.objects.filter(user_id=user_id, problem=problem).order_by('-created_at').first()
        language = request.data.get('language') or (getattr(last_attempt, 'language', None) if last_attempt else 'python') or 'python'

        exec_details = None
        if last_attempt and last_attempt.evaluation_details and (last_attempt.code or '').strip() == (user_code or '').strip():
            exec_details = last_attempt.evaluation_details
        else:
            try:
                from .code_views import CodeViewSet
                code_view = CodeViewSet()
                exec_details = code_view._execute_code(problem, user_code, language)
            except Exception as e:
                logger.warning(f"⚠️ Code execution check during hint request failed: {e}")
                exec_details = {}

        # Parse exact error and test case results
        exact_error = ""
        test_summary = ""
        passed_tests = 0
        total_tests = 0
        failing_test = ""
        results = []
        errors = []

        if exec_details:
            errors = exec_details.get('errors', [])
            results = exec_details.get('results', [])
            
            if errors and len(errors) > 0:
                first_err = errors[0]
                exact_error = first_err.get('message', '') if isinstance(first_err, dict) else str(first_err)
            
            if results:
                total_tests = len(results)
                passed_tests = sum(1 for r in results if r.get('passed'))
                test_summary = f"{passed_tests}/{total_tests} test cases passed."
                
                failed_tc = next((r for r in results if not r.get('passed')), None)
                if failed_tc:
                    failing_test = f"Input: {failed_tc.get('input')}, Expected: {failed_tc.get('expected')}, Got: {failed_tc.get('output')}"
                    if not exact_error:
                        exact_error = f"Test case failed: Input: {failed_tc.get('input')} | Expected: {failed_tc.get('expected')} | Output: {failed_tc.get('output')}"
            elif not exact_error and not exec_details.get('success', False):
                exact_error = exec_details.get('stderr', '') or "Execution failed."

        execution_info = {
            "exact_error": exact_error,
            "test_summary": test_summary,
            "failing_test": failing_test,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "results": results,
            "errors": errors
        }

        # Prepare input for the chain
        chain_input = {
            "problem_description": problem.description,
            "user_code": user_code,
            "attempts_count": progress.attempts_count,
            "failed_attempts_count": progress.failed_attempts_count,
            "current_hint_level": progress.current_hint_level,
            "time_since_last_attempt": time_since_last_attempt,
            "previous_hints": previous_hints_text,
            "hint_level": progress.current_hint_level,
            "hint_type": "conceptual",
            "user_id": user_id,
            "problem_id": problem.id,
            "execution_info": execution_info
        }

        # Run the full agentic loop
        logger.info("🔄 Running Agentic Orchestrator workflow...")
        result = self.orchestrator.generate_adaptive_hint(
            problem_description=problem.description,
            user_code=user_code,
            hint_level=progress.current_hint_level,
            failed_attempts=progress.failed_attempts_count,
            previous_hints=previous_hints_text,
            execution_info=execution_info
        )

        # Get updated hint level and type from the chain result
        new_hint_level = result.get('updated_hint_level', progress.current_hint_level)
        new_hint_type = result.get('updated_hint_type', 'conceptual')

        # Check for duplicate hint (avoid delivering same hint as last time)
        if previous_hints_text and result['generated_hint'].strip() == previous_hints_text[0].strip():
            logger.warning("⚠️  Generated hint is a duplicate of the last delivered hint. Regenerating once...")
            # Try regenerating once
            result = self.hint_chain.process_hint_request(chain_input)
            if result['generated_hint'].strip() == previous_hints_text[0].strip():
                logger.warning("⚠️  Still duplicate after regeneration. Delivering as is.")

        # Update user progress with new hint level
        if new_hint_level != progress.current_hint_level:
            logger.info(f"📈 Updating hint level: {progress.current_hint_level} → {new_hint_level}")
            progress.current_hint_level = new_hint_level
            progress.save()

        # Create hint record with updated level and type
        hint = Hint.objects.create(
            problem=problem,
            content=result['generated_hint'],
            level=new_hint_level,  # Use updated level
            hint_type=new_hint_type  # Use updated type
        )
        logger.info(f"📝 Created hint record (ID: {hint.id}, Level: {hint.level}, Type: {hint.hint_type})")

        # Create hint evaluation record
        hint_evaluation = HintEvaluation.objects.create(
            hint=hint,
            safety_score=result['hint_evaluation']['safety_score'],
            helpfulness_score=result['hint_evaluation']['helpfulness_score'],
            quality_score=result['hint_evaluation']['quality_score'],
            progress_alignment_score=result['hint_evaluation']['progress_alignment_score'],
            pedagogical_value_score=result['hint_evaluation']['pedagogical_value_score']
        )
        logger.info(f"📝 Created hint evaluation record (ID: {hint_evaluation.id})")

        # Attach to latest existing attempt if one exists (do NOT create new Attempt on hint request)
        last_attempt = Attempt.objects.filter(user_id=user_id, problem=problem).order_by('-created_at').first()

        # Create hint delivery record
        hint_delivery = HintDelivery.objects.create(
            hint=hint,
            user_id=user_id,
            attempt=last_attempt,
            is_auto_triggered=False
        )
        
        # Update UserProgress hints_requested
        progress.hints_requested += 1
        progress.save()

        logger.info(f"📝 Created hint delivery record (ID: {hint_delivery.id})")

        # Prepare response in the requested format
        is_code_correct = result['attempt_evaluation'].get('is_correct', False) or (exec_details and exec_details.get('success', False))
        response_data = {
            'status': 'success' if is_code_correct else 'failed',
            'hint': {
                'id': hint_delivery.id,
                'content': result['generated_hint'],
                'level': new_hint_level,
                'type': new_hint_type,
                'exact_error': exact_error,
                'test_summary': test_summary
            },
            'exact_error': exact_error,
            'test_results_summary': test_summary,
            'passed_test_cases': passed_tests,
            'total_test_cases': total_tests,
            'test_results': results,
            'execution_errors': errors,
            'evaluation': result['hint_evaluation'],
            'attempt_id': last_attempt.id if last_attempt else None,
            'attempt_evaluation': {
                'is_correct': is_code_correct,
                'error_pattern': result['attempt_evaluation'].get('error_pattern', ''),
                'conceptual_gap': result['attempt_evaluation'].get('conceptual_gap', ''),
                'diagnosis_summary': result['attempt_evaluation'].get('diagnosis_summary', ''),
                'suggestions': result['attempt_evaluation'].get('suggestions', []),
                'exact_error': exact_error,
                'test_summary': test_summary
            },
            'user_progress': {
                'attempts_count': progress.attempts_count,
                'failed_attempts_count': progress.failed_attempts_count,
                'current_hint_level': new_hint_level,
                'is_stuck': progress.is_stuck(),
                'time_since_last_attempt': time_since_last_attempt
            }
        }
        
        logger.info("🎉 Hint request completed successfully")
        logger.info(f"📤 Sending response: {json.dumps(response_data, indent=2)}")
        logger.info(f"🎯 Final hint level: {new_hint_level}, type: {new_hint_type}")
        
        return Response(response_data)

    @action(detail=False, methods=['post'])
    def check_auto_trigger(self, request):
        """Check if a hint should be auto-triggered"""
        user_id = request.data.get('user_id')
        problem_id = request.data.get('problem_id')
        user_code = request.data.get('user_code')
        problem_data = request.data.get('problem_data')

        if not all([user_id, problem_id, user_code]):
            return Response(
                {'error': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create problem
        problem = self._get_or_create_problem(problem_id, problem_data)
        if not problem:
            return Response(
                {'error': 'Problem not found and no problem data provided'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get user progress
        progress = self._get_user_progress(user_id, problem)
        
        # Check if user is stuck
        if progress.is_stuck():
            # Create attempt record
            attempt = self._create_attempt(user_id, problem, user_code)
            
            # Get previous hints (last 5)
            previous_hints = list(self._get_previous_hints(user_id, problem)[:5])
            previous_hints_text = [delivery.hint.content for delivery in previous_hints]

            # Calculate time since last attempt
            time_since_last_attempt = 0
            if progress.last_activity:
                time_since_last_attempt = (timezone.now() - progress.last_activity).total_seconds()
            progress.last_activity = timezone.now()
            progress.save()

            # Escalate hint level if user is inactive for 5+ minutes
            if time_since_last_attempt > 300:
                logger.info("⏫ User inactive for 5+ minutes, escalating hint level")
                progress.current_hint_level = min(progress.current_hint_level + 1, 5)
                progress.save()

            # Prepare input for the chain
            chain_input = {
                "problem_description": problem.description,
                "user_code": user_code,
                "attempts_count": progress.attempts_count,
                "failed_attempts_count": progress.failed_attempts_count,
                "current_hint_level": progress.current_hint_level,
                "time_since_last_attempt": time_since_last_attempt,
                "previous_hints": previous_hints_text,
                "hint_level": progress.current_hint_level,
                "hint_type": "conceptual"
            }

            # Run the full agentic loop for auto-trigger
            logger.info("🔄 Running Agentic auto-trigger workflow...")
            result = self.orchestrator.generate_adaptive_hint(
                problem_description=problem.description,
                user_code=user_code,
                hint_level=progress.current_hint_level,
                failed_attempts=progress.failed_attempts_count,
                previous_hints=previous_hints_text,
                execution_info=attempt.evaluation_details if isinstance(attempt.evaluation_details, dict) else None
            )

            # Check for duplicate hint (avoid delivering same hint as last time)
            if previous_hints_text and result['generated_hint'].strip() == previous_hints_text[0].strip():
                logger.warning("⚠️  Generated hint is a duplicate of the last delivered hint. Regenerating once...")
                result = self.hint_chain.process_hint_request(chain_input)
                if result['generated_hint'].strip() == previous_hints_text[0].strip():
                    logger.warning("⚠️  Still duplicate after regeneration. Delivering as is.")

            # Get updated hint level and type from the chain result
            new_hint_level = result.get('updated_hint_level', progress.current_hint_level)
            new_hint_type = result.get('updated_hint_type', 'conceptual')

            # Create hint
            hint = Hint.objects.create(
                problem=problem,
                content=result['generated_hint'],
                level=new_hint_level,
                hint_type=new_hint_type
            )

            # Create hint delivery
            hint_delivery = HintDelivery.objects.create(
                hint=hint,
                user_id=user_id,
                attempt=attempt,
                is_auto_triggered=True
            )

            # Create evaluation record
            HintEvaluation.objects.create(
                hint=hint,
                safety_score=result['hint_evaluation']['safety_score'],
                helpfulness_score=result['hint_evaluation']['helpfulness_score'],
                quality_score=result['hint_evaluation']['quality_score'],
                progress_alignment_score=result['hint_evaluation']['progress_alignment_score'],
                pedagogical_value_score=result['hint_evaluation']['pedagogical_value_score']
            )

            # Update user progress
            progress.current_hint_level = new_hint_level
            progress.save()

            return Response({
                'should_trigger': True,
                'hint': {
                    'id': hint_delivery.id,
                    'content': hint.content,
                    'level': hint.level,
                    'type': hint.hint_type
                },
                'evaluation': {
                    'safety_score': result['hint_evaluation']['safety_score'],
                    'helpfulness_score': result['hint_evaluation']['helpfulness_score'],
                    'quality_score': result['hint_evaluation']['quality_score'],
                    'progress_alignment_score': result['hint_evaluation']['progress_alignment_score'],
                    'pedagogical_value_score': result['hint_evaluation']['pedagogical_value_score']
                },
                'attempt_id': attempt.id,
                'user_progress': {
                    'attempts_count': progress.attempts_count,
                    'failed_attempts_count': progress.failed_attempts_count,
                    'current_hint_level': progress.current_hint_level,
                    'is_stuck': progress.is_stuck()
                }
            })

        return Response({
            'should_trigger': False,
            'user_progress': {
                'attempts_count': progress.attempts_count,
                'failed_attempts_count': progress.failed_attempts_count,
                'current_hint_level': progress.current_hint_level,
                'is_stuck': progress.is_stuck()
            }
        })

    @action(detail=True, methods=['post'])
    def provide_feedback(self, request, pk=None):
        """Provide feedback on a hint delivery"""
        try:
            delivery = HintDelivery.objects.get(id=pk)
        except HintDelivery.DoesNotExist:
            return Response(
                {"error": "Hint delivery not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        feedback = request.data.get('feedback')
        rating = request.data.get('rating')

        if feedback:
            delivery.feedback = feedback
        if rating is not None:
            delivery.rating = rating
        
        delivery.save()

        return Response({
            'status': 'Feedback recorded successfully',
            'hint_id': delivery.hint.id,
            'attempt_id': delivery.attempt.id if delivery.attempt else None
        })
