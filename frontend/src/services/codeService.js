import apiClient from './apiClient';

/**
 * Service for handling code execution and submission
 * Note: These endpoints need to be implemented on the backend
 */
const codeService = {
  /**
   * Run code against test cases
   * @param {number} userId - The user ID
   * @param {number} problemId - The problem ID
   * @param {string} code - The code to run
   * @param {string} language - The programming language
   * @returns {Promise<Object>} - Promise resolving to execution results
   */
  runCode: async (userId, problemId, code, language, customInput = null) => {
    const payload = {
      user_id: userId,
      problem_id: problemId,
      code,
      language
    };
    if (customInput !== null && customInput !== '') {
      payload.custom_input = customInput;
    }
    return apiClient.post('/code/run/', payload);
  },
  
  /**
   * Submit a solution for a problem
   * @param {number} userId - The user ID
   * @param {number} problemId - The problem ID
   * @param {string} code - The solution code
   * @param {string} language - The programming language
   * @returns {Promise<Object>} - Promise resolving to submission results
   */
  submitSolution: async (userId, problemId, code, language) => {
    return apiClient.post('/code/submit/', {
      user_id: userId,
      problem_id: problemId,
      code,
      language
    });
  },

  /**
   * Fetch submission history for a problem
   * @param {number} userId - The user ID
   * @param {number} problemId - The problem ID
   * @returns {Promise<Array>} - Promise resolving to an array of attempts
   */
  getHistory: async (userId, problemId) => {
    return apiClient.get(`/code/history/?user_id=${userId}&problem_id=${problemId}`);
  }
};

export default codeService;