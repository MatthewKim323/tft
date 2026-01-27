import { useState, useEffect, useRef } from 'react';
import ShaderBackground from '../components/ShaderBackground';
import FluidCursor from '../components/FluidCursor';
import './Dashboard.css';

export default function Dashboard() {
  const [selectedMetric, setSelectedMetric] = useState('winrate');
  const [isVisible, setIsVisible] = useState(false);
  const [mousePos, setMousePos] = useState({ x: 50, y: 50 });
  const [liveStats, setLiveStats] = useState({
    winRate: 67.3,
    avgPlacement: 3.2,
    games: 142,
    accuracy: 84.7
  });
  const canvasRef = useRef(null);

  useEffect(() => {
    setIsVisible(true);
    
    const handleMouseMove = (e) => {
      setMousePos({
        x: (e.clientX / window.innerWidth) * 100,
        y: (e.clientY / window.innerHeight) * 100
      });
    };
    
    window.addEventListener('mousemove', handleMouseMove);

    // Simulate live data updates
    const interval = setInterval(() => {
      setLiveStats(prev => ({
        winRate: Math.min(100, Math.max(0, prev.winRate + (Math.random() - 0.5) * 0.5)),
        avgPlacement: Math.min(8, Math.max(1, prev.avgPlacement + (Math.random() - 0.5) * 0.1)),
        games: prev.games + (Math.random() > 0.9 ? 1 : 0),
        accuracy: Math.min(100, Math.max(0, prev.accuracy + (Math.random() - 0.5) * 0.3))
      }));
    }, 2000);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      clearInterval(interval);
    };
  }, []);

  // Generate chart data points
  const chartData = Array.from({ length: 40 }, (_, i) => ({
    height: Math.sin(i * 0.3) * 20 + Math.random() * 30 + 40,
    delay: i * 0.03
  }));

  return (
    <>
      {/* SVG gradient definitions */}
      <svg width="0" height="0" style={{ position: 'absolute' }}>
        <defs>
          <linearGradient id="progressGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#B794F6" />
            <stop offset="100%" stopColor="#805AD5" />
          </linearGradient>
        </defs>
      </svg>
      
      <ShaderBackground />
      <FluidCursor />
      <div className="shader-overlay"></div>
      <div 
        className={`dashboard-page ${isVisible ? 'visible' : ''}`}
        style={{ '--mouse-x': `${mousePos.x}%`, '--mouse-y': `${mousePos.y}%` }}
      >
        {/* Animated background grid */}
        <div className="grid-overlay"></div>
        
        <div className="dashboard-container">
          <header className="dashboard-header">
            <div className="header-content">
              <div className="header-text">
                <h1 className="dashboard-title page-title-enter">
                  <span className="title-glow">analytics</span> dashboard
                </h1>
                <div className="live-indicator">
                  <span className="live-dot"></span>
                  <span className="live-text">LIVE</span>
                </div>
              </div>
            </div>
          </header>

          <div className="bento-grid">
            {/* Hero stat card */}
            <div className="glass-card hero-card page-content-enter">
              <div className="card-glow"></div>
              <div className="glass-noise"></div>
              <div className="glass-content">
                <div className="hero-stat">
                  <div className="stat-ring">
                    <svg viewBox="0 0 120 120">
                      <circle className="ring-bg" cx="60" cy="60" r="54" />
                      <circle 
                        className="ring-progress" 
                        cx="60" 
                        cy="60" 
                        r="54"
                        style={{ '--progress': liveStats.winRate / 100 }}
                      />
                    </svg>
                    <div className="ring-value">
                      <span className="value-num">{liveStats.winRate.toFixed(1)}</span>
                      <span className="value-unit">%</span>
                    </div>
                  </div>
                  <div className="stat-label">Win Rate</div>
                  <div className="stat-trend up">
                    <span className="trend-icon">↑</span>
                    <span>12.4% this week</span>
                  </div>
                </div>
                
                {/* Mini sparkline */}
                <div className="mini-chart">
                  {Array.from({ length: 12 }).map((_, i) => (
                    <div 
                      key={i} 
                      className="mini-bar"
                      style={{ 
                        '--height': `${Math.random() * 50 + 50}%`,
                        '--delay': `${i * 0.05}s`
                      }}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* Metric cards */}
            <div className="glass-card metric-card page-content-enter" style={{ '--delay': '0.05s' }}>
              <div className="card-glow"></div>
              <div className="glass-noise"></div>
              <div className="glass-content">
                <div className="metric-icon-wrapper">
                  <div className="metric-icon">🎯</div>
                </div>
                <div className="metric-value-wrapper">
                  <span className="metric-value">{liveStats.avgPlacement.toFixed(1)}</span>
                </div>
                <div className="metric-label">Avg Placement</div>
                <div className="metric-trend up">↑ 0.8</div>
              </div>
            </div>

            <div className="glass-card metric-card page-content-enter" style={{ '--delay': '0.1s' }}>
              <div className="card-glow"></div>
              <div className="glass-noise"></div>
              <div className="glass-content">
                <div className="metric-icon-wrapper">
                  <div className="metric-icon">🎮</div>
                </div>
                <div className="metric-value-wrapper">
                  <span className="metric-value">{liveStats.games}</span>
                </div>
                <div className="metric-label">Games</div>
                <div className="metric-trend">+23 this week</div>
              </div>
            </div>

            <div className="glass-card metric-card page-content-enter" style={{ '--delay': '0.15s' }}>
              <div className="card-glow"></div>
              <div className="glass-noise"></div>
              <div className="glass-content">
                <div className="metric-icon-wrapper">
                  <div className="metric-icon">🧠</div>
                </div>
                <div className="metric-value-wrapper">
                  <span className="metric-value">{liveStats.accuracy.toFixed(1)}%</span>
                </div>
                <div className="metric-label">Decision Accuracy</div>
                <div className="metric-trend up">↑ 5.2%</div>
              </div>
            </div>

            {/* Chart section */}
            <div className="glass-card chart-card page-content-enter" style={{ '--delay': '0.2s' }}>
              <div className="card-glow"></div>
              <div className="glass-noise"></div>
              <div className="glass-content">
                <div className="chart-header">
                  <h2 className="chart-title">Performance Over Time</h2>
                  <div className="chart-controls">
                    {['winrate', 'placement', 'accuracy'].map(metric => (
                      <button 
                        key={metric}
                        className={`chart-btn ${selectedMetric === metric ? 'active' : ''}`}
                        onClick={() => setSelectedMetric(metric)}
                      >
                        {metric === 'winrate' ? 'Win Rate' : metric === 'placement' ? 'Placement' : 'Accuracy'}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="chart-visualization">
                  <div className="chart-y-axis">
                    <span>100%</span>
                    <span>75%</span>
                    <span>50%</span>
                    <span>25%</span>
                    <span>0%</span>
                  </div>
                  <div className="chart-grid">
                    {chartData.map((data, i) => (
                      <div 
                        key={i} 
                        className="chart-bar"
                        style={{ 
                          '--height': `${data.height}%`,
                          '--delay': `${data.delay}s`
                        }}
                      >
                        <div className="bar-glow"></div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Recent games */}
            <div className="glass-card games-card page-content-enter" style={{ '--delay': '0.25s' }}>
              <div className="card-glow"></div>
              <div className="glass-noise"></div>
              <div className="glass-content">
                <h2 className="section-title">Recent Games</h2>
                <div className="games-list">
                  {[
                    { rank: 2, time: '2h ago', comp: '6 Shadow Isles • 4 Vanguard', result: 'win' },
                    { rank: 1, time: '5h ago', comp: '8 Sorcerer • 3 Mage', result: 'win' },
                    { rank: 4, time: '1d ago', comp: '4 Assassin • 4 Ninja', result: 'loss' },
                    { rank: 3, time: '1d ago', comp: '6 Bruiser • 2 Yordle', result: 'win' }
                  ].map((game, i) => (
                    <div 
                      key={i} 
                      className="game-item"
                      style={{ '--delay': `${0.3 + i * 0.05}s` }}
                    >
                      <div className={`game-rank rank-${game.rank}`}>#{game.rank}</div>
                      <div className="game-details">
                        <div className="game-date">{game.time}</div>
                        <div className="game-comp">{game.comp}</div>
                      </div>
                      <div className={`game-result ${game.result}`}>
                        {game.result === 'win' ? '✓' : '✗'}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
