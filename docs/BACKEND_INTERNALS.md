# Hint Generation System

> **Note:** This is a production-only, minimal codebase. All development, test, and legacy files have been removed for clarity and maintainability. The main workflow is orchestrated by `hints/hint_chain.py` and exposed via `hints/views.py`.

A Django-based backend system for generating adaptive, personalized hints for programming problems using RAG (Retrieval Augmented Generation). The system uses LLMs (Large Language Models) to generate context-aware hints based on user progress, code attempts, and learning history.

## Features

### Adaptive Hint Generation

The system generates hints based on multiple factors:

- **User's Current Progress**: Tracks how far the user has progressed in solving the problem
- **Previous Attempts**: Analyzes past code submissions and their outcomes
- **Code Evaluation**: Assesses the correctness and quality of submitted code
- **Hint Level Progression**: Adapts hint complexity based on user's current level
- **Specific Issues**: Identifies and addresses particular problems in the code

### RAG (Retrieval Augmented Generation)

The system uses RAG to provide personalized, context-aware hints by:

- **Similar Problem Retrieval**: Finds problems the user has attempted before using TF-IDF similarity
- **User Solution Analysis**: Extracts successful solutions from user's history
- **Error Pattern Detection**: Identifies common errors from failed attempts with classification
- **Context Building**: Combines retrieved information for enhanced hint generation
- **Fallback Mechanism**: Gracefully falls back to basic hints when RAG context is unavailable

#### RAG Features:
- **User-Specific Learning**: Only uses data from the requesting user (privacy-focused)
- **Similarity Threshold**: Only considers problems with >0.3 similarity for relevance
- **Error Pattern Classification**: Categorizes errors (time_complexity, logic_error, edge_case_missing, wrong_approach, syntax_error, etc.)
- **Smart Context Truncation**: Optimizes context length for LLM efficiency (1500 char limit)
- **Learning Pattern Analysis**: Tracks user's learning patterns and preferences

### Hint Levels

The system uses a 5-level progression system:

1. **Conceptual (Level 1)** – Basic understanding, core concepts
2. **Approach (Level 2)** – Problem-solving strategies, algorithms
3. **Implementation (Level 3)** – Code structure, patterns, syntax
4. **Debug (Level 4)** – Logical/code errors, fixes
5. **Solution (Level 5)** – Nearly complete solution, for stuck users

### Hint Types

- **Conceptual**: Explains underlying concepts
- **Approach**: Suggests solution strategies
- **Implementation**: Focuses on code structure
- **Debug**: Identifies specific issues

### Progress Tracking

- **Attempts Count**: Total code submissions
- **Failed Attempts**: Incorrect submissions
- **Current Hint Level**: User's progression level
- **Time Since Last Activity**: User inactivity
- **User Stuck Detection**: Identifies struggling users

### Hint Evaluation

Each generated hint is evaluated on:

- **Safety Score**: Does not reveal too much
- **Helpfulness Score**: Effectiveness
- **Quality Score**: Clarity and precision
- **Progress Alignment**: Matches user's level
- **Pedagogical Value**: Educational effectiveness

## System Architecture

### Core Components:
- **HintChain**: Main workflow orchestrator with 3 LLM calls
- **RAGService**: Retrieval augmented generation for personalized hints
- **Views**: Django REST API endpoints
- **Models**: Database schema for problems, attempts, hints, and progress

### LLM Integration:
- **OpenRouter**: Primary LLM provider
- **Models Used**:
  - Attempt Evaluation: `qwen/qwen-2.5-coder-32b-instruct:free` (temp: 0.3)
  - Hint Generation: `deepseek/deepseek-r1-0528-qwen3-8b:free` (temp: 0.7)
  - Hint Evaluation: `deepseek/deepseek-r1-0528-qwen3-8b:free` (temp: 0.2)

### Performance Optimizations:
- **Database Query Optimization**: select_related() for reduced queries
- **Similarity Threshold**: Only processes relevant similar problems (>0.3)
- **Context Length Management**: Smart truncation for LLM efficiency
- **Early Exit**: Skips RAG for users with <3 attempts
- **TF-IDF Caching**: Maintains consistent vector dimensions

## Setup

1. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```
3. **Create a `.env` file in the backend directory**

   ```bash
   touch .env  # On Windows: type nul > .env
   ```
4. **Add the following to your `.env` file:**

   ```env
   # OpenRouter API Configuration
   OPENROUTER_API_KEY=your_openrouter_api_key_here

   # (Optional, if using TogetherAI or HuggingFace)
   TOGETHER_API_KEY=your_togetherai_or_huggingface_key_here

   # Django Configuration
   DEBUG=True
   SECRET_KEY=your_django_secret_key_here

   # LangSmith / LangChain Tracing Configuration
   LANGCHAIN_API_KEY=your_langsmith_api_key_here
   LANGSMITH_PROJECT=hg
   LANGSMITH_TRACING_V2=true
   LANGSMITH_ENDPOINT=https://api.smith.langchain.com

   # Compatibility/Alternative variable names (sometimes required)
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_PROJECT=hg
   LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
   ```
5. **Run database migrations**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
6. **Start the Django development server**

   ```bash
   python manage.py runserver
   ```

## API Endpoints

### Request Hint

```
POST /api/hints/request_hint/
```

Request body:

```json
{
    "user_id": 202,                // Unique identifier for the user
    "problem_id": 10,              // User-provided problem ID (will be stored)
    "user_code": "def isValid(s):...",  // The code submitted by the user
    "problem_data": {              // Required if problem doesn't exist
        "title": "Valid Parentheses",
        "description": "Determine if input string has valid bracket ordering..."
    }
}
```

Response:

```json
{
    "status": "failed",            // 'success' or 'failed'
    "hint": {
        "id": 14,                  // Unique identifier for the hint
        "content": "Use a stack to track opening brackets...",  // The hint text
        "level": 3,                // Hint level (1-5)
        "type": "debug"            // Hint type (conceptual/approach/implementation/debug)
    },
    "evaluation": {
        "safety_score": 0.9,       // How much of the solution is revealed (0-1)
        "helpfulness_score": 0.8,  // How helpful the hint is (0-1)
        "quality_score": 0.85,     // Overall quality of the hint (0-1)
        "progress_alignment_score": 0.9, // How well it matches user's level (0-1)
        "pedagogical_value_score": 0.8   // Educational value (0-1)
    },
    "attempt_id": 14,              // Unique identifier for this attempt
    "attempt_evaluation": {
        "success": false,          // Whether the code is correct
        "reason": "The code doesn't handle edge cases properly", // Explanation
        "complexity": "O(n) time, O(1) space", // Time and space complexity
        "edge_cases": ["empty array", "no solution"], // List of edge cases
        "code_quality": "Good", // Assessment of code quality
        "suggestions": ["Consider using a stack for better handling of edge cases"], // Specific suggestions for improvement
        "error_pattern": "edge_case_missing", // Classified error type
        "error_category": "completeness" // Error category
    },
    "user_progress": {
        "attempts_count": 5,       // Total attempts made
        "failed_attempts_count": 3, // Total failed attempts
        "current_hint_level": 5,   // Current hint level (1-5)
        "is_stuck": false,         // Whether user is stuck
        "time_since_last_attempt": 1262.84 // Seconds since last attempt
    }
}
```

## Models

### Problem

- `id`: AutoField (Primary Key)
- `problem_id`: IntegerField (User-provided problem ID, unique)
- `title`: CharField (Problem Title)
- `description`: TextField (Detailed Problem Description)
- `difficulty`: CharField (Easy/Medium/Hard)
- `created_at`: DateTimeField (Creation Timestamp)
- `updated_at`: DateTimeField (Last Update Timestamp)

### UserProgress

- `user_id`: IntegerField (User Identifier)
- `problem`: ForeignKey to Problem (Related Problem)
- `last_activity`: DateTimeField (Last User Activity)
- `attempts_count`: IntegerField (Total Attempts)
- `failed_attempts_count`: IntegerField (Failed Attempts)
- `current_hint_level`: IntegerField (Current Hint Level)

### Attempt

- `user_id`: IntegerField (User Identifier)
- `problem`: ForeignKey to Problem (Related Problem)
- `code`: TextField (Submitted Code)
- `status`: CharField (Success/Failed)
- `evaluation_details`: JSONField (Detailed Evaluation with error patterns)
- `created_at`: DateTimeField (Creation Timestamp)
- `updated_at`: DateTimeField (Last Update Timestamp)

**Enhanced evaluation_details includes:**
- `success`: Boolean (Code correctness)
- `reason`: String (Explanation)
- `complexity`: String (Time/space complexity)
- `edge_cases`: Array (Handled/missed edge cases)
- `code_quality`: String (Assessment of code quality)
- `suggestions`: Array (Specific suggestions for improvement)
- `error_pattern`: String (Classified error type: time_complexity, logic_error, edge_case_missing, wrong_approach, syntax_error, boundary_condition, data_structure_misuse, algorithm_choice, null_pointer, index_error, type_error, or other)
- `error_category`: String (Error category: performance, correctness, completeness, or other)

### Hint

- `problem`: ForeignKey to Problem (Related Problem)
- `content`: TextField (Hint Content)
- `level`: IntegerField (Hint Level 1-5)
- `hint_type`: CharField (Conceptual/Approach/Implementation/Debug)
- `created_at`: DateTimeField (Creation Timestamp)
- `updated_at`: DateTimeField (Last Update Timestamp)

### HintDelivery

- `hint`: ForeignKey to Hint (Related Hint)
- `user_id`: IntegerField (User Identifier)
- `attempt`: ForeignKey to Attempt (Related Attempt)
- `is_auto_triggered`: BooleanField (Auto-Triggered Flag)
- `created_at`: DateTimeField (Creation Timestamp)
- `updated_at`: DateTimeField (Last Update Timestamp)

### HintEvaluation

- `hint`: ForeignKey to Hint (Related Hint)
- `safety_score`: FloatField (Safety Score 0-1)
- `helpfulness_score`: FloatField (Helpfulness Score 0-1)
- `quality_score`: FloatField (Quality Score 0-1)
- `progress_alignment_score`: FloatField (Progress Alignment 0-1)
- `pedagogical_value_score`: FloatField (Pedagogical Value 0-1)
- `created_at`: DateTimeField (Creation Timestamp)
- `updated_at`: DateTimeField (Last Update Timestamp)

## Hint Generation Process

1. **Attempt Evaluation**: User submits code, system evaluates correctness, identifies issues, determines if hint is needed
2. **Progress Tracking**: Updates attempt counts, failed attempts, user activity, detects if user is stuck
3. **Hint Level Determination**: Based on progress, failed attempts, inactivity, issues, current level
4. **Hint Type Selection**: Conceptual, Approach, Implementation, Debug—based on user need
5. **RAG Context Retrieval**: 
   - Find similar problems from user's history
   - Extract user's previous solutions
   - Identify error patterns from failed attempts
   - Build enhanced context for hint generation
6. **Hint Generation**: LLM generates context-aware hints, considers previous hints, adapts to user
7. **Hint Evaluation**: Evaluates hint quality, safety, helpfulness, alignment, pedagogical value

## Performance Metrics

### Response Times:
- **Total Response**: ~35-40 seconds (3 LLM calls)
- **RAG Processing**: ~2-3 seconds
- **Database Operations**: <1 second
- **LLM Call Breakdown**:
  - Attempt Evaluation: ~6-8 seconds
  - RAG-Enhanced Hint Generation: ~20-25 seconds
  - Hint Evaluation: ~3-5 seconds

### Quality Scores:
- **Safety Score**: 0.8-0.9 (excellent - doesn't reveal too much)
- **Helpfulness Score**: 0.7-0.8 (very good - effectively guides users)
- **Quality Score**: 0.8-0.85 (excellent - clear and precise)
- **Progress Alignment**: 0.7-0.9 (good - matches user's level)
- **Pedagogical Value**: 0.7-0.8 (good - educational effectiveness)

### System Reliability:
- **RAG Success Rate**: >95%
- **Fallback Mechanism**: Automatic when RAG fails
- **Error Handling**: Graceful degradation
- **Database Consistency**: Proper foreign key relationships
- **User Data Privacy**: Complete isolation between users

### RAG Performance:
- **Similar Problem Retrieval**: TF-IDF + cosine similarity
- **Context Optimization**: Smart truncation (1500 char limit)
- **Memory Efficiency**: Cached embeddings for problems
- **Query Optimization**: Limited to 3 most recent failed attempts per problem

## Error Pattern Classification

The system classifies errors into specific patterns for better hint generation:

### Error Patterns:
- **time_complexity**: Performance issues, inefficient algorithms
- **logic_error**: Incorrect algorithm logic
- **edge_case_missing**: Missing boundary conditions
- **wrong_approach**: Incorrect problem-solving strategy
- **syntax_error**: Code syntax issues
- **boundary_condition**: Array bounds, null checks
- **data_structure_misuse**: Incorrect data structure usage
- **algorithm_choice**: Wrong algorithm selection
- **null_pointer**: Null reference issues
- **index_error**: Array index problems
- **type_error**: Data type mismatches

### Error Categories:
- **performance**: Time/space complexity issues
- **correctness**: Logic and algorithm errors
- **completeness**: Missing edge cases and conditions
- **other**: Miscellaneous issues

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
