from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from .base import BaseAgent

class AttemptAnalyzer(BaseAgent):
    """Diagnoses student code and identifies logical/conceptual gaps."""
    
    def __init__(self):
        # Using Qwen for precise code evaluation
        super().__init__(model_name='nvidia/nemotron-3-ultra-550b-a55b:free', temperature=0.1)
        self.chain = self._build_chain()

    def _build_chain(self):
        prompt = PromptTemplate.from_template("""
        You are an expert Computer Science Tutor. Your task is to analyze a student's code attempt for a specific problem.
        
        Problem Description:
        {problem_description}
        
        Student's Code:
        {user_code}

        Execution Results & Errors:
        - Exact Error / Exception: {exact_error}
        - Test Cases Result: {test_summary}
        - Failing Test Detail: {failing_test}
        
        Analyze the attempt and provide a structured diagnosis. 
        Focus on WHY they are failing, not just THAT they are failing.
        If there is an exact runtime error, syntax error, or failing test case (such as a stupid mistake, off-by-one, type error, or wrong logic), identify that specific error clearly in the diagnosis alongside any conceptual gap.
        
        Return a JSON object with the following fields:
        1. "is_correct": boolean
        2. "error_pattern": Choose from [logic_error, time_complexity, space_complexity, edge_case_missing, syntax_error, wrong_approach, null_pointer]
        3. "conceptual_gap": A short phrase describing what the student doesn't understand (e.g., "In-place array manipulation", "Hash Map lookup efficiency", "Index boundaries").
        4. "diagnosis_summary": A 1-2 sentence explanation of the technical flaw or error.
        5. "suggestions": A list of 2-3 specific technical areas they should look at.
        """)
        return prompt | self.llm | self.json_parser

    def analyze(self, problem_description: str, user_code: str, execution_info: Dict[str, Any] = None) -> Dict[str, Any]:
        exec_info = execution_info or {}
        exact_error = exec_info.get("exact_error") or "None"
        test_summary = exec_info.get("test_summary") or "No tests executed"
        failing_test = exec_info.get("failing_test") or "None"

        return self.chain.invoke({
            "problem_description": problem_description,
            "user_code": user_code,
            "exact_error": exact_error,
            "test_summary": test_summary,
            "failing_test": failing_test
        })
