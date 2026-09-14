# Frontend-Backend API Requirements

This document outlines the required backend endpoints for our LeetCode-style frontend with hint functionality.

## Current Backend Endpoints

Based on the analysis of the existing backend codebase, here are the currently implemented endpoints:

### 1. Hints API

#### `POST /api/hints/request_hint/`
- **Description**: Request a hint for a specific problem
- **Request Body**:
  ```json
  {
    "user_id": 123,
    "problem_id": 456,
    "user_code": "function solution() { ... }",
    "problem_data": {
      "title": "Two Sum",
      "description": "Given an array of integers..."
    }
  }
  ```
- **Response**:
  ```json
  {
    "status": "success|failed",
    "hint": {
      "id": 1,
      "content": "Think about using a hash map...",
      "level": 1,
      "type": "conceptual"
    },
    "evaluation": {
      "safety_score": 0.95,
      "helpfulness_score": 0.85,
      "quality_score": 0.9,
      "progress_alignment_score": 0.8,
      "pedagogical_value_score": 0.85
    },
    "attempt_id": 123,
    "attempt_evaluation": {
      "success": false,
      "reason": "Failed test cases",
      "complexity": "O(n^2)",
      "edge_cases": ["Empty array", "No solution"]
    },
    "user_progress": {
      "attempts_count": 5,
      "failed_attempts_count": 3,
      "current_hint_level": 2,
      "is_stuck": false,
      "time_since_last_attempt": 120
    }
  }
  ```

#### `POST /api/hints/check_auto_trigger/`
- **Description**: Check if a hint should be automatically triggered
- **Request Body**: Same as `request_hint`
- **Response**:
  ```json
  {
    "should_trigger": true,
    "hint": {
      "id": 1,
      "content": "Check if your algorithm handles edge cases...",
      "level": 2,
      "type": "implementation"
    },
    "evaluation": { ... },
    "attempt_id": 124,
    "user_progress": { ... }
  }
  ```

#### `POST /api/hints/{hint_delivery_id}/provide_feedback/`
- **Description**: Provide feedback on a delivered hint
- **Request Body**:
  ```json
  {
    "feedback": "This hint was helpful",
    "rating": 4
  }
  ```
- **Response**:
  ```json
  {
    "status": "Feedback recorded successfully",
    "hint_id": 1,
    "attempt_id": 123
  }
  ```

## Required Frontend Endpoints (Not Currently Implemented)

The following endpoints are required for our frontend but are not currently implemented in the backend:

### 1. User Authentication

#### `POST /api/auth/register/`
- **Description**: Register a new user
- **Request Body**:
  ```json
  {
    "username": "user123",
    "email": "user@example.com",
    "password": "securepassword"
  }
  ```

#### `POST /api/auth/login/`
- **Description**: Login a user
- **Request Body**:
  ```json
  {
    "username": "user123",
    "password": "securepassword"
  }
  ```

#### `POST /api/auth/logout/`
- **Description**: Logout a user
- **Authentication**: Required

### 2. Problems API

#### `GET /api/problems/`
- **Description**: List all problems with pagination, filtering, and sorting
- **Query Parameters**:
  - `page`: Page number
  - `limit`: Items per page
  - `topic`: Filter by topic
  - `difficulty`: Filter by difficulty
  - `search`: Search term
  - `sort`: Sort field

#### `GET /api/problems/{id}/`
- **Description**: Get detailed information about a specific problem
- **Response**: Complete problem data including description, tests, and starting code

### 3. Code Submission API

#### `POST /api/submissions/`
- **Description**: Submit code for evaluation
- **Request Body**:
  ```json
  {
    "user_id": 123,
    "problem_id": 456,
    "code": "function solution() { ... }",
    "language": "javascript"
  }
  ```
- **Response**: Test results and evaluation

#### `GET /api/submissions/user/{user_id}/`
- **Description**: Get a user's submission history
- **Authentication**: Required

### 4. Topics API

#### `GET /api/topics/`
- **Description**: Get list of all available problem topics
- **Response**: Array of topic names

## Backend-Frontend Integration Plan

### Phase 1: Backend Enhancements
1. Implement user authentication endpoints
2. Create Problems API endpoints
3. Implement code submission endpoints

### Phase 2: Frontend Integration
1. Update frontend API service to use real backend endpoints
2. Implement authentication flow
3. Connect problem listing and filtering to backend
4. Integrate code submission with backend
5. Connect hint request functionality to existing backend endpoints

### Phase 3: Testing & Refinement
1. Test all API integrations
2. Address any performance issues
3. Implement error handling for API failures
4. Add retry mechanisms for unreliable endpoints

## Current Gaps in Backend Implementation

1. **User Authentication System**: The backend has no user authentication system. It currently uses `user_id` directly in requests without verification.

2. **Problem Management**: The backend can store problems, but there are no endpoints to list, filter, or retrieve problems.

3. **Code Submission & Evaluation**: While the backend can evaluate code as part of hint requests, there's no dedicated endpoint for submitting and evaluating code.

4. **Topics Management**: No endpoint to get a list of available topics for filtering problems.

5. **User Profile & Progress**: The backend tracks progress per problem but lacks endpoints to view overall user progress.

The most critical gaps are the lack of authentication and problems listing/retrieval endpoints, as these are fundamental to the frontend experience.