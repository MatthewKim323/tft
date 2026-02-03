import { useState, useEffect, useRef } from 'react';
import PixelBlast from '../components/PixelBlast';
import { useGameStateChanges, useGameStateWS } from '../hooks/useGameState';
import './Logs.css';

export default function Logs() {
  const [isVisible, setIsVisible] = useState(false);
  const [expandedLog, setExpandedLog] = useState(null);
  const [activeFilter, setActiveFilter] = useState('all');
  const [typingText, setTypingText] = useState('');
  const terminalRef = useRef(null);
  
  // Connect to game state API for live changes
  const { changes: liveChanges, isConnected } = useGameStateChanges();
  const { state: gameState } = useGameStateWS(2, 'fast');

  const logEntries = [
    {
      id: 1,
      timestamp: '2024-01-27 14:32:05',
      type: 'decision',
      title: 'Pivot Decision',
      status: 'executed',
      summary: 'Pivoted from Yordle → Shadow Isles at Stage 3-2',
      details: {
        trigger: 'Low health threshold (42 HP) detected',
        analysis: 'Current board strength: 2.4/10, Opponent average: 6.8/10',
        options: [
          { action: 'Stay Yordle', confidence: 23, reason: 'Missing 3 key units' },
          { action: 'Pivot Shadow Isles', confidence: 78, reason: '4 units available, strong synergy' },
          { action: 'Go Fast 8', confidence: 45, reason: 'Economy sufficient but risky' }
        ],
        chosen: 'Pivot Shadow Isles',
        outcome: 'Win streak initiated, +28 HP over 4 rounds'
      }
    },
    {
      id: 2,
      timestamp: '2024-01-27 14:28:12',
      type: 'analysis',
      title: 'Board State Analysis',
      status: 'complete',
      summary: 'Detected 3 players contesting Yordle comp',
      details: {
        boardState: {
          units: ['Lulu★★', 'Veigar★', 'Poppy★★', 'Teemo★'],
          items: ['Rabadon', 'Jeweled Gauntlet', 'Hand of Justice'],
          gold: 34,
          level: 6
        },
        threats: [
          { player: 'Player 3', comp: 'Yordle', overlap: '4 units' },
          { player: 'Player 5', comp: 'Yordle', overlap: '3 units' },
          { player: 'Player 7', comp: 'Mage Yordle', overlap: '2 units' }
        ],
        recommendation: 'Consider pivot or hyper-roll strategy'
      }
    },
    {
      id: 3,
      timestamp: '2024-01-27 14:25:33',
      type: 'item',
      title: 'Item Recommendation',
      status: 'pending',
      summary: 'Suggested BiS items for carry units',
      details: {
        carousel: 'Rod available',
        currentItems: ['BF Sword', 'Chain Vest', 'Tear'],
        recommendations: [
          { item: 'Hextech Gunblade', priority: 'HIGH', reason: 'Core AP carry item' },
          { item: 'Bramble Vest', priority: 'MED', reason: 'Tank frontline' }
        ]
      }
    },
    {
      id: 4,
      timestamp: '2024-01-27 14:22:01',
      type: 'economy',
      title: 'Economy Optimization',
      status: 'executed',
      summary: 'Level up at 4-1 for power spike',
      details: {
        currentGold: 50,
        interest: 5,
        action: 'Level to 7, spend 28 gold rolling',
        expectedValue: 'High chance of hitting key 4-cost units'
      }
    },
    {
      id: 5,
      timestamp: '2024-01-27 14:18:45',
      type: 'decision',
      title: 'Positioning Update',
      status: 'executed',
      summary: 'Repositioned carry to avoid Zephyr',
      details: {
        threat: 'Player 2 has Zephyr, targeting corner',
        action: 'Moved Veigar from corner to second row',
        counterplay: 'Placed bait unit in corner position'
      }
    }
  ];

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
            {/* Filter sidebar */}
            <aside className="filter-sidebar glass-card page-content-enter">
              <div className="card-glow"></div>
              <div className="glass-noise"></div>
              <div className="sidebar-content">
                <h3 className="sidebar-title">Filters</h3>
                <div className="filter-list">
                  {[
                    { id: 'all', label: 'All Logs', count: logEntries.length },
                    { id: 'decision', label: 'Decisions', count: logEntries.filter(l => l.type === 'decision').length },
                    { id: 'analysis', label: 'Analysis', count: logEntries.filter(l => l.type === 'analysis').length },
                    { id: 'item', label: 'Items', count: logEntries.filter(l => l.type === 'item').length },
                    { id: 'economy', label: 'Economy', count: logEntries.filter(l => l.type === 'economy').length }
                  ].map(filter => (
                    <button
                      key={filter.id}
                      className={`filter-btn ${activeFilter === filter.id ? 'active' : ''}`}
                      onClick={() => setActiveFilter(filter.id)}
                    >
                      <span className="filter-label">{filter.label}</span>
                      <span className="filter-count">{filter.count}</span>
                    </button>
                  ))}
                </div>

                <div className="sidebar-stats">
                  <div className="stat-item">
                    <span className="stat-value">847</span>
                    <span className="stat-label">Total Decisions</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-value">94.2%</span>
                    <span className="stat-label">Success Rate</span>
                  </div>
                </div>
              </div>
            </aside>

            {/* Log entries */}
            <main className="logs-main">
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
            </main>
          </div>
        </div>
      </div>
    </>
  );
}
