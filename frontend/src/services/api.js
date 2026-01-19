import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://0.0.0.0:8001';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Get suggestions for a travel query
 * @param {string} query - The user's query text
 * @param {number} cursorPosition - Optional cursor position
 * @param {object} context - Optional context object
 * @returns {Promise<object>} Suggestion response
 */
export const getSuggestions = async (query, cursorPosition = null, context = {}) => {
  try {
    const response = await api.post('/suggest', {
      query,
      cursor_position: cursorPosition,
      context,
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching suggestions:', error);
    throw error;
  }
};

export default api;
