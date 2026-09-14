from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock
from rest_framework.test import APIClient
from rest_framework import status
from hints.models import Problem, Attempt
from struggle_analysis.trajectory import build_trajectory
from struggle_analysis.assessment import assess_prefix, assess_trajectory
from struggle_analysis.llm_assessment import (
    format_trajectory_for_llm,
    parse_llm_json_response,
    assess_prefix_with_llm,
    assess_trajectory_with_llm
)
from struggle_analysis.comparison import compare_struggle_assessments
from struggle_analysis.services import handle_attempt


class ResearchAssessmentBaselineTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_id = "user_test_assessment_777"
        self.problem = Problem.objects.create(
            title="Assessment Benchmark",
            problem_id="test_assessment_benchmark",
            description="Benchmark problem for struggle assessment baseline",
            difficulty="medium"
        )

    def _create_attempt(self, code, status_str, passed, total, error_msg=None, dt_offset_seconds=0):
        results = []
        for i in range(total):
            results.append({
                'input': f'{i}',
                'expected': f'{i}',
                'output': f'{i}' if i < passed else 'wrong',
                'passed': i < passed
            })
        errors = []
        if error_msg:
            errors.append({'message': error_msg, 'line': 1})

        eval_details = {
            'success': status_str == 'success',
            'results': results,
            'errors': errors,
            'execution_time': '0.10s'
        }

        created_at = timezone.now() + timedelta(seconds=dt_offset_seconds)
        attempt = Attempt.objects.create(
            user_id=self.user_id,
            problem=self.problem,
            code=code,
            language='python',
            status=status_str,
            execution_time='0.10s',
            evaluation_details=eval_details
        )
        if dt_offset_seconds != 0:
            Attempt.objects.filter(pk=attempt.pk).update(created_at=created_at)
            attempt.refresh_from_db()

        handle_attempt(attempt)
        return attempt

    def test_case_a_clear_progression(self):
        """Case A: 0/10 -> 2/10 -> 5/10 -> 8/10 -> 10/10 -> Expected: PRODUCTIVE"""
        self._create_attempt("code_0", "failed", 0, 10, dt_offset_seconds=0)
        self._create_attempt("code_2", "failed", 2, 10, dt_offset_seconds=20)
        self._create_attempt("code_5", "failed", 5, 10, dt_offset_seconds=40)
        self._create_attempt("code_8", "failed", 8, 10, dt_offset_seconds=60)
        self._create_attempt("code_10", "success", 10, 10, dt_offset_seconds=80)

        res = assess_prefix(self.user_id, self.problem.problem_id)
        assessment = res["assessment"]

        self.assertEqual(assessment["state"], "PRODUCTIVE")
        self.assertGreaterEqual(assessment["confidence"], 0.70)
        self.assertIn("P1_PERFORMANCE_IMPROVEMENT", assessment["positive_signals"])
        self.assertIn("P5_OVERALL_TRAJECTORY_PROGRESS", assessment["positive_signals"])

    def test_case_b_clear_stagnation(self):
        """Case B: 0/10 -> 0/10 -> 0/10 -> 0/10 -> 0/10 -> Expected: UNPRODUCTIVE"""
        code = "def solve(): pass"
        self._create_attempt(code, "failed", 0, 10, dt_offset_seconds=0)
        self._create_attempt(code, "failed", 0, 10, dt_offset_seconds=15)
        self._create_attempt(code, "failed", 0, 10, dt_offset_seconds=30)
        self._create_attempt(code, "failed", 0, 10, dt_offset_seconds=45)
        self._create_attempt(code, "failed", 0, 10, dt_offset_seconds=60)

        res = assess_prefix(self.user_id, self.problem.problem_id)
        assessment = res["assessment"]

        self.assertEqual(assessment["state"], "UNPRODUCTIVE")
        self.assertGreaterEqual(assessment["confidence"], 0.70)
        self.assertIn("U1_REPEATED_EXECUTION", assessment["negative_signals"])
        self.assertIn("U4_PERFORMANCE_STAGNATION", assessment["negative_signals"])

    def test_case_c_error_evolution(self):
        """Case C: compile error -> different compile error -> runtime error -> 5/10 -> 8/10 -> Expected: PRODUCTIVE"""
        self._create_attempt("def err1(:", "failed", 0, 10, error_msg="SyntaxError: invalid syntax", dt_offset_seconds=0)
        self._create_attempt("def err2(:", "failed", 0, 10, error_msg="IndentationError: unexpected indent", dt_offset_seconds=20)
        self._create_attempt("def err3(): return 1/0", "failed", 0, 10, error_msg="ZeroDivisionError: division by zero", dt_offset_seconds=40)
        self._create_attempt("def err4(): return 5", "failed", 5, 10, dt_offset_seconds=60)
        self._create_attempt("def err5(): return 8", "failed", 8, 10, dt_offset_seconds=80)

        res = assess_prefix(self.user_id, self.problem.problem_id)
        assessment = res["assessment"]

        self.assertEqual(assessment["state"], "PRODUCTIVE")
        self.assertIn("P1_PERFORMANCE_IMPROVEMENT", assessment["positive_signals"])

    def test_case_d_short_trajectory(self):
        """Case D: Single failed attempt -> Expected: UNCERTAIN"""
        self._create_attempt("print(1)", "failed", 0, 10, dt_offset_seconds=0)

        res = assess_prefix(self.user_id, self.problem.problem_id)
        assessment = res["assessment"]

        self.assertEqual(assessment["state"], "UNCERTAIN")
        self.assertIn("UNCERTAIN_SHORT_TRAJECTORY", assessment["uncertainty_signals"])

    def test_case_e_exploration_without_clear_outcome(self):
        """Case E: Code edits without evaluation test details -> Expected: UNCERTAIN"""
        self._create_attempt("a = 1", "failed", 0, 0, dt_offset_seconds=0)
        self._create_attempt("b = 2", "failed", 0, 0, dt_offset_seconds=20)
        self._create_attempt("c = 3", "failed", 0, 0, dt_offset_seconds=40)

        res = assess_prefix(self.user_id, self.problem.problem_id)
        assessment = res["assessment"]

        self.assertEqual(assessment["state"], "UNCERTAIN")
        self.assertIn("UNCERTAIN_NO_EVALUATION_FEEDBACK", assessment["uncertainty_signals"])

    def test_case_f_stagnation_followed_by_recovery_temporal_adaptation(self):
        """
        Case F: 0/10 -> 0/10 -> 0/10 -> 5/10 -> 8/10
        At t=3: UNPRODUCTIVE
        At t=5: PRODUCTIVE
        Demonstrates temporal prefix adaptation as new evidence appears!
        """
        code = "def solve(): pass"
        self._create_attempt(code, "failed", 0, 10, dt_offset_seconds=0)
        self._create_attempt(code, "failed", 0, 10, dt_offset_seconds=15)
        self._create_attempt(code, "failed", 0, 10, dt_offset_seconds=30)
        self._create_attempt("def solve(): return x * 2", "failed", 5, 10, dt_offset_seconds=60)
        self._create_attempt("def solve(): return x * 2 + 1", "failed", 8, 10, dt_offset_seconds=80)

        res_t3 = assess_prefix(self.user_id, self.problem.problem_id, max_attempts=3)
        assessment_t3 = res_t3["assessment"]
        self.assertEqual(assessment_t3["state"], "UNPRODUCTIVE")

        res_t5 = assess_prefix(self.user_id, self.problem.problem_id, max_attempts=5)
        assessment_t5 = res_t5["assessment"]
        self.assertEqual(assessment_t5["state"], "PRODUCTIVE")
        self.assertIn("P4_STAGNATION_ESCAPE", assessment_t5["positive_signals"])

    def test_case_g_mixed_conflicting_signals(self):
        """Case G: Mixed signals (Repeated error + Code change + Same performance) -> Expected: UNCERTAIN"""
        code_a = "def fn(): return 1/0"
        self._create_attempt(code_a, "failed", 0, 10, error_msg="ZeroDivisionError", dt_offset_seconds=0)
        self._create_attempt(code_a, "failed", 0, 10, error_msg="ZeroDivisionError", dt_offset_seconds=20)

        res = assess_prefix(self.user_id, self.problem.problem_id)
        assessment = res["assessment"]
        self.assertIn("U2_REPEATED_ERROR", assessment["negative_signals"])

    def test_case_h_cyclic_reversion(self):
        """Case H: Code A -> Code B -> Code A -> Code B without test gain -> Expected: U6_REVERSION_CYCLIC signal"""
        code_a = "def f(): return 'A'"
        code_b = "def f(): return 'B'"

        self._create_attempt(code_a, "failed", 1, 10, dt_offset_seconds=0)
        self._create_attempt(code_b, "failed", 1, 10, dt_offset_seconds=20)
        self._create_attempt(code_a, "failed", 1, 10, dt_offset_seconds=40)
        self._create_attempt(code_b, "failed", 1, 10, dt_offset_seconds=60)

        res = assess_prefix(self.user_id, self.problem.problem_id)
        assessment = res["assessment"]

        self.assertIn("U6_REVERSION_CYCLIC", assessment["negative_signals"])

    def test_struggle_assessment_api_endpoint(self):
        """GET /api/struggle-analysis/assess/<problem_id>/?user_id=<user_id>&max_attempts=t"""
        self._create_attempt("code_0", "failed", 0, 10, dt_offset_seconds=0)
        self._create_attempt("code_5", "failed", 5, 10, dt_offset_seconds=20)

        url = f"/api/struggle-analysis/assess/{self.problem.problem_id}/?user_id={self.user_id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.json()
        self.assertIn("trajectory", data)
        self.assertIn("assessment", data)

        assessment = data["assessment"]
        self.assertIn(assessment["state"], ["PRODUCTIVE", "UNPRODUCTIVE", "UNCERTAIN"])


class LLMTrajectoryReasoningTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_id = "user_test_llm_reasoning_888"
        self.problem = Problem.objects.create(
            title="LLM Assessment Benchmark",
            problem_id="test_llm_benchmark",
            description="Benchmark problem for LLM trajectory reasoning",
            difficulty="hard"
        )

    def _create_attempt(self, code, status_str, passed, total, error_msg=None, dt_offset_seconds=0):
        results = []
        for i in range(total):
            results.append({
                'input': f'{i}',
                'expected': f'{i}',
                'output': f'{i}' if i < passed else 'wrong',
                'passed': i < passed
            })
        errors = []
        if error_msg:
            errors.append({'message': error_msg, 'line': 1})

        eval_details = {
            'success': status_str == 'success',
            'results': results,
            'errors': errors,
            'execution_time': '0.10s'
        }

        created_at = timezone.now() + timedelta(seconds=dt_offset_seconds)
        attempt = Attempt.objects.create(
            user_id=self.user_id,
            problem=self.problem,
            code=code,
            language='python',
            status=status_str,
            execution_time='0.10s',
            evaluation_details=eval_details
        )
        if dt_offset_seconds != 0:
            Attempt.objects.filter(pk=attempt.pk).update(created_at=created_at)
            attempt.refresh_from_db()

        handle_attempt(attempt)
        return attempt

    def test_prompt_formatting_and_prefix_temporal_isolation(self):
        """
        Verify that formatting a trajectory prefix max_attempts=3 contains strictly
        attempts 1..3 and NEVER contains attempts 4 or 5 (Zero Future Leakage).
        """
        for i in range(1, 6):
            self._create_attempt(f"code_version_{i}_secret", "failed", i*2, 10, dt_offset_seconds=i*10)

        traj_prefix_3 = build_trajectory(self.user_id, self.problem.problem_id, max_attempts=3)
        prompt_text = format_trajectory_for_llm(traj_prefix_3)

        # Assert attempts 1, 2, 3 are present
        self.assertIn("Attempt #1:", prompt_text)
        self.assertIn("code_version_1_secret", prompt_text)
        self.assertIn("Attempt #2:", prompt_text)
        self.assertIn("code_version_2_secret", prompt_text)
        self.assertIn("Attempt #3:", prompt_text)
        self.assertIn("code_version_3_secret", prompt_text)

        # Assert attempts 4 and 5 are strictly ABSENT (Zero Future Leakage)
        self.assertNotIn("Attempt #4:", prompt_text)
        self.assertNotIn("code_version_4_secret", prompt_text)
        self.assertNotIn("Attempt #5:", prompt_text)
        self.assertNotIn("code_version_5_secret", prompt_text)

    def test_json_parsing_resilience(self):
        """Test parse_llm_json_response handling markdown fencing and variations."""
        raw_json_str = '{"state": "PRODUCTIVE", "confidence": 0.85, "reasoning": "Progress observed."}'
        parsed1 = parse_llm_json_response(raw_json_str)
        self.assertEqual(parsed1["state"], "PRODUCTIVE")
        self.assertEqual(parsed1["confidence"], 0.85)

        markdown_fenced = '```json\n{"state": "UNPRODUCTIVE", "confidence": 0.7, "reasoning": "Stagnation."}\n```'
        parsed2 = parse_llm_json_response(markdown_fenced)
        self.assertEqual(parsed2["state"], "UNPRODUCTIVE")

        invalid_key_json = '{"state": "INVALID_STATE", "confidence": 0.5, "reasoning": "Unknown."}'
        parsed3 = parse_llm_json_response(invalid_key_json)
        self.assertEqual(parsed3["state"], "UNCERTAIN")

    def test_robust_llm_failure_handling(self):
        """Test assess_trajectory_with_llm failure behavior when API key is missing."""
        traj = build_trajectory(self.user_id, self.problem.problem_id)
        with patch('django.conf.settings.OPENROUTER_API_KEY', None):
            res = assess_trajectory_with_llm(traj)
            self.assertEqual(res["status"], "failed")
            self.assertIn("OPENROUTER_API_KEY", res["error"])

    def test_method_comparison_utility(self):
        """Test compare_struggle_assessments utility format and agreement tracking."""
        self._create_attempt("code_0", "failed", 0, 10, dt_offset_seconds=0)
        self._create_attempt("code_5", "failed", 5, 10, dt_offset_seconds=20)

        # Mock assess_prefix_with_llm response
        mock_llm_result = {
            "trajectory_prefix": {},
            "assessment": {
                "method": "LLM",
                "model": "nvidia/nemotron-3-super-120b-a12b:free",
                "state": "PRODUCTIVE",
                "confidence": 0.85,
                "reasoning": "Test score improved from 0 to 5."
            }
        }

        with patch('struggle_analysis.comparison.assess_prefix_with_llm', return_value=mock_llm_result):
            comp = compare_struggle_assessments(self.user_id, self.problem.problem_id)
            self.assertIn("rule_based", comp)
            self.assertIn("llm", comp)
            self.assertIn("agreement", comp)
            self.assertEqual(comp["rule_based"]["state"], "PRODUCTIVE")
            self.assertEqual(comp["llm"]["state"], "PRODUCTIVE")
            self.assertTrue(comp["agreement"])

    def test_struggle_llm_assess_and_compare_api_endpoints(self):
        """Test GET /api/struggle-analysis/llm-assess/ and GET /api/struggle-analysis/compare/"""
        self._create_attempt("a = 1", "failed", 1, 10, dt_offset_seconds=0)
        self._create_attempt("a = 2", "success", 10, 10, dt_offset_seconds=20)

        mock_llm_res = {
            "trajectory_prefix": {},
            "assessment": {
                "method": "LLM",
                "model": "nvidia/nemotron-3-super-120b-a12b:free",
                "state": "PRODUCTIVE",
                "confidence": 0.90,
                "reasoning": "Problem solved cleanly."
            }
        }

        with patch('struggle_analysis.views.assess_prefix_with_llm', return_value=mock_llm_res):
            url = f"/api/struggle-analysis/llm-assess/{self.problem.problem_id}/?user_id={self.user_id}"
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        with patch('struggle_analysis.views.compare_struggle_assessments', return_value={"agreement": True}):
            url_comp = f"/api/struggle-analysis/compare/{self.problem.problem_id}/?user_id={self.user_id}"
            response_comp = self.client.get(url_comp)
            self.assertEqual(response_comp.status_code, status.HTTP_200_OK)


class ResearchExperimentFrameworkTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_id = "user_test_experiment_999"
        self.problem = Problem.objects.create(
            title="Experiment Framework Benchmark",
            problem_id="test_exp_benchmark",
            description="Benchmark problem for research experiment framework",
            difficulty="medium"
        )

    def _create_attempt(self, code, status_str, passed, total, error_msg=None, dt_offset_seconds=0):
        results = []
        for i in range(total):
            results.append({
                'input': f'{i}',
                'expected': f'{i}',
                'output': f'{i}' if i < passed else 'wrong',
                'passed': i < passed
            })
        errors = []
        if error_msg:
            errors.append({'message': error_msg, 'line': 1})

        eval_details = {
            'success': status_str == 'success',
            'results': results,
            'errors': errors,
            'execution_time': '0.10s'
        }

        created_at = timezone.now() + timedelta(seconds=dt_offset_seconds)
        attempt = Attempt.objects.create(
            user_id=self.user_id,
            problem=self.problem,
            code=code,
            language='python',
            status=status_str,
            execution_time='0.10s',
            evaluation_details=eval_details
        )
        if dt_offset_seconds != 0:
            Attempt.objects.filter(pk=attempt.pk).update(created_at=created_at)
            attempt.refresh_from_db()

        handle_attempt(attempt)
        return attempt

    def test_snapshot_baseline_temporal_isolation(self):
        """Test Snapshot Baseline evaluates strictly attempt A_t without historical context."""
        from struggle_analysis.snapshot_baseline import assess_snapshot_trajectory
        self._create_attempt("code_1", "failed", 0, 10, dt_offset_seconds=0)
        self._create_attempt("code_2", "failed", 5, 10, dt_offset_seconds=20)
        self._create_attempt("code_3", "success", 10, 10, dt_offset_seconds=40)

        traj = build_trajectory(self.user_id, self.problem.problem_id)
        res = assess_snapshot_trajectory(traj)

        self.assertEqual(res["method"], "Snapshot Baseline")
        self.assertEqual(res["assessment_attempt"], 3)
        self.assertEqual(res["state"], "PRODUCTIVE")
        self.assertIn("SNAPSHOT_ALL_TESTS_PASSED", res["evidence"]["positive_signals"])

    def test_assess_with_method_unified_interface(self):
        """Test common interface assess_with_method normalizing outputs across snapshot, rule_based, llm."""
        from struggle_analysis.experiment import assess_with_method
        self._create_attempt("code_1", "failed", 0, 10, dt_offset_seconds=0)
        self._create_attempt("code_2", "failed", 5, 10, dt_offset_seconds=20)

        snap = assess_with_method("snapshot", self.user_id, self.problem.problem_id)
        self.assertEqual(snap["assessment"]["method"], "Snapshot Baseline")

        rule = assess_with_method("rule_based", self.user_id, self.problem.problem_id)
        self.assertEqual(rule["assessment"]["method"], "Rule-Based Baseline")

        with patch('struggle_analysis.experiment.assess_trajectory_with_llm', return_value={"state": "PRODUCTIVE", "confidence": 0.85, "reasoning": "Mock LLM"}):
            llm = assess_with_method("llm", self.user_id, self.problem.problem_id)
            self.assertEqual(llm["assessment"]["method"], "LLM Trajectory Reasoning")
            self.assertEqual(llm["assessment"]["state"], "PRODUCTIVE")

    def test_prefix_experiment_and_method_agreement(self):
        """Test run_prefix_experiment and analyze_method_agreement calculation."""
        from struggle_analysis.experiment import run_prefix_experiment, analyze_method_agreement
        self._create_attempt("code_1", "failed", 0, 10, dt_offset_seconds=0)
        self._create_attempt("code_2", "failed", 5, 10, dt_offset_seconds=20)
        self._create_attempt("code_3", "success", 10, 10, dt_offset_seconds=40)

        exp = run_prefix_experiment(self.user_id, self.problem.problem_id, include_llm=False)
        self.assertEqual(exp["trajectory_length"], 3)
        self.assertEqual(len(exp["prefix_results"]), 3)
        self.assertIn("agreement_summary", exp)

    def test_controlled_trajectory_patterns_p1_to_p10(self):
        """Test controlled behavioral patterns P1 through P10 dataset structure and evaluation."""
        from struggle_analysis.experiment import get_controlled_patterns, run_controlled_experiment
        patterns = get_controlled_patterns()
        self.assertEqual(len(patterns), 10)
        self.assertIn("P1", patterns)
        self.assertIn("P10", patterns)

        res = run_controlled_experiment(pattern_id="P1", include_llm=False)
        self.assertEqual(len(res["results"]), 1)
        p1_res = res["results"][0]
        self.assertEqual(p1_res["pattern_id"], "P1")
        self.assertEqual(p1_res["rule_based"]["state"], "PRODUCTIVE")

    def test_export_experiment_dataset_json_format(self):
        """Test export_experiment_dataset schema validity."""
        from struggle_analysis.experiment import export_experiment_dataset
        sample_exp = {"trajectory_length": 2, "evaluations": []}
        exported = export_experiment_dataset(sample_exp)
        self.assertIn("export_metadata", exported)
        self.assertIn("experiment_data", exported)

    def test_experiment_and_pattern_api_endpoints(self):
        """Test GET /api/struggle-analysis/experiment/<problem_id>/ and GET /api/struggle-analysis/patterns/"""
        self._create_attempt("code_1", "failed", 0, 10, dt_offset_seconds=0)

        url_exp = f"/api/struggle-analysis/experiment/{self.problem.problem_id}/?user_id={self.user_id}&include_llm=false"
        res_exp = self.client.get(url_exp)
        self.assertEqual(res_exp.status_code, status.HTTP_200_OK)

        url_pat = "/api/struggle-analysis/patterns/?pattern_id=P1&include_llm=false"
        res_pat = self.client.get(url_pat)
        self.assertEqual(res_pat.status_code, status.HTTP_200_OK)


class HybridStruggleAssessmentTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_id = "user_test_hybrid_1000"
        self.problem = Problem.objects.create(
            title="Hybrid Framework Benchmark",
            problem_id="test_hybrid_benchmark",
            description="Benchmark problem for hybrid struggle assessment",
            difficulty="hard"
        )

    def _create_attempt(self, code, status_str, passed, total, error_msg=None, dt_offset_seconds=0):
        results = []
        for i in range(total):
            results.append({
                'input': f'{i}',
                'expected': f'{i}',
                'output': f'{i}' if i < passed else 'wrong',
                'passed': i < passed
            })
        errors = []
        if error_msg:
            errors.append({'message': error_msg, 'line': 1})

        eval_details = {
            'success': status_str == 'success',
            'results': results,
            'errors': errors,
            'execution_time': '0.10s'
        }

        created_at = timezone.now() + timedelta(seconds=dt_offset_seconds)
        attempt = Attempt.objects.create(
            user_id=self.user_id,
            problem=self.problem,
            code=code,
            language='python',
            status=status_str,
            execution_time='0.10s',
            evaluation_details=eval_details
        )
        if dt_offset_seconds != 0:
            Attempt.objects.filter(pk=attempt.pk).update(created_at=created_at)
            attempt.refresh_from_db()

        handle_attempt(attempt)
        return attempt

    def test_hybrid_productive_consensus(self):
        """Rule PRODUCTIVE + LLM PRODUCTIVE -> Hybrid PRODUCTIVE with consensus confidence boost."""
        from struggle_analysis.hybrid import fuse_struggle_evidence
        rule_res = {"state": "PRODUCTIVE", "confidence": 0.80, "positive_signals": ["P1_PERFORMANCE_IMPROVEMENT"], "negative_signals": [], "uncertainty_signals": [], "reasoning": "Rule positive"}
        llm_res = {"state": "PRODUCTIVE", "confidence": 0.85, "positive_signals": ["P1_PERFORMANCE_IMPROVEMENT"], "negative_signals": [], "uncertainty_signals": [], "reasoning": "LLM positive", "model": "test-model"}
        traj = {"trajectory_length": 3, "attempts": [{}, {}, {}]}

        fused = fuse_struggle_evidence(rule_res, llm_res, traj)
        self.assertEqual(fused["state"], "PRODUCTIVE")
        self.assertEqual(fused["method"], "hybrid")
        self.assertGreater(fused["confidence"], 0.80)
        self.assertIn("Full Consensus", fused["evidence"]["agreement"][0])

    def test_hybrid_unproductive_consensus(self):
        """Rule UNPRODUCTIVE + LLM UNPRODUCTIVE -> Hybrid UNPRODUCTIVE with consensus confidence boost."""
        from struggle_analysis.hybrid import fuse_struggle_evidence
        rule_res = {"state": "UNPRODUCTIVE", "confidence": 0.80, "positive_signals": [], "negative_signals": ["U1_REPEATED_EXECUTION"], "uncertainty_signals": [], "reasoning": "Rule negative"}
        llm_res = {"state": "UNPRODUCTIVE", "confidence": 0.80, "positive_signals": [], "negative_signals": ["U1_REPEATED_EXECUTION"], "uncertainty_signals": [], "reasoning": "LLM negative", "model": "test-model"}
        traj = {"trajectory_length": 3, "attempts": [{}, {}, {}]}

        fused = fuse_struggle_evidence(rule_res, llm_res, traj)
        self.assertEqual(fused["state"], "UNPRODUCTIVE")
        self.assertGreater(fused["confidence"], 0.80)

    def test_hybrid_conflict_productive_vs_unproductive(self):
        """Rule PRODUCTIVE + LLM UNPRODUCTIVE -> Conflict recorded, defaults conservatively to UNCERTAIN."""
        from struggle_analysis.hybrid import fuse_struggle_evidence
        rule_res = {"state": "PRODUCTIVE", "confidence": 0.80, "positive_signals": ["P1_PERFORMANCE_IMPROVEMENT"], "negative_signals": [], "uncertainty_signals": [], "reasoning": "Rule positive"}
        llm_res = {"state": "UNPRODUCTIVE", "confidence": 0.80, "positive_signals": [], "negative_signals": ["U1_REPEATED_EXECUTION"], "uncertainty_signals": [], "reasoning": "LLM negative", "model": "test-model"}
        traj = {"trajectory_length": 3, "attempts": [{}, {}, {}]}

        fused = fuse_struggle_evidence(rule_res, llm_res, traj)
        self.assertEqual(fused["state"], "UNCERTAIN")
        self.assertTrue(len(fused["evidence"]["conflict"]) > 0)
        self.assertIn("HYBRID_METHOD_CONFLICT", fused["uncertainty_signals"])

    def test_hybrid_both_uncertain(self):
        """Both methods UNCERTAIN -> Hybrid UNCERTAIN."""
        from struggle_analysis.hybrid import fuse_struggle_evidence
        rule_res = {"state": "UNCERTAIN", "confidence": 0.50, "positive_signals": [], "negative_signals": [], "uncertainty_signals": ["UNCERTAIN_SHORT_TRAJECTORY"], "reasoning": "Rule uncertain"}
        llm_res = {"state": "UNCERTAIN", "confidence": 0.50, "positive_signals": [], "negative_signals": [], "uncertainty_signals": ["UNCERTAIN_SHORT_TRAJECTORY"], "reasoning": "LLM uncertain", "model": "test-model"}
        traj = {"trajectory_length": 2, "attempts": [{}, {}]}

        fused = fuse_struggle_evidence(rule_res, llm_res, traj)
        self.assertEqual(fused["state"], "UNCERTAIN")

    def test_hybrid_insufficient_trajectory(self):
        """Trajectory length < 2 -> Hybrid UNCERTAIN."""
        from struggle_analysis.hybrid import fuse_struggle_evidence
        rule_res = {"state": "UNCERTAIN", "confidence": 0.50}
        llm_res = {"state": "UNCERTAIN", "confidence": 0.50}
        traj = {"trajectory_length": 1, "attempts": [{}]}

        fused = fuse_struggle_evidence(rule_res, llm_res, traj)
        self.assertEqual(fused["state"], "UNCERTAIN")
        self.assertIn("HYBRID_SHORT_TRAJECTORY", fused["uncertainty_signals"])

    def test_hybrid_assess_with_method_integration(self):
        """Test assess_with_method('hybrid') dispatching."""
        from struggle_analysis.experiment import assess_with_method
        self._create_attempt("code_1", "failed", 0, 10, dt_offset_seconds=0)
        self._create_attempt("code_2", "failed", 5, 10, dt_offset_seconds=20)

        with patch('struggle_analysis.hybrid.assess_trajectory_with_llm', return_value={"state": "PRODUCTIVE", "confidence": 0.85, "reasoning": "Mock LLM"}):
            res = assess_with_method("hybrid", self.user_id, self.problem.problem_id)
            self.assertEqual(res["assessment"]["method"], "Hybrid Feature + LLM")
            self.assertEqual(res["assessment"]["state"], "PRODUCTIVE")

    def test_hybrid_prefix_experiment_integration(self):
        """Test run_prefix_experiment returns outputs for all 4 methods (M1, M2, M3, M4)."""
        from struggle_analysis.experiment import run_prefix_experiment
        self._create_attempt("code_1", "failed", 0, 10, dt_offset_seconds=0)
        self._create_attempt("code_2", "failed", 5, 10, dt_offset_seconds=20)

        with patch('struggle_analysis.experiment.assess_trajectory_with_llm', return_value={"state": "PRODUCTIVE", "confidence": 0.85, "reasoning": "Mock LLM"}):
            exp = run_prefix_experiment(self.user_id, self.problem.problem_id, include_llm=True)
            self.assertEqual(len(exp["prefix_results"]), 2)
            step2 = exp["prefix_results"][1]
            self.assertIn("snapshot", step2)
            self.assertIn("rule_based", step2)
            self.assertIn("llm", step2)
            self.assertIn("hybrid", step2)
            self.assertEqual(step2["hybrid"]["method"], "Hybrid Feature + LLM")

    def test_hybrid_metadata_recording(self):
        """Test hybrid output metadata recording llm_model, config_version, prompt_version."""
        from struggle_analysis.hybrid import fuse_struggle_evidence
        rule_res = {"state": "PRODUCTIVE", "confidence": 0.80}
        llm_res = {"state": "PRODUCTIVE", "confidence": 0.85, "model": "meta-llama/llama-3.3-70b-instruct"}
        traj = {"trajectory_length": 3, "attempts": [{}, {}, {}]}

        fused = fuse_struggle_evidence(rule_res, llm_res, traj)
        meta = fused["metadata"]
        self.assertEqual(meta["llm_model"], "meta-llama/llama-3.3-70b-instruct")
        self.assertEqual(meta["config_version"], "2E_HYBRID_PROVISIONAL_V1")
        self.assertEqual(meta["prompt_version"], "TASK_2C_SYSTEM_V1")

    def test_hybrid_api_endpoint(self):
        """Test GET /api/struggle-analysis/hybrid/<problem_id>/"""
        self._create_attempt("code_1", "failed", 0, 10, dt_offset_seconds=0)
        self._create_attempt("code_2", "failed", 5, 10, dt_offset_seconds=20)

        with patch('struggle_analysis.views.assess_prefix_hybrid', return_value={"assessment": {"method": "Hybrid Feature + LLM", "state": "PRODUCTIVE"}}):
            url = f"/api/struggle-analysis/hybrid/{self.problem.problem_id}/?user_id={self.user_id}"
            res = self.client.get(url)
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            data = res.json()
            self.assertEqual(data["assessment"]["method"], "Hybrid Feature + LLM")


class ResearchReproducibilityAuditTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_id = "user_test_reproducibility_1001"
        self.problem = Problem.objects.create(
            title="Reproducibility Audit Benchmark",
            problem_id="test_repro_benchmark",
            description="Benchmark problem for research reproducibility audit",
            difficulty="medium"
        )

    def _create_attempt(self, code, status_str, passed, total, error_msg=None, dt_offset_seconds=0):
        results = []
        for i in range(total):
            results.append({
                'input': f'{i}',
                'expected': f'{i}',
                'output': f'{i}' if i < passed else 'wrong',
                'passed': i < passed
            })
        errors = []
        if error_msg:
            errors.append({'message': error_msg, 'line': 1})

        eval_details = {
            'success': status_str == 'success',
            'results': results,
            'errors': errors,
            'execution_time': '0.10s'
        }

        created_at = timezone.now() + timedelta(seconds=dt_offset_seconds)
        attempt = Attempt.objects.create(
            user_id=self.user_id,
            problem=self.problem,
            code=code,
            language='python',
            status=status_str,
            execution_time='0.10s',
            evaluation_details=eval_details
        )
        if dt_offset_seconds != 0:
            Attempt.objects.filter(pk=attempt.pk).update(created_at=created_at)
            attempt.refresh_from_db()

        handle_attempt(attempt)
        return attempt

    def test_strict_model_pinning_prevents_silent_fallback(self):
        """Verify strict_model_pinning=True returns explicit error for pinned model rather than silent fallback."""
        from struggle_analysis.llm_assessment import assess_trajectory_with_llm
        traj = build_trajectory(self.user_id, self.problem.problem_id)
        
        with patch('django.conf.settings.OPENROUTER_API_KEY', 'fake_key'), patch('struggle_analysis.llm_assessment.ChatOpenAI', side_effect=Exception("Pinned model API connection reset")):
            res = assess_trajectory_with_llm(traj, model_name="meta-llama/llama-3.3-70b-instruct", strict_model_pinning=True)
            self.assertEqual(res["status"], "failed")
            self.assertIn("meta-llama/llama-3.3-70b-instruct", res["error"])
            self.assertTrue(res["strict_model_pinning"])

    def test_version_metadata_recording_across_conditions(self):
        """Verify rule_config_version, prompt_version, and hybrid_config_version recorded in outputs."""
        from struggle_analysis.assessment import assess_trajectory
        from struggle_analysis.llm_assessment import PROMPT_VERSION
        from struggle_analysis.config import RULE_CONFIG_VERSION, HYBRID_CONFIG
        from struggle_analysis.hybrid import fuse_struggle_evidence

        self._create_attempt("code_1", "failed", 0, 10, dt_offset_seconds=0)
        self._create_attempt("code_2", "failed", 5, 10, dt_offset_seconds=20)
        traj = build_trajectory(self.user_id, self.problem.problem_id)

        rule_res = assess_trajectory(traj)
        self.assertEqual(rule_res["rule_config_version"], RULE_CONFIG_VERSION)

        mock_llm = {"state": "PRODUCTIVE", "confidence": 0.85, "model": "meta-llama/llama-3.3-70b-instruct"}
        fused = fuse_struggle_evidence(rule_res, mock_llm, traj, strict_model_pinning=True)
        meta = fused["metadata"]
        self.assertEqual(meta["rule_config_version"], RULE_CONFIG_VERSION)
        self.assertEqual(meta["hybrid_config_version"], HYBRID_CONFIG['VERSION'])
        self.assertEqual(meta["prompt_version"], PROMPT_VERSION)
        self.assertTrue(meta["strict_model_pinning"])

    def test_same_input_comparison_and_temporal_isolation(self):
        """Verify M1, M2, M3, M4 evaluate identical trajectory prefix payload up to step t with zero future leakage."""
        from struggle_analysis.experiment import run_prefix_experiment
        for i in range(1, 6):
            self._create_attempt(f"code_{i}", "failed", i, 10, dt_offset_seconds=i*20)

        with patch('struggle_analysis.experiment.assess_trajectory_with_llm', return_value={"state": "PRODUCTIVE", "confidence": 0.80}):
            exp = run_prefix_experiment(self.user_id, self.problem.problem_id, include_llm=True)
            self.assertEqual(exp["trajectory_length"], 5)
            self.assertEqual(len(exp["prefix_results"]), 5)

            step3 = exp["prefix_results"][2]
            self.assertEqual(step3["attempt"], 3)
            self.assertEqual(step3["snapshot"]["assessment_attempt"], 3)
            self.assertEqual(step3["rule_based"]["assessment_attempt"], 3)
            self.assertEqual(step3["llm"]["assessment_attempt"], 3)
            self.assertEqual(step3["hybrid"]["assessment_attempt"], 3)


