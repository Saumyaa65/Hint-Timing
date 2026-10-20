from typing import Dict, Any, List
from langchain_core.prompts import PromptTemplate
from .base import BaseAgent

class HintGenerator(BaseAgent):
    """Generates the final hint text for the student."""
    
    def __init__(self):
        super().__init__(model_name='nvidia/nemotron-3-ultra-550b-a55b:free', temperature=0.7)
        self.chain = self._build_chain()

    def _build_chain(self):
        prompt = PromptTemplate.from_template("""
        You are a supportive AI Coding Tutor. Your goal is to write a hint that helps the student solve the problem on their own.
        
        CRITICAL RULE: DO NOT PROVIDE FULL CODE SOLUTIONS. DO NOT REVEAL THE ENTIRE ANSWER.
        
        Problem: {problem_description}
        Student's Code: {user_code}
        
        Pedagogical Strategy:
        - Approach: {strategy}
        - Focus: {focus_area}
        - Complexity: {complexity}/5
        
        Diagnosis Context: {diagnosis_summary}
        Execution Error / Output: {exact_error}
        Test Results: {test_summary}
        
        Previous Hints: {previous_hints}
        
        Write a concise, helpful hint (max 3-4 sentences). 
        - If there is an exact runtime error, syntax error, or failing test case (such as a stupid mistake, off-by-one, type error, or wrong logic), point it out clearly so they know what broke.
        - If strategy is 'socratic', ask a leading question guiding them toward the fix.
        - If strategy is 'conceptual', explain the concept in the context of this problem.
        - If strategy is 'directional', point them to what they missed without giving complete code.
        """)
        return prompt | self.llm | self.str_parser

    def generate_hint(self, 
                      problem_description: str, 
                      user_code: str, 
                      strategy_info: Dict[str, Any], 
                      diagnosis_summary: str,
                      previous_hints: List[str],
                      exact_error: str = "None",
                      test_summary: str = "None") -> str:
        return self.chain.invoke({
            "problem_description": problem_description,
            "user_code": user_code,
            "strategy": strategy_info.get("strategy"),
            "focus_area": strategy_info.get("focus_area"),
            "complexity": strategy_info.get("complexity"),
            "diagnosis_summary": diagnosis_summary,
            "exact_error": exact_error or "None",
            "test_summary": test_summary or "None",
            "previous_hints": "\n".join(previous_hints) if previous_hints else "None"
        })
