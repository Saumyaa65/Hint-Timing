import apiClient from './apiClient';

/**
 * Service for handling user authentication
 * Note: These endpoints need to be implemented on the backend
 */
const authService = {
  /**
   * Register a new user
   * @param {string} name - User's name
   * @param {string} email - User's email
   * @param {string} password - User's password
   * @returns {Promise<Object>} - Promise resolving to user data
   */
  register: async (name, email, password) => {
    return apiClient.post('/auth/register/', {
      name,
      email,
      password
    });
  },
  
  /**
   * Log in a user
   * @param {string} email - User's email
   * @param {string} password - User's password
   * @returns {Promise<Object>} - Promise resolving to user data and token
   */
  login: async (email, password) => {
    return apiClient.post('/auth/login/', {
      email,
      password
    });
  },
  
  /**
   * Log out the current user
   * @returns {Promise<Object>} - Promise resolving to success message
   */
  logout: async () => {
    return apiClient.post('/auth/logout/');
  },
  
  /**
   * Get the current user's profile
   * @returns {Promise<Object>} - Promise resolving to user data
   */
  getCurrentUser: async () => {
    return apiClient.get('/auth/me/');
  },
  
  /**
   * Store user data in localStorage
   * @param {Object} userData - User data to store
   */
  setUser: (userData) => {
    localStorage.setItem('user', JSON.stringify(userData));
  },
  
  /**
   * Get user data from localStorage
   * @returns {Object|null} - User data or null if not logged in
   */
  getUser: () => {
    const userData = localStorage.getItem('user');
    return userData ? JSON.parse(userData) : null;
  },
  
  /**
   * Clear user data from localStorage
   */
  clearUser: () => {
    localStorage.removeItem('user');
  }
};

export default authService;