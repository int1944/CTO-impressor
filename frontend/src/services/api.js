import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://10.106.104.140:8001";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Get suggestions for a travel query
 * @param {string} query - The user's query text
 * @param {number} cursorPosition - Optional cursor position
 * @param {object} context - Optional context object
 * @param {AbortSignal} signal - Optional abort signal for request cancellation
 * @returns {Promise<object>} Suggestion response
 */
export const getSuggestions = async (
  query,
  cursorPosition = null,
  context = {},
  signal = null
) => {
  try {
    const response = await api.post(
      "/suggest",
      {
        query,
        cursor_position: cursorPosition,
        context,
      },
      {
        signal, // Pass abort signal to axios
      }
    );
    return response.data;
  } catch (error) {
    // Don't log abort errors as they're expected
    if (error.name !== 'CanceledError' && error.code !== 'ERR_CANCELED') {
      console.error("Error fetching suggestions:", error);
    }
    throw error;
  }
};

/**
 * Search for cities by name
 * @param {string} query - The search query (city name)
 * @param {number} limit - Maximum number of results
 * @returns {Promise<object>} City search response
 */
export const searchCities = async (query, limit = 10) => {
  try {
    const cityApiUrl = import.meta.env.VITE_CITY_API_URL || "http://localhost:8000";
    const response = await axios.get(`${cityApiUrl}/search`, {
      params: {
        q: query,
        limit: limit
      }
    });
    return response.data;
  } catch (error) {
    console.error("Error searching cities:", error);
    throw error;
  }
};

export default api;
