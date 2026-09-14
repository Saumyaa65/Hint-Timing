import apiClient from './apiClient';

/**
 * Service for handling problem-related API requests
 * Note: These endpoints need to be implemented on the backend
 */
const problemService = {
  /**
   * Get all problems
   * @param {Object} filters - Optional filters (topic, difficulty)
   * @returns {Promise<Array>} - Promise resolving to an array of problems
   */
  getAllProblems: async (filters = {}) => {
    const queryParams = new URLSearchParams();
    
    // Add filters if they exist
    if (filters.topic) queryParams.append('topic', filters.topic);
    if (filters.difficulty) queryParams.append('difficulty', filters.difficulty);
    if (filters.search) queryParams.append('search', filters.search);
    
    const queryString = queryParams.toString();
    const endpoint = queryString ? `/problems/?${queryString}` : '/problems/';
    
    console.log(`Making request to endpoint: ${endpoint}`);
    try {
      const response = await apiClient.get(endpoint);
      console.log('Response:', response);
      return response;
    } catch (error) {
      console.error('Error in getAllProblems:', error);
      throw error;
    }
  },
  
  /**
   * Get a single problem by ID
   * @param {number} problemId - The problem ID
   * @returns {Promise<Object>} - Promise resolving to problem data
   */
  getProblemById: async (problemId) => {
    return apiClient.get(`/problems/${problemId}/`);
  },
  
  /**
   * Get all available topics
   * @returns {Promise<Array>} - Promise resolving to an array of topic names
   */
  getTopics: async () => {
    return apiClient.get('/problems/topics/');
  }
};

export default problemService;