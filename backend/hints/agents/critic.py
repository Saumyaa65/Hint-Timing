from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from .base import BaseAgent

class HintCritic(BaseAgent):
    """Evaluates the quality and safety of generated hints."""
    
    def __init__(self):
        super().__init__(model_name='nvidia/nemotron-3-super-120b-a12b:free', temperature=0.2)
        self.chain = self._build_chain()

    def _build_chain(self):
        prompt = PromptTemplate.from_template("""
        You are a Quality Assurance Agent for an educational platform. Evaluate the following hint for a coding problem.
        
        Problem: {problem_description}
        Student's Code: {user_code}
        Generated Hint: {hint_content}
        
        Provide scores between 0.0 and 1.0 for the following metrics:
        1. safety_score: 1.0 if no code is revealed, lower if it leaks the solution.
        2. helpfulness_score: 1.0 if it clearly points to a path forward.
        3. quality_score: 1.0 if the writing is clear and concise.
        4. progress_alignment_score: 1.0 if it matches the student's current difficulty.
        5. pedagogical_value_score: 1.0 if it encourages thinking rather than just giving an answer.
        
        Return a JSON object with these five scores.
        """)
        return prompt | self.llm | self.json_parser

    def evaluate_hint(self, problem_description: str, user_code: str, hint_content: str) -> Dict[str, Any]:
        return self.chain.invoke({
            "problem_description": problem_description,
            "user_code": user_code,
            "hint_content": hint_content
        })
