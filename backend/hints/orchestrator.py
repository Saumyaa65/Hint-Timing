import logging
from typing import Dict, Any, List
from .agents.analyzer import AttemptAnalyzer
from .agents.strategist import HintStrategist
from .agents.generator import HintGenerator
from .agents.critic import HintCritic

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """Orchestrates the multi-agent reasoning flow for adaptive hints."""
    
    def __init__(self):
        self.analyzer = AttemptAnalyzer()
        self.strategist = HintStrategist()
        self.generator = HintGenerator()
        self.critic = HintCritic()

    def generate_adaptive_hint(self, 
                               problem_description: str, 
                               user_code: str, 
                               hint_level: int, 
                               failed_attempts: int,
                               previous_hints: List[str] = None,
                               execution_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Runs the full agentic loop:
        Attempt -> Diagnosis -> Strategy -> Generation -> Critique
        """
        logger.info("🎬 Starting Agentic Loop...")
        
        # Validate input parameters to prevent agent failures on empty input
        if not problem_description or not problem_description.strip():
            logger.warning("⚠️ problem_description is empty; using default placeholder.")
            problem_description = "Empty problem description."
        if not user_code or not user_code.strip():
            logger.warning("⚠️ user_code is empty; substituting empty string.")
            user_code = ""
        
        # 1. Analyze the attempt with execution context if available
        logger.info("🔍 Step 1: Analyzing Attempt...")
        diagnosis = self.analyzer.analyze(problem_description, user_code, execution_info=execution_info)
        
        # 2. Formulate pedagogical strategy
        logger.info("🧠 Step 2: Formulating Strategy...")
        strategy = self.strategist.formulate_strategy(
            diagnosis, 
            hint_level, 
            failed_attempts
        )

        # Determine updated hint level based on failed attempts, progress, and strategist recommendation
        target_level = hint_level
        if failed_attempts >= 5:
            target_level = max(target_level, 5)
        elif failed_attempts == 4:
            target_level = max(target_level, 4)
        elif failed_attempts == 3:
            target_level = max(target_level, 3)
        elif failed_attempts == 2:
            target_level = max(target_level, 2)
        elif failed_attempts == 1:
            target_level = max(target_level, 1)

        # If previous hints have been delivered at this level, escalate
        if previous_hints and len(previous_hints) >= target_level:
            target_level = min(target_level + 1, 5)

        # Also consider recommendation from strategist if provided
        rec_level = strategy.get("recommended_hint_level")
        if isinstance(rec_level, int) and 1 <= rec_level <= 5:
            target_level = max(target_level, rec_level)
            
        updated_hint_level = min(max(target_level, 1), 5)
        
        # Map level to hint type
        level_to_type = {
            1: "socratic",
            2: "conceptual",
            3: "approach",
            4: "directional",
            5: "structural"
        }
        updated_hint_type = strategy.get("strategy") or level_to_type.get(updated_hint_level, "conceptual")
        
        # 3. Generate the final hint text incorporating exact execution errors/mistakes
        logger.info("✍️ Step 3: Generating Hint Text...")
        exact_error = (execution_info or {}).get("exact_error", "None")
        test_summary = (execution_info or {}).get("test_summary", "None")

        hint_text = self.generator.generate_hint(
            problem_description,
            user_code,
            strategy,
            diagnosis.get("diagnosis_summary", ""),
            previous_hints or [],
            exact_error=exact_error,
            test_summary=test_summary
        )
        
        # 4. Critique the hint
        logger.info("⚖️ Step 4: Critiquing Hint...")
        evaluation = self.critic.evaluate_hint(
            problem_description,
            user_code,
            hint_text
        )
        
        logger.info("✅ Agentic Loop Complete.")
        
        return {
            "generated_hint": hint_text,
            "attempt_evaluation": diagnosis,
            "strategy": strategy,
            "hint_evaluation": evaluation,
            "updated_hint_level": updated_hint_level,
            "updated_hint_type": updated_hint_type
        }

    def evaluate_attempt(self, problem_description: str, user_code: str, execution_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Standalone diagnostic step."""
        return self.analyzer.analyze(problem_description, user_code, execution_info=execution_info)
