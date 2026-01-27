import { useState, useEffect } from 'react';
import ShaderBackground from '../components/ShaderBackground';
import './Logs.css';

export default function Logs() {
  const [selectedLog, setSelectedLog] = useState(null);
  const [filter, setFilter] = useState('all');
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const sampleLogs = [
    {
      id: 1,
      timestamp: '2024-01-15 14:32:18',
      type: 'state_extraction',
      message: 'Game state extracted successfully',
      details: {
        stage: 'Stage 3-2',
        gold: 45,
        health: 78,
        level: 5,
        board: '6 units detected',
        bench: '3 units detected',
        shop: '5 units available'
      }
    },
    {
      id: 2,
      timestamp: '2024-01-15 14:32:15',
      type: 'decision',
      message: 'Decision: Purchase unit from shop',
      details: {
        reasoning: 'Optimal unit available for current composition',
        unit: 'Jinx',
        cost: 3,
        synergy: 'Adds 2 Sniper trait',
        expectedValue: 0.12
      }
    },
    {
      id: 3,
      timestamp: '2024-01-15 14:32:10',
      type: 'analysis',
      message: 'Analyzing board state and opponent compositions',
      details: {
        opponentsAnalyzed: 7,
        threatLevel: 'Medium',
        recommendedAction: 'Econ to 50 gold',
        confidence: 0.87
      }
    },
    {
      id: 4,
      timestamp: '2024-01-15 14:32:05',
      type: 'state_extraction',
      message: 'Game state extracted successfully',
      details: {
        stage: 'Stage 3-2',
        gold: 42,
        health: 78,
        level: 5,
        board: '6 units detected',
        bench: '2 units detected',
        shop: '5 units available'
      }
    }
  ];

  const filteredLogs = filter === 'all' 
    ? sampleLogs 
    : sampleLogs.filter(log => log.type === filter);

  return (
    <>
      <ShaderBackground />
      <div className="shader-overlay"></div>
      <div className={`logs-page ${isVisible ? 'visible' : ''}`}>
      <div className="logs-container">
        <header className="logs-header">
          <h1 className="logs-title page-title-enter">Decision Logs</h1>
          <p className="logs-subtitle page-subtitle-enter">Transparent view into the bot's decision-making process</p>
        </header>

        <div className="logs-content">
          <div className="logs-filters page-content-enter">
            <button 
              className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
              onClick={() => setFilter('all')}
            >
              All
            </button>
            <button 
              className={`filter-btn ${filter === 'state_extraction' ? 'active' : ''}`}
              onClick={() => setFilter('state_extraction')}
            >
              State Extraction
            </button>
            <button 
              className={`filter-btn ${filter === 'analysis' ? 'active' : ''}`}
              onClick={() => setFilter('analysis')}
            >
              Analysis
            </button>
            <button 
              className={`filter-btn ${filter === 'decision' ? 'active' : ''}`}
              onClick={() => setFilter('decision')}
            >
              Decisions
            </button>
          </div>

          <div className="logs-list page-content-enter" style={{ '--delay': '0.1s' }}>
            {filteredLogs.map((log) => (
              <div 
                key={log.id}
                className={`log-item ${selectedLog === log.id ? 'expanded' : ''}`}
                onClick={() => setSelectedLog(selectedLog === log.id ? null : log.id)}
              >
                <div className="log-header">
                  <div className="log-type-badge" data-type={log.type}>
                    {log.type.replace('_', ' ')}
                  </div>
                  <div className="log-timestamp">{log.timestamp}</div>
                </div>
                <div className="log-message">{log.message}</div>
                {selectedLog === log.id && (
                  <div className="log-details">
                    {Object.entries(log.details).map(([key, value]) => (
                      <div key={key} className="detail-row">
                        <span className="detail-key">{key.replace(/_/g, ' ')}:</span>
                        <span className="detail-value">{typeof value === 'object' ? JSON.stringify(value) : value}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
    </>
  );
}
