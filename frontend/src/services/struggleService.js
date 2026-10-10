import apiClient from './apiClient';

/**
 * Service for handling struggle analysis and M4 hybrid assessment
 */
const struggleService = {
  /**
   * Assess struggle state using Condition M4: Refined Hybrid Model
   * @param {string|number} userId - The user ID
   * @param {string|number} problemId - The problem ID
   * @param {string} [sessionId] - Optional session ID for trajectory scoping
   * @returns {Promise<Object>} - Promise resolving to hybrid assessment results
   */
  assessHybrid: async (userId, problemId, sessionId = null) => {
    let url = `/struggle-analysis/hybrid/${problemId}/?user_id=${encodeURIComponent(userId)}`;
    if (sessionId) {
      url += `&session_id=${encodeURIComponent(sessionId)}`;
    }
    return apiClient.get(url);
  }
};

export default struggleService;
