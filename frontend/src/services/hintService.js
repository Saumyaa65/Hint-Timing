import apiClient from './apiClient';

/**
 * Service for handling hint-related API requests
 */
const hintService = {
  /**
   * Request a hint for a specific problem
   * @param {number} userId - The user ID
   * @param {number} problemId - The problem ID
   * @param {string} userCode - The user's current code
   * @param {Object} problemData - Optional problem data if problem doesn't exist
   * @returns {Promise<Object>} - Promise resolving to hint data
   */
  requestHint: async (userId, problemId, userCode, problemData = null, sessionId = null) => {
    const payload = {
      user_id: userId,
      problem_id: problemId,
      user_code: userCode
    };
    
    // Add problem data if provided
    if (problemData) {
      payload.problem_data = problemData;
    }
    if (sessionId) {
      payload.session_id = sessionId;
    }
    
    return apiClient.post('/hints/request_hint/', payload);
  },
  
  /**
   * Check if a hint should be auto-triggered
   * @param {number} userId - The user ID
   * @param {number} problemId - The problem ID
   * @param {string} userCode - The user's current code
   * @param {Object} problemData - Optional problem data if problem doesn't exist
   * @param {string} [sessionId] - Optional session ID
   * @returns {Promise<Object>} - Promise resolving to auto-trigger data
   */
  checkAutoTrigger: async (userId, problemId, userCode, problemData = null, sessionId = null) => {
    const payload = {
      user_id: userId,
      problem_id: problemId,
      user_code: userCode
    };
    
    // Add problem data if provided
    if (problemData) {
      payload.problem_data = problemData;
    }
    if (sessionId) {
      payload.session_id = sessionId;
    }
    
    return apiClient.post('/hints/check_auto_trigger/', payload);
  },
  
  /**
   * Provide feedback on a hint
   * @param {number} hintDeliveryId - The hint delivery ID
   * @param {string} feedback - User feedback text
   * @param {number} rating - Rating from 1-5
   * @returns {Promise<Object>} - Promise with feedback submission result
   */
  provideFeedback: async (hintDeliveryId, feedback, rating) => {
    return apiClient.post(`/hints/${hintDeliveryId}/provide_feedback/`, {
      feedback,
      rating
    });
  }
};

export default hintService;