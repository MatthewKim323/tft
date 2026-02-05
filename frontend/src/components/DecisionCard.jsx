import { useState } from 'react';
import './DecisionCard.css';

/**
 * Single decision card component
 * Shows one AI Coach recommendation with expandable reasoning
 */
export default function DecisionCard({ decision, isLatest = false }) {
  const [expanded, setExpanded] = useState(isLatest);
  
  if (!decision) return null;
  
  const { timestamp, game_state_summary, analysis, decision: dec, alternative_actions } = decision;
  
  // Format timestamp
  const formatTime = (ts) => {
    try {
      const date = new Date(ts);
      return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
      });
    } catch {
      return ts;
    }
  };
  
  // Priority colors
  const priorityColors = {
    critical: '#ff4757',
    high: '#ffa502',
    medium: '#7bed9f',
    low: '#70a1ff'
  };
  
  const priorityColor = priorityColors[dec?.priority] || '#70a1ff';
  
  // Action indicators (CSS-based, no emojis)
  const actionClasses = {
    BUY: 'action-buy',
    SELL: 'action-sell',
    LEVEL: 'action-level',
    REROLL: 'action-reroll',
    POSITION: 'action-position',
    EQUIP: 'action-equip',
    HOLD: 'action-hold'
  };
  
  const actionClass = actionClasses[dec?.action] || 'action-default';
  
  return (
    <div 
      className={`decision-card ${isLatest ? 'latest' : ''} ${expanded ? 'expanded' : ''}`}
      onClick={() => setExpanded(!expanded)}
      style={{ '--priority-color': priorityColor }}
    >
      <div className="decision-header">
        <span className="decision-time">{formatTime(timestamp)}</span>
        <span 
          className="decision-priority"
          style={{ backgroundColor: priorityColor }}
        >
          {dec?.priority?.toUpperCase()}
        </span>
      </div>
      
      <div className="decision-main">
        <div className={`decision-indicator ${actionClass}`}></div>
        <div className="decision-action">
          <span className="action-type">{dec?.action?.toLowerCase()}</span>
          <span className="action-target">{dec?.target}</span>
        </div>
      </div>
      
      <div className="decision-reasoning">
        {dec?.reasoning}
      </div>
      
      {expanded && (
        <div className="decision-details">
          <div className="detail-section">
            <h4>game state</h4>
            <div className="state-grid">
              <div className="state-item">
                <span className="label">stage</span>
                <span className="value">{game_state_summary?.stage}</span>
              </div>
              <div className="state-item">
                <span className="label">hp</span>
                <span className="value">{game_state_summary?.health}</span>
              </div>
              <div className="state-item">
                <span className="label">gold</span>
                <span className="value gold">{game_state_summary?.gold}</span>
              </div>
              <div className="state-item">
                <span className="label">level</span>
                <span className="value">{game_state_summary?.level}</span>
              </div>
            </div>
          </div>
          
          <div className="detail-section">
            <h4>analysis</h4>
            <div className="analysis-tags">
              <span className={`tag economy-${analysis?.economy_status}`}>
                <span className="tag-dot"></span>
                {analysis?.economy_status}
              </span>
              <span className={`tag board-${analysis?.board_strength}`}>
                <span className="tag-dot"></span>
                {analysis?.board_strength}
              </span>
              <span className="tag position">
                <span className="tag-dot"></span>
                {analysis?.position_estimate}
              </span>
            </div>
          </div>
          
          {alternative_actions?.length > 0 && (
            <div className="detail-section">
              <h4>alternatives</h4>
              <div className="alternatives-list">
                {alternative_actions.map((alt, i) => (
                  <div key={i} className="alternative-item">
                    <span className="alt-action">{alt.action?.toLowerCase()}</span>
                    <span className="alt-reason">{alt.reasoning}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {game_state_summary?.active_traits?.length > 0 && (
            <div className="detail-section">
              <h4>active traits</h4>
              <div className="traits-list">
                {game_state_summary.active_traits.map((trait, i) => (
                  <span key={i} className="trait-tag">{trait}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      
      <div className="expand-hint">
        {expanded ? 'collapse' : 'expand'}
      </div>
    </div>
  );
}
