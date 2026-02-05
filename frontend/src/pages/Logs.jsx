import { useState, useEffect, useRef } from 'react';
import PixelBlast from '../components/PixelBlast';
import DecisionLog from '../components/DecisionLog';
import { useGameStateChanges, useGameStateWS } from '../hooks/useGameState';
import './Logs.css';

const STORAGE_KEY = 'tft_session_logs';

// Convert coach decision to log entry format
const decisionToLogEntry = (decision, index) => {
  const actionTypeMap = {
    'BUY': 'decision',
    'SELL': 'decision', 
    'LEVEL': 'economy',
    'REROLL': 'economy',
    'HOLD': 'economy',
    'POSITION': 'decision',
    'EQUIP': 'item'
  };
  
  return {
    id: `${decision.timestamp}-${index}`,
    timestamp: new Date(decision.timestamp).toLocaleString(),
    type: actionTypeMap[decision.decision?.action] || 'decision',
    title: `${decision.decision?.action || 'Decision'}: ${decision.decision?.target || ''}`,
    status: 'recommended',
    summary: decision.decision?.reasoning || '',
    details: {
      analysis: `Economy: ${decision.analysis?.economy_status} | Board: ${decision.analysis?.board_strength} | Position: ${decision.analysis?.position_estimate}`,
      boardState: {
        stage: decision.game_state_summary?.stage,
        health: decision.game_state_summary?.health,
        gold: decision.game_state_summary?.gold,
        level: decision.game_state_summary?.level
      },
      options: decision.alternative_actions?.map(alt => ({
        action: alt.action,
        confidence: 50,
        reason: alt.reasoning
      })) || []
    }
  };
};

