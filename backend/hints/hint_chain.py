import os
import logging
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from django.conf import settings

# LangChain imports
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_openai import ChatOpenAI

# Local imports
from .rag_service import RAGService

logger = logging.getLogger(__name__)

class HintChain:
    def __init__(self):
        logger.info("🚀 Initializing HintChain...")
        
        self.api_key = settings.OPENROUTER_API_KEY
        self.langsmith_api_key = settings.LANGSMITH_API_KEY
        
        # Configure LangSmith
        if self.langsmith_api_key:
            os.environ["LANGCHAIN_API_KEY"] = self.langsmith_api_key
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
            os.environ["LANGCHAIN_TRACING_V2"] = str(settings.LANGSMITH_TRACING_V2)
            os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
        
        # Model configurations for different operations
        self.model_configs = {
            'attempt_evaluation': {
                'model': 'nvidia/nemotron-3-ultra-550b-a55b:free',
                'temperature': 0.3,  # Lower temperature for more precise evaluation
                'description': 'Attempt Evaluation Model'
            },
            'hint_generation': {
                'model': 'nvidia/nemotron-3-ultra-550b-a55b:free',
                'temperature': 0.7,  # Higher temperature for creative hint generation
                'description': 'Hint Generation Model'
            },
            'hint_evaluation': {
                'model': 'nvidia/nemotron-3-ultra-550b-a55b:free',
                'temperature': 0.2,  # Very low temperature for consistent scoring
                'description': 'Hint Evaluation Model'
            },
            'auto_trigger': {
                'model': 'nvidia/nemotron-3-ultra-550b-a55b:free',
                'temperature': 0.4,  # Medium temperature for balanced decision making
                'description': 'Auto-Trigger Decision Model'
            }
        }
        
        # Initialize LLM instances for each operation
        self.llms = {}
        for operation, config in self.model_configs.items():
            self.llms[operation] = ChatOpenAI(
                model=config['model'],
                openai_api_key=self.api_key,
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=config['temperature']
            )
            logger.info(f"✅ Initialized {config['description']}: {config['model']} (temp: {config['temperature']})")
        
        # Initialize output parsers
        self.str_parser = StrOutputParser()
        self.json_parser = JsonOutputParser()
        
        # Initialize RAG service
        self.rag_service = RAGService()
        
        # Build the chains
        self._build_chains()
        
        logger.info("✅ HintChain initialized successfully")

    def _build_chains(self):
        """Build all the LangChain components with superior prompts and parsing"""
        
        # 1. Attempt Evaluation Chain - Enhanced with Error Pattern Classification
        attempt_eval_prompt = PromptTemplate.from_template("""
        Problem Description: {problem_description}
        
        User's Code:
        {user_code}
        
        Please analyze if this code would solve the problem correctly. Consider:
        1. Logic correctness
        2. Edge cases
        3. Time and space complexity
        4. Code quality
        
        Respond in the following format:
        success: [true/false]
        reason: [brief explanation]
        complexity: [time and space complexity]
        edge_cases: [list of edge cases handled or missed]
        code_quality: [assessment of code quality]
        suggestions: [specific suggestions for improvement]
        error_pattern: [classify the main error pattern - choose from: time_complexity, logic_error, edge_case_missing, wrong_approach, syntax_error, boundary_condition, data_structure_misuse, algorithm_choice, null_pointer, index_error, type_error, or other]
        error_category: [categorize the error - choose from: performance, correctness, completeness, or other]
        
        Example response:
        success: false
        reason: The code doesn't handle the case where no solution exists
        complexity: O(n) time, O(1) space
        edge_cases: Missing empty array, missing no-solution case
        code_quality: Good structure but missing edge case handling
        suggestions: Add null checks, handle edge cases, improve error handling
        error_pattern: edge_case_missing
        error_category: completeness
        """)
        
        self.attempt_evaluation_chain = (
            attempt_eval_prompt 
            | self.llms['attempt_evaluation'] 
            | self.str_parser
        )
        
        # 2. Hint Generation Chain - Using superior prompt from prompts.py
        hint_gen_prompt = PromptTemplate.from_template("""
        Problem Description: {problem_description}
        
        User's Current Code:
        {user_code}
        
        User Progress:
        - Total Attempts: {attempts_count}
        - Failed Attempts: {failed_attempts_count}
        - Current Hint Level: {current_hint_level}
        - Time Since Last Attempt: {time_since_last_attempt} seconds
        
        Previous Hints Given:
        {previous_hints}
        
        Current Hint Level: {hint_level}
        Hint Type: {hint_type}
        
        Please generate a hint that:
        1. Is non-revealing (doesn't give away the solution)
        2. Is appropriate for hint level {hint_level} and type {hint_type}
        3. Builds upon previous hints and user's progress
        4. Guides the user to think about the problem
        5. Is specific to their current code and approach
        6. Considers their previous attempts and failures
        7. Provides pedagogical value by encouraging problem-solving skills
        
        The hint should be:
        - More conceptual for early levels
        - More specific for higher levels
        - Focused on the current hint type
        - Aligned with the user's learning progress
        
        Provide only the hint content, no additional formatting.
        """)
        
        self.hint_generation_chain = (
            hint_gen_prompt 
            | self.llms['hint_generation'] 
            | self.str_parser
        )
        
        # 3. Hint Evaluation Chain - Using superior prompt from prompts.py
        hint_eval_prompt = PromptTemplate.from_template("""
        Problem Description: {problem_description}
        
        User's Code:
        {user_code}
        
        User Progress:
        - Total Attempts: {attempts_count}
        - Failed Attempts: {failed_attempts_count}
        - Current Hint Level: {current_hint_level}
        - Time Since Last Attempt: {time_since_last_attempt} seconds
        
        Previous Hints:
        {previous_hints}
        
        Hint to Evaluate:
        {hint_content}
        
        Please evaluate this hint and provide scores in the following format:
        
        safety_score: [score between 0 and 1]
        helpfulness_score: [score between 0 and 1]
        quality_score: [score between 0 and 1]
        progress_alignment_score: [score between 0 and 1]
        pedagogical_value_score: [score between 0 and 1]
        
        For each score, provide a number between 0 and 1, where:
        - 0 means completely ineffective
        - 1 means perfect effectiveness
        
        Example response format:
        safety_score: 0.8
        helpfulness_score: 0.7
        quality_score: 0.9
        progress_alignment_score: 0.6
        pedagogical_value_score: 0.8
        """)
        
        self.hint_evaluation_chain = (
            hint_eval_prompt 
            | self.llms['hint_evaluation'] 
            | self.str_parser
        )
        
        # 4. Auto-Trigger Decision Chain - Using superior prompt from prompts.py
        auto_trigger_prompt = PromptTemplate.from_template("""
        Problem Description: {problem_description}
        
        User's Current Code:
        {user_code}
        
        User Progress:
        - Total Attempts: {attempts_count}
        - Failed Attempts: {failed_attempts_count}
        - Current Hint Level: {current_hint_level}
        - Time Since Last Attempt: {time_since_last_attempt} seconds
        
        Last Attempt:
        - Status: {last_attempt_status}
        - Error Message: {last_attempt_error}
        - Test Cases Passed: {test_cases_passed}/{total_test_cases}
        
        Please analyze if the user needs a hint based on:
        1. Time since last activity
        2. Number of failed attempts
        3. Error patterns in the code
        4. Test case failures
        5. Code complexity and approach
        
        Provide:
        1. A decision (yes/no) on whether to trigger a hint
        2. The reason for the decision
        3. The recommended hint type (conceptual/approach/implementation/debug)
        4. The recommended hint level
        
        Respond in the following format:
        decision: [yes/no]
        reason: [reason for the decision]
        hint_type: [conceptual/approach/implementation/debug]
        hint_level: [1-5]
        """)
        
        self.auto_trigger_chain = (
            auto_trigger_prompt 
            | self.llms['auto_trigger'] 
            | self.str_parser
        )
        
        # 5. Main Workflow Chain
        self._build_main_workflow()
        
        logger.info("✅ All chains built successfully")

    def _build_main_workflow(self):
        """Build the main workflow chain that orchestrates everything"""
        
        def run_workflow(inputs):
            """Run the complete workflow step by step with superior parsing"""
            logger.info("🔄 Running workflow steps...")
            
            # Step 1: Evaluate the attempt
            attempt_eval_input = {
                "problem_description": inputs["problem_description"],
                "user_code": inputs["user_code"]
            }
            attempt_eval_response = self.attempt_evaluation_chain.invoke(attempt_eval_input)
            attempt_evaluation = self._parse_attempt_evaluation(attempt_eval_response)
            logger.info(f"✅ Step 1 - Attempt evaluation completed: {attempt_evaluation.get('success', 'Unknown')}")
            
            # Update hint level and type based on attempt evaluation (after 1st LLM call)
            logger.info("🎯 Updating hint level and type based on attempt evaluation...")
            current_hint_level = inputs.get("current_hint_level", 1)
            attempts_count = inputs.get("attempts_count", 0)
            failed_attempts_count = inputs.get("failed_attempts_count", 0)
            time_since_last_attempt = inputs.get("time_since_last_attempt", 0)
            
            new_hint_level = self._get_next_hint_level(
                current_hint_level, failed_attempts_count, time_since_last_attempt, attempt_evaluation
            )
            new_hint_type = self._get_hint_type(new_hint_level, attempt_evaluation)
            
            logger.info(f"📈 Updated hint level: {current_hint_level} → {new_hint_level}")
            logger.info(f"🏷️  Updated hint type: {new_hint_type}")
            
            # Step 2: Generate hint with updated level and type (using RAG when possible)
            user_id = inputs.get("user_id")
            problem_id = inputs.get("problem_id")
            
            # Try RAG-enhanced hint generation first
            if user_id and problem_id:
                try:
                    logger.info("🎯 Attempting RAG-enhanced hint generation...")
                    generated_hint = self.rag_service.generate_rag_enhanced_hint(
                        problem_description=inputs["problem_description"],
                        user_code=inputs["user_code"],
                        previous_hints=inputs.get("previous_hints", []),
                        hint_level=new_hint_level,
                        user_progress={
                            "attempts_count": attempts_count,
                            "failed_attempts_count": failed_attempts_count,
                            "current_hint_level": new_hint_level,
                            "time_since_last_attempt": time_since_last_attempt
                        },
                        hint_type=new_hint_type,
                        user_id=user_id,
                        problem_id=problem_id
                    )
                    logger.info(f"✅ Step 2 - RAG-enhanced hint generated: {len(generated_hint)} characters")
                except Exception as e:
                    logger.warning(f"⚠️ RAG hint generation failed, falling back to basic: {e}")
                    # Fallback to basic hint generation
                    hint_gen_input = {
                        "problem_description": inputs["problem_description"],
                        "user_code": inputs["user_code"],
                        "attempts_count": attempts_count,
                        "failed_attempts_count": failed_attempts_count,
                        "current_hint_level": new_hint_level,
                        "time_since_last_attempt": time_since_last_attempt,
                        "previous_hints": inputs.get("previous_hints", []),
                        "hint_level": new_hint_level,
                        "hint_type": new_hint_type
                    }
                    generated_hint = self.hint_generation_chain.invoke(hint_gen_input)
                    logger.info(f"✅ Step 2 - Basic hint generated: {len(generated_hint)} characters")
            else:
                # Use basic hint generation if user_id or problem_id not available
                hint_gen_input = {
                    "problem_description": inputs["problem_description"],
                    "user_code": inputs["user_code"],
                    "attempts_count": attempts_count,
                    "failed_attempts_count": failed_attempts_count,
                    "current_hint_level": new_hint_level,
                    "time_since_last_attempt": time_since_last_attempt,
                    "previous_hints": inputs.get("previous_hints", []),
                    "hint_level": new_hint_level,
                    "hint_type": new_hint_type
                }
                generated_hint = self.hint_generation_chain.invoke(hint_gen_input)
                logger.info(f"✅ Step 2 - Basic hint generated: {len(generated_hint)} characters")
            
            # Step 3: Evaluate the hint with updated level
            hint_eval_input = {
                "problem_description": inputs["problem_description"],
                "user_code": inputs["user_code"],
                "attempts_count": attempts_count,
                "failed_attempts_count": failed_attempts_count,
                "current_hint_level": new_hint_level,  # Use updated level
                "time_since_last_attempt": time_since_last_attempt,
                "previous_hints": inputs.get("previous_hints", []),
                "hint_content": generated_hint
            }
            hint_eval_response = self.hint_evaluation_chain.invoke(hint_eval_input)
            hint_evaluation = self._parse_hint_evaluation(hint_eval_response)
            logger.info(f"✅ Step 3 - Hint evaluation completed")
            
            return {
                "attempt_evaluation": attempt_evaluation,
                "generated_hint": generated_hint,
                "hint_evaluation": hint_evaluation,
                "updated_hint_level": new_hint_level,
                "updated_hint_type": new_hint_type
            }
        
        # Main workflow as a simple chain
        self.main_workflow = RunnableLambda(run_workflow)
        
        logger.info("✅ Main workflow chain built successfully")

    def _get_next_hint_level(self, current_level: int, failed_attempts: int, time_since_last: float, attempt_evaluation: dict) -> int:
        """
        Determine the next hint level based on user progress and attempt evaluation.
        Hint levels:
        1. Conceptual (Basic understanding)
        2. Approach (Problem-solving strategy)
        3. Implementation (Code structure)
        4. Debug (Specific issues)
        5. Solution (Almost complete solution)
        """
        logger.info("🎯 Determining next hint level...")
        logger.info(f"   - Current hint level: {current_level}")
        logger.info(f"   - Failed attempts: {failed_attempts}")
        logger.info(f"   - Time since last attempt: {time_since_last:.2f} seconds")
        
        # If user has made multiple failed attempts, increase hint level
        if failed_attempts >= 3:
            new_level = min(current_level + 1, 5)
            logger.info(f"   - Increasing level due to multiple failures: {current_level} → {new_level}")
            return new_level
            
        # If user is stuck (inactive for 5+ minutes), increase hint level
        if time_since_last > 300:  # 5 minutes
            new_level = min(current_level + 1, 5)
            logger.info(f"   - Increasing level due to user being stuck: {current_level} → {new_level}")
            return new_level
            
        # If attempt evaluation shows specific issues, adjust level accordingly
        if attempt_evaluation.get('edge_cases'):
            # If missing edge cases, focus on implementation level
            new_level = max(3, current_level)
            logger.info(f"   - Adjusting level for edge case issues: {current_level} → {new_level}")
            return new_level
            
        # If code has complexity issues, focus on approach level
        if 'complexity' in attempt_evaluation.get('reason', '').lower():
            new_level = max(2, current_level)
            logger.info(f"   - Adjusting level for complexity issues: {current_level} → {new_level}")
            return new_level
            
        # If basic logic issues, focus on conceptual level
        if 'logic' in attempt_evaluation.get('reason', '').lower():
            new_level = max(1, current_level)
            logger.info(f"   - Adjusting level for logic issues: {current_level} → {new_level}")
            return new_level
            
        # Default: stay at current level
        logger.info(f"   - Keeping current level: {current_level}")
        return current_level

    def _get_hint_type(self, hint_level: int, attempt_evaluation: dict) -> str:
        """
        Determine the hint type based on hint level and attempt evaluation.
        Hint types:
        - conceptual: Basic understanding (level 1)
        - approach: Problem-solving strategy (level 2)
        - implementation: Code structure (level 3)
        - debug: Specific issues (level 4)
        """
        logger.info("🏷️  Determining hint type...")
        logger.info(f"   - Hint level: {hint_level}")
        
        # If there are specific issues in the code, use debug type
        if attempt_evaluation.get('edge_cases') or 'error' in attempt_evaluation.get('reason', '').lower():
            hint_type = 'debug'
            logger.info(f"   - Using debug type due to specific issues")
            return hint_type
            
        # If there are complexity issues, use approach type
        if 'complexity' in attempt_evaluation.get('reason', '').lower():
            hint_type = 'approach'
            logger.info(f"   - Using approach type due to complexity issues")
            return hint_type
            
        # Map hint levels to types
        hint_type_map = {
            1: 'conceptual',
            2: 'approach',
            3: 'implementation',
            4: 'debug',
            5: 'debug'  # Level 5 is also debug as it's for specific issues
        }
        
        hint_type = hint_type_map.get(hint_level, 'conceptual')
        logger.info(f"   - Mapped hint level {hint_level} to type: {hint_type}")
        return hint_type

    def _parse_attempt_evaluation(self, response: str) -> Dict[str, Any]:
        """Parse attempt evaluation response with robust error handling"""
        result = {
            'success': False,
            'reason': '',
            'complexity': '',
            'edge_cases': [],
            'code_quality': '',
            'suggestions': [],
            'error_pattern': '',
            'error_category': ''
        }
        
        try:
            for line in response.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if key == 'success':
                        result['success'] = value.lower() == 'true'
                    elif key == 'reason':
                        result['reason'] = value
                    elif key == 'complexity':
                        result['complexity'] = value
                    elif key == 'edge_cases':
                        result['edge_cases'] = [case.strip() for case in value.split(',') if case.strip()]
                    elif key == 'code_quality':
                        result['code_quality'] = value
                    elif key == 'suggestions':
                        result['suggestions'] = [suggestion.strip() for suggestion in value.split(',') if suggestion.strip()]
                    elif key == 'error_pattern':
                        result['error_pattern'] = value
                    elif key == 'error_category':
                        result['error_category'] = value
        except Exception as e:
            logger.error(f"Error parsing attempt evaluation: {e}")
        
        return result

    def _parse_hint_evaluation(self, response: str) -> Dict[str, float]:
        """Parse hint evaluation response with robust error handling"""
        scores = {}
        
        try:
            for line in response.split('\n'):
                line = line.strip()
                if not line:
                    continue
                
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower()
                    
                    # Clean up markdown formatting from key
                    key = key.replace('**', '').replace('*', '').replace('-', '').strip()
                    
                    try:
                        score = float(value.strip())
                        if 0 <= score <= 1:  # Ensure score is between 0 and 1
                            scores[key] = score
                    except (ValueError, IndexError):
                        continue
            
            # Ensure all required scores are present
            required_scores = [
                'safety_score',
                'helpfulness_score',
                'quality_score',
                'progress_alignment_score',
                'pedagogical_value_score'
            ]
            
            # Set default score of 0.5 for any missing scores
            for score in required_scores:
                if score not in scores:
                    scores[score] = 0.5
            
        except Exception as e:
            logger.error(f"Error parsing hint evaluation: {e}")
            # Return default scores if parsing fails
            scores = {
                'safety_score': 0.5,
                'helpfulness_score': 0.5,
                'quality_score': 0.5,
                'progress_alignment_score': 0.5,
                'pedagogical_value_score': 0.5
            }
        
        return scores

    def _parse_auto_trigger_decision(self, response: str) -> Tuple[bool, str, str, int]:
        """Parse auto-trigger decision response with robust error handling"""
        should_trigger = False
        reason = ""
        hint_type = "conceptual"
        hint_level = 1
        
        try:
            lines = response.split('\n')
            for line in lines:
                line = line.strip().lower()
                if "decision:" in line:
                    should_trigger = "yes" in line
                elif "reason:" in line:
                    reason = line.split("reason:")[1].strip()
                elif "hint_type:" in line:
                    hint_type = line.split("hint_type:")[1].strip()
                elif "hint_level:" in line:
                    try:
                        hint_level = int(line.split("hint_level:")[1].strip())
                    except (ValueError, IndexError):
                        hint_level = 1
        except Exception as e:
            logger.error(f"Error parsing auto-trigger decision: {e}")
        
        return should_trigger, reason, hint_type, hint_level

    def process_hint_request(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a complete hint request using the LangChain workflow
        
        Args:
            inputs: Dictionary containing all necessary data
            
        Returns:
            Dictionary with attempt_evaluation, generated_hint, and hint_evaluation
        """
        logger.info("🔄 Starting hint request processing with LangChain workflow...")
        
        try:
            # Execute the main workflow
            result = self.main_workflow.invoke(inputs)
            
            logger.info("✅ Workflow completed successfully")
            logger.info(f"   - Attempt evaluation: {result['attempt_evaluation'].get('success', 'Unknown')}")
            logger.info(f"   - Hint generated: {len(result['generated_hint'])} characters")
            logger.info(f"   - Hint evaluation scores: {result['hint_evaluation']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}")
            # Return fallback results
            return {
                "attempt_evaluation": {
                    "success": False,
                    "reason": "Workflow failed",
                    "complexity": "Unknown",
                    "edge_cases": [],
                    "code_quality": "Unknown",
                    "suggestions": ["Check your code implementation"]
                },
                "generated_hint": "Consider breaking down the problem into smaller steps.",
                "hint_evaluation": {
                    "safety_score": 0.8,
                    "helpfulness_score": 0.7,
                    "quality_score": 0.8,
                    "progress_alignment_score": 0.7,
                    "pedagogical_value_score": 0.8
                }
            }

    def check_auto_trigger(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if a hint should be auto-triggered using the auto-trigger chain
        
        Args:
            inputs: Dictionary containing user progress and attempt data
            
        Returns:
            Dictionary with auto-trigger decision
        """
        logger.info("🤖 Checking auto-trigger with LangChain...")
        
        try:
            response = self.auto_trigger_chain.invoke(inputs)
            should_trigger, reason, hint_type, hint_level = self._parse_auto_trigger_decision(response)
            
            result = {
                "should_trigger": should_trigger,
                "reason": reason,
                "hint_type": hint_type,
                "hint_level": hint_level
            }
            
            logger.info(f"✅ Auto-trigger decision: {should_trigger}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Auto-trigger check failed: {e}")
            return {
                "should_trigger": False,
                "reason": "Auto-trigger check failed",
                "hint_type": "conceptual",
                "hint_level": 1
            }

    def evaluate_attempt_only(self, problem_description: str, user_code: str) -> Dict[str, Any]:
        """
        Evaluate only the user's attempt (standalone)
        
        Args:
            problem_description: Description of the problem
            user_code: User's submitted code
            
        Returns:
            Dictionary with attempt evaluation
        """
        logger.info("🔍 Evaluating attempt with LangChain...")
        
        try:
            response = self.attempt_evaluation_chain.invoke({
                "problem_description": problem_description,
                "user_code": user_code
            })
            result = self._parse_attempt_evaluation(response)
            logger.info(f"✅ Attempt evaluation completed: {result.get('success', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Attempt evaluation failed: {e}")
            return {
                "success": False,
                "reason": "Evaluation failed",
                "complexity": "Unknown",
                "edge_cases": [],
                "code_quality": "Unknown",
                "suggestions": ["Check your implementation"]
            } 