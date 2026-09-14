from django.test import TestCase
from unittest.mock import MagicMock, patch
from .models import Problem, UserProgress
from .orchestrator import AgentOrchestrator

class HintSystemTests(TestCase):
    def test_problem_creation(self):
        """Test problem creation and __str__ representation."""
        problem = Problem.objects.create(
            title="Test Problem",
            problem_id="test-1",
            description="Test Description",
            difficulty="easy"
        )
        self.assertEqual(str(problem), f"{problem.id}: Test Problem")
        self.assertEqual(problem.difficulty, "easy")

    def test_user_progress_stuck_logic(self):
        """Test user progress stuck logic threshold behavior."""
        problem = Problem.objects.create(
            title="Test Problem 2",
            problem_id="test-2",
            description="Test Description 2",
            difficulty="medium"
        )
        progress = UserProgress.objects.create(
            user_id=42,
            problem=problem,
            attempts_count=3,
            failed_attempts_count=3,
            current_hint_level=1
        )
        # Not stuck yet because last_activity is timezone.now() (less than 5 min threshold)
        self.assertFalse(progress.is_stuck())

    @patch('hints.orchestrator.AttemptAnalyzer')
    @patch('hints.orchestrator.HintStrategist')
    @patch('hints.orchestrator.HintGenerator')
    @patch('hints.orchestrator.HintCritic')
    def test_orchestrator_input_validation(self, mock_critic, mock_generator, mock_strategist, mock_analyzer):
        """Test that AgentOrchestrator handles empty inputs gracefully using validation fallbacks."""
        # Set up mock returns
        mock_analyzer.return_value.analyze.return_value = {"success": False, "reason": "Failed"}
        mock_strategist.return_value.formulate_strategy.return_value = {"strategy": "conceptual"}
        mock_generator.return_value.generate_hint.return_value = "Hint text"
        mock_critic.return_value.evaluate_hint.return_value = {
            "safety_score": 1.0, "helpfulness_score": 1.0, "quality_score": 1.0,
            "progress_alignment_score": 1.0, "pedagogical_value_score": 1.0
        }
        
        orchestrator = AgentOrchestrator()
        result = orchestrator.generate_adaptive_hint("", "", 1, 0)
        
        # Verify that orchestrator did not fail and returned expected structure
        self.assertEqual(result["generated_hint"], "Hint text")
        self.assertEqual(result["updated_hint_level"], 1)