export default function Logs() {
  const [isVisible, setIsVisible] = useState(false);
  const [expandedLog, setExpandedLog] = useState(null);
  const [activeFilter, setActiveFilter] = useState('all');
  const [typingText, setTypingText] = useState('');
  const [logEntries, setLogEntries] = useState([]);
  const terminalRef = useRef(null);
  
  // Connect to game state API for live changes
  const { changes: liveChanges, isConnected } = useGameStateChanges();
  const { state: gameState } = useGameStateWS(2, 'fast');

  // Load saved logs from localStorage on mount
  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        setLogEntries(parsed);
      }
    } catch (e) {
      console.error('Failed to load saved logs:', e);
    }
  }, []);

  // Save logs to localStorage when they change
  useEffect(() => {
    if (logEntries.length > 0) {
      try {
        // Keep only last 100 entries
        const toSave = logEntries.slice(0, 100);
        localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
      } catch (e) {
        console.error('Failed to save logs:', e);
      }
    }
  }, [logEntries]);

  // Function to add new decision to history
  const addDecisionToHistory = (decision) => {
    if (!decision || !decision.decision) return;
    
    const logEntry = decisionToLogEntry(decision, Date.now());
    setLogEntries(prev => {
      // Avoid duplicates (same timestamp + action)
      const isDuplicate = prev.some(entry => 
        entry.id === logEntry.id || 
        (entry.timestamp === logEntry.timestamp && entry.title === logEntry.title)
      );
      if (isDuplicate) return prev;
      return [logEntry, ...prev].slice(0, 100);
    });
  };

  // Clear all logs
  const clearLogs = () => {
    setLogEntries([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  useEffect(() => {
    setIsVisible(true);

    // Typing animation for terminal
    const text = '> analyzing decision patterns...\n> loading neural weights...\n> bot ready_';
    let i = 0;
    const typeInterval = setInterval(() => {
      if (i < text.length) {
        setTypingText(text.slice(0, i + 1));
        i++;
      } else {
        clearInterval(typeInterval);
      }
    }, 50);

    return () => {
      clearInterval(typeInterval);
    };
  }, []);

  const filteredLogs = activeFilter === 'all' 
    ? logEntries 
    : logEntries.filter(log => log.type === activeFilter);

  const getTypeColor = (type) => {
    switch(type) {
      case 'decision': return '#B794F6';
      case 'analysis': return '#63B3ED';
      case 'item': return '#F6AD55';
      case 'economy': return '#68D391';
      default: return '#A0AEC0';
    }
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'executed': return 'status-success';
      case 'pending': return 'status-pending';
      case 'complete': return 'status-info';
      default: return '';
    }
  };

  return (
    <>
      <PixelBlast
        variant="square"
        pixelSize={4}
        color="#B794F6"
        patternScale={2}
        patternDensity={1}
        enableRipples
        rippleSpeed={0.4}
        rippleThickness={0.12}
        rippleIntensityScale={1.5}
        speed={0.5}
        edgeFade={0.25}
        transparent
      />

      <div 
        className={`logs-page ${isVisible ? 'visible' : ''}`}
      >
        
        <div className="logs-container">
          <header className="logs-header">
            <div className="header-content">
              <div className="header-text">
                <h1 className="logs-title page-title-enter">
                  <span className="title-glow">decision</span> logs
                </h1>
                <div className="terminal-badge">
                  <span className="terminal-text">{typingText}</span>
                  <span className="cursor-blink">|</span>
                </div>
                <div className={`api-status ${isConnected ? 'connected' : ''}`}>
                  <span className="status-dot"></span>
                  <span className="status-text">{isConnected ? 'API Connected' : 'API Offline'}</span>
                </div>
              </div>
            </div>
          </header>

          <div className="logs-layout">
            {/* Coach - Live Recommendations */}
            <aside className="coach-sidebar glass-card page-content-enter">
              <div className="card-glow"></div>
              <div className="glass-noise"></div>
              <div className="sidebar-content coach-sidebar-content">
                <DecisionLog maxDecisions={30} onNewDecision={addDecisionToHistory} />
              </div>
            </aside>

            {/* Historical Log entries */}
            <main className="logs-main">
              <div className="logs-section-header">
                <div className="section-header-left">
                  <h2 className="section-title">session history</h2>
                  <span className="log-count">{logEntries.length} entries</span>
                </div>
                <div className="section-header-right">
                  {logEntries.length > 0 && (
                    <button className="clear-history-btn" onClick={clearLogs}>
                      clear all
                    </button>
                  )}
                </div>
              </div>
              <div className="logs-filter-row">
                <div className="filter-pills">
                  {[
                    { id: 'all', label: 'All' },
                    { id: 'decision', label: 'Decisions' },
                    { id: 'analysis', label: 'Analysis' },
                    { id: 'economy', label: 'Economy' }
                  ].map(filter => (
                    <button
                      key={filter.id}
                      className={`filter-pill ${activeFilter === filter.id ? 'active' : ''}`}
                      onClick={() => setActiveFilter(filter.id)}
                    >
                      {filter.label}
                    </button>
                  ))}
                </div>
              </div>
              
              {logEntries.length === 0 ? (
                <div className="logs-empty">
                  <div className="empty-state">
                    <div className="empty-icon"></div>
                    <p>no decisions yet</p>
                    <p className="hint">decisions will appear here as the coach analyzes your game</p>
                  </div>
                </div>
              ) : (
              <div className="logs-list">
                {filteredLogs.map((log, index) => (
                  <div 
                    key={log.id}
                    className={`log-entry glass-card ${expandedLog === log.id ? 'expanded' : ''}`}
                    style={{ '--delay': `${0.1 + index * 0.05}s` }}
                    onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}
                  >
                    <div className="card-glow"></div>
                    <div className="glass-noise"></div>
                    <div className="log-content">
                      <div className="log-header">
                        <div className="log-indicator" style={{ '--indicator-color': getTypeColor(log.type) }}></div>
                        <div className="log-meta">
                          <div className="log-title">{log.title}</div>
                          <div className="log-timestamp">
                            {log.timestamp}
                          </div>
                        </div>
                        <div className={`log-status ${getStatusColor(log.status)}`}>
                          {log.status}
                        </div>
                        <div className="expand-icon">{expandedLog === log.id ? '−' : '+'}</div>
                      </div>
                      
                      <div className="log-summary">{log.summary}</div>
                      
                      {expandedLog === log.id && (
                        <div className="log-details">
                          <div className="details-divider"></div>
                          
                          {log.details.trigger && (
                            <div className="detail-section">
                              <h4>Trigger</h4>
                              <p>{log.details.trigger}</p>
                            </div>
                          )}
                          
                          {log.details.analysis && (
                            <div className="detail-section">
                              <h4>Analysis</h4>
                              <p>{log.details.analysis}</p>
                            </div>
                          )}
                          
                          {log.details.options && (
                            <div className="detail-section">
                              <h4>Options Evaluated</h4>
                              <div className="options-list">
                                {log.details.options.map((opt, i) => (
                                  <div 
                                    key={i} 
                                    className={`option-item ${opt.action === log.details.chosen ? 'chosen' : ''}`}
                                  >
                                    <div className="option-header">
                                      <span className="option-action">{opt.action}</span>
                                      <div className="confidence-bar">
                                        <div 
                                          className="confidence-fill"
                                          style={{ '--width': `${opt.confidence}%` }}
                                        ></div>
                                        <span className="confidence-value">{opt.confidence}%</span>
                                      </div>
                                    </div>
                                    <p className="option-reason">{opt.reason}</p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {log.details.outcome && (
                            <div className="detail-section outcome">
                              <h4>Outcome</h4>
                              <p className="outcome-text">{log.details.outcome}</p>
                            </div>
                          )}

                          {log.details.boardState && (
                            <div className="detail-section">
                              <h4>Board State</h4>
                              <div className="board-grid">
                                <div className="board-item">
                                  <span className="board-label">Units</span>
                                  <span className="board-value">{log.details.boardState.units.join(', ')}</span>
                                </div>
                                <div className="board-item">
                                  <span className="board-label">Items</span>
                                  <span className="board-value">{log.details.boardState.items.join(', ')}</span>
                                </div>
                                <div className="board-item">
                                  <span className="board-label">Gold</span>
                                  <span className="board-value">{log.details.boardState.gold}</span>
                                </div>
                                <div className="board-item">
                                  <span className="board-label">Level</span>
                                  <span className="board-value">{log.details.boardState.level}</span>
                                </div>
                              </div>
                            </div>
                          )}

                          {log.details.threats && (
                            <div className="detail-section">
                              <h4>Threats Detected</h4>
                              <div className="threats-list">
                                {log.details.threats.map((threat, i) => (
                                  <div key={i} className="threat-item">
                                    <span className="threat-player">{threat.player}</span>
                                    <span className="threat-comp">{threat.comp}</span>
                                    <span className="threat-overlap">{threat.overlap}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              )}
            </main>
          </div>
        </div>
      </div>
    </>
  );
}
