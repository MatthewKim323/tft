import { useState, useEffect, useRef } from 'react';
import DecisionCard from './DecisionCard';
import './DecisionLog.css';

const WS_URL = 'ws://127.0.0.1:8000/ws/decisions';

/**
 * Decision Log Panel - Shows AI Coach recommendations in real-time
 */
export default function DecisionLog({ maxDecisions = 20, onNewDecision = null }) {
  const [decisions, setDecisions] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [lastHeartbeat, setLastHeartbeat] = useState(null);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  
  useEffect(() => {
    let mounted = true;
    
    const connect = () => {
      if (!mounted) return;
      
      try {
        wsRef.current = new WebSocket(WS_URL);
        
        wsRef.current.onopen = () => {
          console.log('Decision WebSocket connected');
          setIsConnected(true);
          setError(null);
        };
        
        wsRef.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            if (data.type === 'decision') {
              setDecisions(prev => {
                const newDecisions = [data, ...prev];
                return newDecisions.slice(0, maxDecisions);
              });
              setLastHeartbeat(new Date());
              
              // Notify parent to add to history
              if (onNewDecision) {
                onNewDecision(data);
              }
            } else if (data.type === 'heartbeat') {
              setLastHeartbeat(new Date());
            } else if (data.type === 'error') {
              setError(data.error);
            }
          } catch (e) {
            console.error('Failed to parse decision:', e);
          }
        };
        
        wsRef.current.onclose = () => {
          console.log('Decision WebSocket closed');
          setIsConnected(false);
          
          // Reconnect after 3 seconds
          if (mounted) {
            reconnectTimeoutRef.current = setTimeout(connect, 3000);
          }
        };
        
        wsRef.current.onerror = (e) => {
          console.error('Decision WebSocket error:', e);
          setError('Connection failed');
        };
        
      } catch (e) {
        console.error('Failed to create WebSocket:', e);
        setError('Failed to connect');
        
        // Retry
        if (mounted) {
          reconnectTimeoutRef.current = setTimeout(connect, 3000);
        }
      }
    };
    
    connect();
    
    return () => {
      mounted = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [maxDecisions]);
  
  const clearHistory = () => {
    setDecisions([]);
  };
  
  return (
    <div className="decision-log">
      <div className="decision-log-header">
        <div className="header-left">
          <div className="header-indicator"></div>
          <h2 className="section-title">coach</h2>
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>
        {decisions.length > 0 && (
          <button className="clear-btn" onClick={clearHistory}>
            clear
          </button>
        )}
      </div>
      
      {error && (
        <div className="decision-error">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}
      
      <div className="decision-list">
        {decisions.length === 0 ? (
          <div className="decision-empty">
            {isConnected ? (
              <>
                <div className="empty-icon"></div>
                <p>waiting for game state...</p>
                <p className="hint">press <kbd>\</kbd> to capture</p>
              </>
            ) : (
              <>
                <div className="empty-icon offline"></div>
                <p>not connected</p>
                <p className="hint"><code>python run_state_api.py</code></p>
              </>
            )}
          </div>
        ) : (
          decisions.map((decision, index) => (
            <DecisionCard 
              key={`${decision.timestamp}-${index}`}
              decision={decision}
              isLatest={index === 0}
            />
          ))
        )}
      </div>
      
      {lastHeartbeat && (
        <div className="decision-footer">
          Last update: {lastHeartbeat.toLocaleTimeString()}
        </div>
      )}
    </div>
  );
}
