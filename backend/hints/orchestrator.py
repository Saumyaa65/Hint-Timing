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
                               previous_hints: List[str] = None) -> Dict[str, Any]:
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
        
        # 1. Analyze the attempt
        logger.info("🔍 Step 1: Analyzing Attempt...")
        diagnosis = self.analyzer.analyze(problem_description, user_code)
        
        # 2. Formulate pedagogical strategy
        logger.info("🧠 Step 2: Formulating Strategy...")
        strategy = self.strategist.formulate_strategy(
            diagnosis, 
            hint_level, 
            failed_attempts
        )
        
        # 3. Generate the final hint text
        logger.info("✍️ Step 3: Generating Hint Text...")
        hint_text = self.generator.generate_hint(
            problem_description,
            user_code,
            strategy,
            diagnosis.get("diagnosis_summary", ""),
            previous_hints or []
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
            "updated_hint_level": hint_level, # Future: Strategist can update this
            "updated_hint_type": strategy.get("strategy", "conceptual")
        }

    def evaluate_attempt(self, problem_description: str, user_code: str) -> Dict[str, Any]:
        """Standalone diagnostic step."""
        return self.analyzer.analyze(problem_description, user_code)
