import { useState, useEffect } from 'react';
import ShaderBackground from '../components/ShaderBackground';
import OrbLoader from '../components/OrbLoader';
import './Home.css';

export default function Home({ isInitialLoad = false, onLoadComplete }) {
  const [isLoading, setIsLoading] = useState(isInitialLoad);
  const [showContent, setShowContent] = useState(!isInitialLoad);

  useEffect(() => {
    if (isInitialLoad) {
      setIsLoading(true);
      setShowContent(false);
    } else {
      setIsLoading(false);
      setTimeout(() => {
        setShowContent(true);
      }, 100);
    }
  }, [isInitialLoad]);

  const handleLoadComplete = () => {
    setIsLoading(false);
    setTimeout(() => {
      setShowContent(true);
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
          
          <div className={`home-page ${showContent ? 'visible' : ''}`}>
            <div className="home-content">
              <div className="hero-section">
                <h1 className="hero-title">
                  <span className="title-word" style={{ '--delay': '0s' }}>tft</span>
                  <span className="title-word accent" style={{ '--delay': '0.1s' }}>bot</span>
                </h1>
                
                <p className="hero-tagline">
                  <span className="tagline-word" style={{ '--delay': '0.2s' }}>three-layer</span>
                  <span className="tagline-word" style={{ '--delay': '0.25s' }}>intelligence</span>
                  <span className="tagline-word" style={{ '--delay': '0.3s' }}>system</span>
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
