import { useEffect, useState } from 'react';
import NoiseOrb from './NoiseOrb';
import './OrbLoader.css';

export default function OrbLoader({ onComplete, minDuration = 3000 }) {
  const [progress, setProgress] = useState(0);
  const [isExiting, setIsExiting] = useState(false);
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const startTime = Date.now();

    const interval = setInterval(() => {
      const elapsedTime = Date.now() - startTime;
      const newProgress = Math.min(100, (elapsedTime / minDuration) * 100);
      setProgress(newProgress);

      if (newProgress === 100) {
        clearInterval(interval);
        // Start fade out
        setIsExiting(true);
        // Complete after fade animation
        setTimeout(() => {
          setIsVisible(false);
          if (onComplete) onComplete();
        }, 800); // Match fade duration
      }
    }, 50);

    return () => clearInterval(interval);
  }, [onComplete, minDuration]);

  if (!isVisible) return null;

  return (
    <div className={`orb-loader ${isExiting ? 'exiting' : ''}`}>
      <div className="orb-container">
        {/* Glow behind orb */}
        <div className="orb-glow" />
        <NoiseOrb size={256} />
      </div>

      {/* Progress bar */}
      <div className="progress-bar-container">
        <div className="progress-bar-track">
          <div 
            className="progress-bar-fill"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  );
}
