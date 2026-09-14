from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from .base import BaseAgent

class AttemptAnalyzer(BaseAgent):
    """Diagnoses student code and identifies logical/conceptual gaps."""
    
    def __init__(self):
        # Using Qwen for precise code evaluation
        super().__init__(model_name='nvidia/nemotron-3-super-120b-a12b:free', temperature=0.1)
        self.chain = self._build_chain()

    def _build_chain(self):
        prompt = PromptTemplate.from_template("""
        You are an expert Computer Science Tutor. Your task is to analyze a student's code attempt for a specific problem.
        
        Problem Description:
        {problem_description}
        
        Student's Code:
        {user_code}
        
        Analyze the attempt and provide a structured diagnosis. 
        Focus on WHY they are failing, not just THAT they are failing.
        
        Return a JSON object with the following fields:
        1. "is_correct": boolean
        2. "error_pattern": Choose from [logic_error, time_complexity, space_complexity, edge_case_missing, syntax_error, wrong_approach, null_pointer]
        3. "conceptual_gap": A short phrase describing what the student doesn't understand (e.g., "In-place array manipulation", "Hash Map lookup efficiency").
        4. "diagnosis_summary": A 1-2 sentence explanation of the technical flaw.
        5. "suggestions": A list of 2-3 specific technical areas they should look at.
        """)
        return prompt | self.llm | self.json_parser

    def analyze(self, problem_description: str, user_code: str) -> Dict[str, Any]:
        return self.chain.invoke({
            "problem_description": problem_description,
            "user_code": user_code
        })