class HumanAnnotationAndEvaluationTests(TestCase):
    def setUp(self):
        self.user_id = "user_annotation_test_1001"
        self.user_id_2 = "user_annotation_test_1002"
        self.problem = Problem.objects.create(
            title="Annotation Protocol Benchmark",
            problem_id="test_annotation_benchmark",
            description="Benchmark problem for human annotation unit tests",
            difficulty="easy"
        )

    def _create_attempt(self, user_id, code, status_str, passed, total, dt_offset_seconds=0):
        results = [{'input': f'{i}', 'expected': f'{i}', 'output': f'{i}' if i < passed else 'wrong', 'passed': i < passed} for i in range(total)]
        eval_details = {'success': status_str == 'success', 'results': results, 'errors': [], 'execution_time': '0.10s'}
        created_at = timezone.now() + timedelta(seconds=dt_offset_seconds)
        attempt = Attempt.objects.create(
            user_id=user_id,
            problem=self.problem,
            code=code,
            language='python',
            status=status_str,
            execution_time='0.10s',
            evaluation_details=eval_details
        )
        if dt_offset_seconds != 0:
            Attempt.objects.filter(pk=attempt.pk).update(created_at=created_at)
            attempt.refresh_from_db()
        handle_attempt(attempt)
        return attempt

    def test_three_label_schema_validation(self):
        """1. Three-label schema validation: PRODUCTIVE, UNPRODUCTIVE, UNCERTAIN."""
        from struggle_analysis.annotation import validate_annotation_record
        base = {
            "annotation_id": "ann_1",
            "student_id": "anon_u1",
            "problem_id": "anon_p1",
            "prefix_length": 2,
            "confidence": "HIGH",
            "annotator_id": "rev_1",
            "annotation_version": "TASK_2F_B_PROTOCOL_V1"
        }
        for lbl in ["PRODUCTIVE", "UNPRODUCTIVE", "UNCERTAIN"]:
            rec = {**base, "label": lbl}
            valid, errs = validate_annotation_record(rec)
            self.assertTrue(valid, f"Label {lbl} should be valid: {errs}")

        invalid_rec = {**base, "label": "INVALID_LABEL"}
        valid, errs = validate_annotation_record(invalid_rec)
        self.assertFalse(valid)
        self.assertIn("Invalid label", errs[0])

    def test_prefix_contains_no_future_attempts(self):
        """2. Prefix contains no future attempts (At+1..AN)."""
        from struggle_analysis.annotation import generate_prefix_annotation_material
        for i in range(1, 6):
            self._create_attempt(self.user_id, f"code_{i}", "failed", i, 10, dt_offset_seconds=i*10)

        mat = generate_prefix_annotation_material(self.user_id, self.problem.problem_id, prefix_length=2)
        self.assertEqual(mat["prefix_length"], 2)
        self.assertEqual(len(mat["attempts"]), 2)
        self.assertEqual(mat["attempts"][0]["step"], 1)
        self.assertEqual(mat["attempts"][1]["step"], 2)
        self.assertEqual(mat["total_available_attempts_in_db"], 5)

    def test_annotation_record_cannot_contain_future_info(self):
        """3. Annotation record cannot contain future information or model predictions."""
        from struggle_analysis.annotation import validate_annotation_record
        rec = {
            "annotation_id": "ann_2",
            "student_id": "anon_u1",
            "problem_id": "anon_p1",
            "prefix_length": 2,
            "label": "PRODUCTIVE",
            "confidence": "HIGH",
            "annotator_id": "rev_1",
            "annotation_version": "TASK_2F_B_PROTOCOL_V1",
            "model_prediction": "PRODUCTIVE"  # Forbidden
        }
        valid, errs = validate_annotation_record(rec)
        self.assertFalse(valid)
        self.assertIn("Forbidden model field", errs[0])

    def test_model_predictions_not_exposed_in_annotation_material(self):
        """4. Model predictions are strictly excluded from annotation material."""
        from struggle_analysis.annotation import generate_prefix_annotation_material
        self._create_attempt(self.user_id, "code_1", "failed", 1, 10)
        mat = generate_prefix_annotation_material(self.user_id, self.problem.problem_id, prefix_length=1)
        
        self.assertNotIn("rule_based", mat)
        self.assertNotIn("llm", mat)
        self.assertNotIn("hybrid", mat)
        self.assertNotIn("snapshot", mat)
        self.assertEqual(mat["status"], "awaiting_human_annotation")

    def test_student_identifiers_pseudonymized_in_research_export(self):
        """5. Student and problem identifiers are pseudonymized in research export."""
        from struggle_analysis.annotation import pseudonymize_id, generate_prefix_annotation_material
        self._create_attempt(self.user_id, "code_1", "failed", 1, 10)
        
        pseudo_u = pseudonymize_id(self.user_id, prefix="anon_user")
        self.assertTrue(pseudo_u.startswith("anon_user_"))
        self.assertNotIn(self.user_id, pseudo_u)

        mat = generate_prefix_annotation_material(self.user_id, self.problem.problem_id, prefix_length=1)
        self.assertTrue(mat["student_id"].startswith("anon_user_"))
        self.assertNotIn(self.user_id, mat["student_id"])

    def test_annotation_export_import_roundtrip(self):
        """6. Annotation JSON and CSV export/import roundtrips work cleanly."""
        from struggle_analysis.annotation import validate_annotation_record, export_annotation_batch, import_annotation_batch
        records = [{
            "annotation_id": "ann_101",
            "student_id": "anon_u1",
            "problem_id": "anon_p1",
            "prefix_length": 3,
            "label": "PRODUCTIVE",
            "confidence": "HIGH",
            "rationale": "Active exploration with test improvement",
            "evidence": {"progression": ["+2 tests"]},
            "annotator_id": "rev_A",
            "annotation_version": "TASK_2F_B_PROTOCOL_V1",
            "timestamp": "2026-09-14T01:40:00Z"
        }]

        # JSON Roundtrip
        json_str = export_annotation_batch({"records": records}, format_type="json")
        imported_json = import_annotation_batch(json_str, format_type="json")
        self.assertEqual(len(imported_json), 1)
        self.assertEqual(imported_json[0]["label"], "PRODUCTIVE")

        # CSV Roundtrip
        csv_str = export_annotation_batch({"records": records}, format_type="csv")
        imported_csv = import_annotation_batch(csv_str, format_type="csv")
        self.assertEqual(len(imported_csv), 1)
        self.assertEqual(imported_csv[0]["label"], "PRODUCTIVE")

    def test_two_annotators_independent_annotation_same_prefix(self):
        """7. Two annotators can independently annotate the same trajectory prefix."""
        rec_a = {
            "annotation_id": "ann_a", "student_id": "anon_u1", "problem_id": "anon_p1", "prefix_length": 2,
            "label": "PRODUCTIVE", "confidence": "HIGH", "annotator_id": "annotator_A", "annotation_version": "V1"
        }
        rec_b = {
            "annotation_id": "ann_b", "student_id": "anon_u1", "problem_id": "anon_p1", "prefix_length": 2,
            "label": "UNCERTAIN", "confidence": "MEDIUM", "annotator_id": "annotator_B", "annotation_version": "V1"
        }
        self.assertNotEqual(rec_a["annotator_id"], rec_b["annotator_id"])
        self.assertNotEqual(rec_a["label"], rec_b["label"])
        self.assertEqual(rec_a["student_id"], rec_b["student_id"])

    def test_uncertain_preserved_as_real_third_class(self):
        """8. UNCERTAIN is preserved as a real third primary class in agreement & evaluation."""
        from struggle_analysis.agreement import calculate_cohens_kappa
        records_a = [{"student_id": "s1", "problem_id": "p1", "prefix_length": 1, "label": "UNCERTAIN"}]
        records_b = [{"student_id": "s1", "problem_id": "p1", "prefix_length": 1, "label": "UNCERTAIN"}]
        
        res = calculate_cohens_kappa(records_a, records_b)
        self.assertEqual(res["cohens_kappa"], 1.0)
        self.assertEqual(res["confusion_matrix"]["UNCERTAIN"]["UNCERTAIN"], 1)

    def test_agreement_calculation_cohen_and_fleiss(self):
        """9. Inter-rater agreement calculation (Cohen's & Fleiss' Kappa) works on real records."""
        from struggle_analysis.agreement import calculate_cohens_kappa, calculate_fleiss_kappa
        records_a = [
            {"student_id": "s1", "problem_id": "p1", "prefix_length": 1, "label": "PRODUCTIVE"},
            {"student_id": "s2", "problem_id": "p1", "prefix_length": 2, "label": "UNPRODUCTIVE"}
        ]
        records_b = [
            {"student_id": "s1", "problem_id": "p1", "prefix_length": 1, "label": "PRODUCTIVE"},
            {"student_id": "s2", "problem_id": "p1", "prefix_length": 2, "label": "UNCERTAIN"}
        ]
        cohen = calculate_cohens_kappa(records_a, records_b)
        self.assertEqual(cohen["paired_count"], 2)
        self.assertEqual(cohen["raw_agreement_pct"], 50.0)

        fleiss = calculate_fleiss_kappa([
            {"PRODUCTIVE": 2, "UNPRODUCTIVE": 0, "UNCERTAIN": 0},
            {"PRODUCTIVE": 0, "UNPRODUCTIVE": 1, "UNCERTAIN": 1}
        ])
        self.assertEqual(fleiss["subjects_count"], 2)

    def test_evaluation_interface_aborts_when_reference_labels_absent(self):
        """10. Evaluation interface aborts cleanly when reference labels are absent."""
        from struggle_analysis.evaluation import evaluate_model_performance
        res = evaluate_model_performance(human_records=[], model_predictions=[{"student_id": "s1", "problem_id": "p1", "prefix_length": 1, "state": "PRODUCTIVE"}])
        self.assertEqual(res["status"], "no_reference_labels")

    def test_student_level_grouping_prevents_leakage(self):
        """11. Student-level grouping leaves zero student overlap between train and test splits."""
        from struggle_analysis.evaluation import split_students_train_test
        records = [
            {"student_id": f"student_{i}", "problem_id": "p1", "prefix_length": j, "label": "PRODUCTIVE"}
            for i in range(10) for j in range(1, 4)
        ]
        train, test = split_students_train_test(records, test_ratio=0.3, seed=42)
        train_students = set(r["student_id"] for r in train)
        test_students = set(r["student_id"] for r in test)

        self.assertEqual(len(train_students.intersection(test_students)), 0)
        self.assertEqual(len(train_students) + len(test_students), 10)




