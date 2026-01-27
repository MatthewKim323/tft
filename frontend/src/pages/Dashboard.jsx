import { useState, useEffect } from 'react';
import ShaderBackground from '../components/ShaderBackground';
import './Dashboard.css';

export default function Dashboard() {
  const [selectedMetric, setSelectedMetric] = useState('winrate');
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  return (
    <>
      <ShaderBackground />
      <div className="shader-overlay"></div>
      <div className={`dashboard-page ${isVisible ? 'visible' : ''}`}>
      <div className="dashboard-container">
        <header className="dashboard-header">
          <h1 className="dashboard-title page-title-enter">Analytics Dashboard</h1>
          <p className="dashboard-subtitle page-subtitle-enter">Track bot performance and decision quality over time</p>
        </header>

        <div className="dashboard-content">
          <div className="metrics-grid page-content-enter">
            <div className="metric-card">
              <div className="metric-label">Win Rate</div>
              <div className="metric-value">67.3%</div>
              <div className="metric-trend up">↑ 12.4% this week</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Avg Placement</div>
              <div className="metric-value">3.2</div>
              <div className="metric-trend up">↑ 0.8 this week</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Games Played</div>
              <div className="metric-value">142</div>
              <div className="metric-trend">+23 this week</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Decision Accuracy</div>
              <div className="metric-value">84.7%</div>
              <div className="metric-trend up">↑ 5.2% this week</div>
            </div>
          </div>

          <div className="chart-section page-content-enter" style={{ '--delay': '0.1s' }}>
            <div className="chart-header">
              <h2 className="chart-title">Performance Over Time</h2>
              <div className="chart-controls">
                <button 
                  className={`chart-btn ${selectedMetric === 'winrate' ? 'active' : ''}`}
                  onClick={() => setSelectedMetric('winrate')}
                >
                  Win Rate
                </button>
                <button 
                  className={`chart-btn ${selectedMetric === 'placement' ? 'active' : ''}`}
                  onClick={() => setSelectedMetric('placement')}
                >
                  Avg Placement
                </button>
                <button 
                  className={`chart-btn ${selectedMetric === 'accuracy' ? 'active' : ''}`}
                  onClick={() => setSelectedMetric('accuracy')}
                >
                  Decision Accuracy
                </button>
              </div>
            </div>
            <div className="chart-placeholder">
              <div className="chart-message">
                Chart visualization will be connected to Riot API data
              </div>
            </div>
          </div>

          <div className="recent-games page-content-enter" style={{ '--delay': '0.2s' }}>
            <h2 className="section-title">Recent Games</h2>
            <div className="games-list">
              <div className="game-item">
                <div className="game-rank">#2</div>
                <div className="game-details">
                  <div className="game-date">2 hours ago</div>
                  <div className="game-comp">6 Shadow Isles • 4 Vanguard</div>
                </div>
                <div className="game-result win">Win</div>
              </div>
              <div className="game-item">
                <div className="game-rank">#1</div>
                <div className="game-details">
                  <div className="game-date">5 hours ago</div>
                  <div className="game-comp">8 Sorcerer • 3 Mage</div>
                </div>
                <div className="game-result win">Win</div>
              </div>
              <div className="game-item">
                <div className="game-rank">#4</div>
                <div className="game-details">
                  <div className="game-date">1 day ago</div>
                  <div className="game-comp">4 Assassin • 4 Ninja</div>
                </div>
                <div className="game-result loss">Loss</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    </>
  );
}
