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
        """Get or create user progress"""
        logger.info(f"👤 Getting user progress for user {user_id} on problem {problem.id}")
        try:
            progress = UserProgress.objects.get(
                user_id=user_id,
                problem=problem
            )
            logger.info(f"✅ Found existing progress: {progress.attempts_count} attempts, {progress.failed_attempts_count} failed")
            return progress
        except UserProgress.DoesNotExist:
            logger.info("📝 Creating new user progress record")
            progress = UserProgress.objects.create(
                user_id=user_id,
                problem=problem,
                attempts_count=0,
                failed_attempts_count=0,
                current_hint_level=1
            )
            logger.info(f"✅ Created new progress record for user {user_id}")
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

    def _create_attempt(self, user_id: int, problem: Problem, user_code: str) -> Attempt:
        """Create an attempt record for the user"""
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
            evaluation_details=attempt_evaluation
        )
        
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
        
        # Increment attempts count
        progress.attempts_count += 1
        logger.info(f"📈 Incremented attempts count: {progress.attempts_count}")
        
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
            "problem_id": problem.id
        }

        # Run the full agentic loop
        logger.info("🔄 Running Agentic Orchestrator workflow...")
        result = self.orchestrator.generate_adaptive_hint(
            problem_description=problem.description,
            user_code=user_code,
            hint_level=progress.current_hint_level,
            failed_attempts=progress.failed_attempts_count,
            previous_hints=previous_hints_text
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

        # Create attempt record
        attempt = Attempt.objects.create(
            user_id=user_id,
            problem=problem,
            code=user_code,
            status='failed' if not result['attempt_evaluation'].get('is_correct', False) else 'success',
            evaluation_details=result['attempt_evaluation']
        )
        logger.info(f"📝 Created attempt record (ID: {attempt.id}, Status: {attempt.status})")

        # Update failed_attempts_count only if failed, reset on success
        if not result['attempt_evaluation'].get('is_correct', False):
            progress.failed_attempts_count += 1
            logger.info(f"❌ Incremented failed_attempts_count: {progress.failed_attempts_count}")
        else:
            progress.failed_attempts_count = 0
            logger.info(f"✅ Reset failed_attempts_count to 0 (success)")
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

        # Create hint delivery record
        hint_delivery = HintDelivery.objects.create(
            hint=hint,
            user_id=user_id,
            attempt=attempt,
            is_auto_triggered=False
        )
        
        # Update UserProgress hints_requested
        progress.hints_requested += 1
        progress.save()

        logger.info(f"📝 Created hint delivery record (ID: {hint_delivery.id})")

        # Prepare response in the requested format
        response_data = {
            'status': 'success' if result['attempt_evaluation'].get('is_correct', False) else 'failed',
            'hint': {
                'id': hint_delivery.id,
                'content': result['generated_hint'],
                'level': new_hint_level,
                'type': new_hint_type
            },
            'evaluation': result['hint_evaluation'],
            'attempt_id': attempt.id,
            'attempt_evaluation': {
                'is_correct': result['attempt_evaluation'].get('is_correct', False),
                'error_pattern': result['attempt_evaluation'].get('error_pattern', ''),
                'conceptual_gap': result['attempt_evaluation'].get('conceptual_gap', ''),
                'diagnosis_summary': result['attempt_evaluation'].get('diagnosis_summary', ''),
                'suggestions': result['attempt_evaluation'].get('suggestions', [])
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
                previous_hints=previous_hints_text
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
