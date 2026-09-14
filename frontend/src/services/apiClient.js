// API client for handling requests to the backend
const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api';

let globalAuthToken = null;

export const setAuthToken = (token) => {
  globalAuthToken = token;
};

/**
 * Make an API request with fetch
 * @param {string} endpoint - The API endpoint (without the base URL)
 * @param {Object} options - Fetch options like method, body, headers
 * @returns {Promise<Object>} - Promise resolving to the JSON response
 */
export async function apiRequest(endpoint, options = {}) {
  // Set up default headers
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...options.headers,
  };

  if (globalAuthToken) {
    headers['Authorization'] = `Bearer ${globalAuthToken}`;
  }

  // Log the request for debugging
  console.log(`Making API request to: ${API_URL}${endpoint}`);

  // Make the request with CORS mode
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
    mode: 'cors',
    credentials: 'same-origin',
  });

  // Handle errors
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({
      message: 'An error occurred while fetching data'
    }));
    
    throw new Error(errorData.message || `API Error: ${response.status}`);
  }

  // Return the response data
  return response.json();
}

/**
 * GET request helper
 * @param {string} endpoint - The API endpoint
 * @param {Object} options - Additional fetch options
 */
export function get(endpoint, options = {}) {
  return apiRequest(endpoint, { ...options, method: 'GET' });
}

/**
 * POST request helper
 * @param {string} endpoint - The API endpoint
 * @param {Object} data - Request body data
 * @param {Object} options - Additional fetch options
 */
export function post(endpoint, data, options = {}) {
  return apiRequest(endpoint, {
    ...options,
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * PUT request helper
 * @param {string} endpoint - The API endpoint
 * @param {Object} data - Request body data
 * @param {Object} options - Additional fetch options
 */
export function put(endpoint, data, options = {}) {
  return apiRequest(endpoint, {
    ...options,
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

/**
 * DELETE request helper
 * @param {string} endpoint - The API endpoint
 * @param {Object} options - Additional fetch options
 */
export function del(endpoint, options = {}) {
  return apiRequest(endpoint, { ...options, method: 'DELETE' });
}

// Export the default client object
export default {
  get,
  post,
  put,
  delete: del
};