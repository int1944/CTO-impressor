import { useState, useEffect, useCallback, useRef } from "react";
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
  
  // Track the last query we fetched to prevent duplicate requests
  const lastFetchedQuery = useRef(null);
  // Track in-flight request to cancel if needed
  const abortControllerRef = useRef(null);

  const fetchSuggestions = useCallback(async () => {
    // Early return if query is empty
    if (!debouncedQuery.trim()) {
      // Cancel any in-flight request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
      
      // Only reset state if we had a previous query (avoid unnecessary state updates)
      if (lastFetchedQuery.current !== null) {
        setSuggestions([]);
        setIntent(null);
        setNextSlot(null);
        setSource(null);
        setLatency(0);
        setLoading(false);
        lastFetchedQuery.current = null;
      }
      return;
    }

    // Only fetch suggestions if user has entered at least one word AND a space
    // This prevents unnecessary API calls and cache hits until user completes first word
    const trimmedQuery = debouncedQuery.trim();
    const words = trimmedQuery.split(/\s+/);
    
    // Check if user has typed at least one word followed by a space
    // This is true if: query has multiple words OR query ends with a space (indicating completion of first word)
    const hasCompletedFirstWord = words.length > 1 || debouncedQuery.endsWith(' ');
    
    if (!hasCompletedFirstWord) {
      // Don't fetch suggestions yet - user is still typing their first word
      // Cancel any in-flight request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
      
      // Reset state to avoid showing stale suggestions
      if (lastFetchedQuery.current !== null) {
        setSuggestions([]);
        setIntent(null);
        setNextSlot(null);
        setSource(null);
        setLatency(0);
        setLoading(false);
        lastFetchedQuery.current = null;
      }
      return;
    }

    // Skip if this is the same query we just fetched
    if (lastFetchedQuery.current === debouncedQuery) {
      return;
    }

    // Cancel previous request if still in flight
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller for this request
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    setLoading(true);
    setError(null);
    lastFetchedQuery.current = debouncedQuery;

    try {
      const response = await getSuggestions(
        debouncedQuery,
        cursorPosition,
        context,
        abortController.signal
      );

      // Check if request was aborted
      if (abortController.signal.aborted) {
        return;
      }

      setSuggestions(response.suggestions || []);
      setIntent(response.intent || null);
      setNextSlot(response.next_slot || null);
      setSource(response.source || null);
      setLatency(response.latency_ms || 0);
      
      // Debug logging for holiday queries
      if (process.env.NODE_ENV === 'development') {
        if (response.intent === 'holiday' || debouncedQuery.toLowerCase().includes('holiday') || debouncedQuery.toLowerCase().includes('vacation')) {
          console.log('🎉 Holiday Query Detected:', {
            query: debouncedQuery,
            intent: response.intent,
            nextSlot: response.next_slot,
            source: response.source,
            suggestionsCount: response.suggestions?.length || 0,
            suggestions: response.suggestions
          });
        }
      }
    } catch (err) {
      // Ignore abort errors
      if (err.name === 'AbortError' || err.name === 'CanceledError') {
        return;
      }
      
      // Only update state if request wasn't aborted
      if (!abortController.signal.aborted) {
        setError(err.message || "Failed to fetch suggestions");
        setSuggestions([]);
      }
    } finally {
      // Only update loading state if request wasn't aborted
      if (!abortController.signal.aborted) {
        setLoading(false);
      }
      abortControllerRef.current = null;
    }
  }, [debouncedQuery, cursorPosition, context]);

  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

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
