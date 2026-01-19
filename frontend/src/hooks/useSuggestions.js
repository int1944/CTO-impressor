import { useState, useEffect, useCallback } from "react";
import { getSuggestions } from "../services/api";
import { useDebounce } from "./useDebounce";

/**
 * Custom hook for fetching suggestions with debouncing
 * @param {string} query - The user's query text
 * @param {number} cursorPosition - Optional cursor position
 * @param {object} context - Optional context object
 * @returns {object} { suggestions, loading, error, intent, nextSlot, source, latency }
 */
export function useSuggestions(query, cursorPosition = null, context = {}) {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [intent, setIntent] = useState(null);
  const [nextSlot, setNextSlot] = useState(null);
  const [source, setSource] = useState(null);
  const [latency, setLatency] = useState(0);

  const debouncedQuery = useDebounce(query, 400);

  const fetchSuggestions = useCallback(async () => {
    if (!debouncedQuery.trim()) {
      setSuggestions([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await getSuggestions(
        debouncedQuery,
        cursorPosition,
        context
      );

      setSuggestions(response.suggestions || []);
      setIntent(response.intent || null);
      setNextSlot(response.next_slot || null);
      setSource(response.source || null);
      setLatency(response.latency_ms || 0);
    } catch (err) {
      setError(err.message || "Failed to fetch suggestions");
      setSuggestions([]);
    } finally {
      setLoading(false);
    }
  }, [debouncedQuery, cursorPosition, context]);

  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  return {
    suggestions,
    loading,
    error,
    intent,
    nextSlot,
    source,
    latency,
  };
}
