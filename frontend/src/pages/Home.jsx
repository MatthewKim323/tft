import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import ShaderBackground from '../components/ShaderBackground';
import OrbLoader from '../components/OrbLoader';
import '../App.css';

export default function Home({ isInitialLoad = false, onLoadComplete }) {
  const [isLoading, setIsLoading] = useState(isInitialLoad);
  const [showContent, setShowContent] = useState(!isInitialLoad);

  useEffect(() => {
    if (isInitialLoad) {
      // Show loader on initial load or refresh
      setIsLoading(true);
      setShowContent(false);
    } else {
      // On navigation, just fade in smoothly
      setIsLoading(false);
      // Small delay for smooth transition
      setTimeout(() => {
        setShowContent(true);
      }, 100);
    }
  }, [isInitialLoad]);

  const handleLoadComplete = () => {
    setIsLoading(false);
    setTimeout(() => {
      setShowContent(true);
      // Notify parent that home has loaded
      if (onLoadComplete) {
        onLoadComplete();
      }
    }, 200);
  };

  return (
    <>
      {isLoading && isInitialLoad ? (
        <div className="loading-screen">
          <OrbLoader onComplete={handleLoadComplete} />
        </div>
      ) : (
        <>
          <ShaderBackground />
          <div className="shader-overlay"></div>
          <div className={`landing-content ${showContent ? 'visible' : ''}`}>
            <div className="landing-hero">
              <h1 className="landing-title">
                <span className="title-word" style={{ '--delay': '0s' }}>TFT</span>
                <span className="title-word" style={{ '--delay': '0.15s' }}>BOT</span>
              </h1>
              
              <div className="title-underline" style={{ '--delay': '0.3s' }}></div>
              
              <p className="landing-tagline" style={{ '--delay': '0.45s' }}>
                Three-layer intelligence system
              </p>
            </div>

            <div className="landing-cta" style={{ '--delay': '0.6s' }}>
              <Link to="/dashboard" className="cta-primary">
                <span>Launch Dashboard</span>
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                  <path d="M7 4L13 10L7 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
              </Link>
            </div>
          </div>
        </>
      )}
    </>
  );
}
