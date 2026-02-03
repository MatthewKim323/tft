/**
 * React hook for connecting to TFT State Extraction API
 * Provides real-time game state via WebSocket
 */

import { useState, useEffect, useRef, useCallback } from 'react';

const API_BASE = 'http://127.0.0.1:8000';
const WS_BASE = 'ws://127.0.0.1:8000';

/**
 * Hook for fetching game state via REST API
 */
export function useGameStateREST(pollInterval = 1000) {
  const [state, setState] = useState(null);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    let mounted = true;
    let timeoutId;

    const fetchState = async () => {
      try {
        const response = await fetch(`${API_BASE}/state?mode=fast`);
        if (!response.ok) throw new Error('API not available');
        
        const data = await response.json();
        if (mounted) {
          setState(data);
          setIsConnected(true);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setIsConnected(false);
          setError(err.message);
        }
      }
      
      if (mounted) {
        timeoutId = setTimeout(fetchState, pollInterval);
      }
    };

    fetchState();

    return () => {
      mounted = false;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [pollInterval]);

  return { state, error, isConnected };
}

/**
 * Hook for real-time game state via WebSocket
 */
export function useGameStateWS(fps = 5, mode = 'fast') {
  const [state, setState] = useState(null);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(`${WS_BASE}/ws/state?fps=${fps}&mode=${mode}`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.error) {
            setError(data.error);
          } else {
            setState(data);
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
        setIsConnected(false);
      };

      ws.onclose = () => {
        console.log('WebSocket closed, reconnecting...');
        setIsConnected(false);
        // Attempt to reconnect after 2 seconds
        reconnectTimeoutRef.current = setTimeout(connect, 2000);
      };

      wsRef.current = ws;
    } catch (err) {
      setError(err.message);
      setIsConnected(false);
      // Attempt to reconnect after 2 seconds
      reconnectTimeoutRef.current = setTimeout(connect, 2000);
    }
  }, [fps, mode]);

  useEffect(() => {
    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  return { state, error, isConnected };
}

/**
 * Hook for tracking game state changes
 */
export function useGameStateChanges() {
  const [changes, setChanges] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    const connect = () => {
      try {
        const ws = new WebSocket(`${WS_BASE}/ws/changes`);
        
        ws.onopen = () => {
          setIsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'change') {
              setChanges(prev => [data, ...prev].slice(0, 100)); // Keep last 100 changes
            }
          } catch (e) {
            console.error('Failed to parse change event:', e);
          }
        };

        ws.onclose = () => {
          setIsConnected(false);
          setTimeout(connect, 2000);
        };

        wsRef.current = ws;
      } catch (err) {
        setTimeout(connect, 2000);
      }
    };

    connect();

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const clearChanges = useCallback(() => setChanges([]), []);

  return { changes, isConnected, clearChanges };
}

/**
 * Check if the API server is running
 */
export async function checkAPIHealth() {
  try {
    const response = await fetch(`${API_BASE}/`);
    if (response.ok) {
      const data = await response.json();
      return { online: true, ...data };
    }
  } catch (err) {
    // API not available
  }
  return { online: false };
}

/**
 * Fetch single game state snapshot
 */
export async function fetchGameState(mode = 'fast') {
  const response = await fetch(`${API_BASE}/state?mode=${mode}`);
  if (!response.ok) throw new Error('Failed to fetch game state');
  return response.json();
}

/**
 * Get ROI region definitions
 */
export async function fetchRegions() {
  const response = await fetch(`${API_BASE}/regions`);
  if (!response.ok) throw new Error('Failed to fetch regions');
  return response.json();
}

export default useGameStateWS;
