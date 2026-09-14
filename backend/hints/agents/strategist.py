from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from .base import BaseAgent

class HintStrategist(BaseAgent):
    """Decides the pedagogical strategy (how to help the student)."""
    
    def __init__(self):
        # Using DeepSeek-R1 for reasoning/strategy
        super().__init__(model_name='nvidia/nemotron-3-super-120b-a12b:free', temperature=0.4)
        self.chain = self._build_chain()

    def _build_chain(self):
        prompt = PromptTemplate.from_template("""
        You are a Pedagogical Strategist for a coding platform. Based on a student's diagnosis, decide on the best way to guide them without giving away the answer.
        
        Diagnosis:
        - Error Pattern: {error_pattern}
        - Conceptual Gap: {conceptual_gap}
        - Diagnosis Summary: {diagnosis_summary}
        
        Student Progress:
        - Current Hint Level: {hint_level}
        - Failed Attempts: {failed_attempts}
        
        Decide on a strategy. 
        - Early levels should use 'Socratic' (asking questions).
        - Mid levels should use 'Conceptual' (explaining the underlying idea).
        - Higher levels/repeated failures should use 'Directional' (pointing to specific lines or logic).
        
        Return a JSON object:
        1. "strategy": Choose from [socratic, conceptual, directional, structural]
        2. "focus_area": What specific part of the code/logic to focus the hint on.
        3. "tone": The encouraging tone to take.
        4. "complexity": The depth of the hint (1-5).
        """)
        return prompt | self.llm | self.json_parser

    def formulate_strategy(self, diagnosis: Dict[str, Any], hint_level: int, failed_attempts: int) -> Dict[str, Any]:
        return self.chain.invoke({
            "error_pattern": diagnosis.get("error_pattern"),
            "conceptual_gap": diagnosis.get("conceptual_gap"),
            "diagnosis_summary": diagnosis.get("diagnosis_summary"),
            "hint_level": hint_level,
            "failed_attempts": failed_attempts
        })
