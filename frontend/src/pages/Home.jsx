import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import ShaderBackground from '../components/ShaderBackground';
import OrbLoader from '../components/OrbLoader';
import './Home.css';

export default function Home({ isInitialLoad = false, onLoadComplete }) {
  const [isLoading, setIsLoading] = useState(isInitialLoad);
  const [showContent, setShowContent] = useState(!isInitialLoad);
  const [mousePos, setMousePos] = useState({ x: 50, y: 50 });

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

    const handleMouseMove = (e) => {
      setMousePos({
        x: (e.clientX / window.innerWidth) * 100,
        y: (e.clientY / window.innerHeight) * 100
      });
    };
    
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
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
          <div className="shader-overlay"></div>
          
          <div 
            className={`home-page ${showContent ? 'visible' : ''}`}
            style={{ '--mouse-x': `${mousePos.x}%`, '--mouse-y': `${mousePos.y}%` }}
          >
            {/* Grid overlay */}
            <div className="grid-overlay"></div>
            
            <div className="home-content">
              {/* Main hero section */}
              <div className="hero-section">
                <h1 className="hero-title">
                  <span className="title-line">
                    <span className="title-word" style={{ '--delay': '0s' }}>tft</span>
                    <span className="title-word accent" style={{ '--delay': '0.1s' }}>bot</span>
                  </span>
                </h1>
                
                <p className="hero-tagline">
                  <span className="tagline-word" style={{ '--delay': '0.2s' }}>three-layer</span>
                  <span className="tagline-word" style={{ '--delay': '0.25s' }}>intelligence</span>
                  <span className="tagline-word" style={{ '--delay': '0.3s' }}>system</span>
                </p>

                <div className="hero-cta" style={{ '--delay': '0.4s' }}>
                  <Link to="/dashboard" className="cta-button">
                    <span className="cta-text">launch dashboard</span>
                    <span className="cta-icon">→</span>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
