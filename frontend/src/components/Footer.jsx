import { useEffect, useRef } from 'react';
import './Footer.css';

export default function Footer() {
  const wrapperRef = useRef(null);
  const animationRef = useRef(null);

  useEffect(() => {
    const wrapper = wrapperRef.current;
    if (!wrapper) return;

    let position = 0;
    const speed = 0.3;
    let singleSetWidth = 0;

    const calculateSetWidth = () => {
      const iconCount = 5; // Number of unique icons
      const icons = wrapper.querySelectorAll('.tech-icon');
      if (icons.length >= iconCount) {
        let totalWidth = 0;
        const gap = parseFloat(getComputedStyle(wrapper).gap) || 24;
        for (let i = 0; i < iconCount; i++) {
          totalWidth += icons[i].offsetWidth;
        }
        totalWidth += gap * iconCount; // Add gaps
        singleSetWidth = totalWidth;
      }
    };

    // Wait for layout
    setTimeout(() => {
      calculateSetWidth();
    }, 100);

    const animate = () => {
      if (singleSetWidth > 0) {
        position -= speed;
        
        // When we've scrolled one full set, reset to create infinite loop
        if (Math.abs(position) >= singleSetWidth) {
          position = 0;
        }
        
        wrapper.style.transform = `translateX(${position}px)`;
      }
      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  const techIcons = [
    { name: 'React', url: 'https://react.dev', icon: (
      <svg viewBox="0 0 24 24" fill="currentColor">
        <circle cx="12" cy="12" r="2" fill="currentColor"/>
        <ellipse cx="12" cy="12" rx="11" ry="4.2" fill="none" stroke="currentColor" strokeWidth="1"/>
        <ellipse cx="12" cy="12" rx="11" ry="4.2" fill="none" stroke="currentColor" strokeWidth="1" transform="rotate(60 12 12)"/>
        <ellipse cx="12" cy="12" rx="11" ry="4.2" fill="none" stroke="currentColor" strokeWidth="1" transform="rotate(-60 12 12)"/>
      </svg>
    )},
    { name: 'Vite', url: 'https://vitejs.dev', icon: (
      <svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2L2 7l1.5 11L12 22l8.5-4L22 7l-10-5zm0 2.2l7.5 3.75-1.2 8.4L12 19.8l-6.3-3.45-1.2-8.4L12 4.2z"/>
      </svg>
    )},
    { name: 'WebGL', url: 'https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API', icon: (
      <svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 2.18l8 4v8.64l-8 4-8-4V8.18l8-4zM4 9.09v5.82l6 3v-5.82l-6-3zm16 0l-6 3v5.82l6-3V9.09z"/>
      </svg>
    )},
    { name: 'Python', url: 'https://www.python.org', icon: (
      <svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2c-1.1 0-2.1.1-3 .3C7.1 2.7 6 3.7 6 5v2h6v1H5c-1.1 0-2.1.7-2.4 1.7-.4 1.2-.4 2.5 0 3.7.3 1 1.3 1.7 2.4 1.7h1.5v-2c0-1.4 1.2-2.6 2.6-2.6h5.8c1.1 0 2-.9 2-2V5c0-1.3-1.1-2.3-2.9-2.7-.9-.2-1.9-.3-3-.3zm-2.5 1.5c.4 0 .8.3.8.8s-.3.8-.8.8-.8-.3-.8-.8.4-.8.8-.8zM18 8v2c0 1.4-1.2 2.6-2.6 2.6H9.6c-1.1 0-2 .9-2 2v4c0 1.3 1.3 2.1 2.6 2.4 1.5.4 3 .4 4.8 0 1.2-.3 2.6-1 2.6-2.4v-2h-6v-1h8.5c1.1 0 1.6-.8 2-1.7.4-1 .4-2 0-3-.3-.8-.9-1.5-2-1.7-.3-.1-.7-.2-1.1-.2H18zm-3.5 10c.4 0 .8.3.8.8s-.3.8-.8.8-.8-.3-.8-.8.4-.8.8-.8z"/>
      </svg>
    )},
    { name: 'Three.js', url: 'https://threejs.org', icon: (
      <svg viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2L2 19.5h20L12 2zm0 4l6.5 11.5h-13L12 6z"/>
      </svg>
    )}
  ];

  // Create 4 sets for seamless infinite scroll
  const iconSets = [...techIcons, ...techIcons, ...techIcons, ...techIcons];

  return (
    <>
      {/* Status bar floating above footer */}
      <div className="floating-status-bar">
        <div className="status-item">
          <span className="status-dot active"></span>
          <span className="status-label">system online</span>
        </div>
        <div className="status-divider"></div>
        <div className="status-item">
          <span className="status-value">v0.1.0</span>
        </div>
        <div className="status-divider"></div>
        <div className="status-item">
          <span className="status-label">ds project pitchfire</span>
        </div>
      </div>

      <footer className="app-footer">
        <div className="footer-content">
          <p className="footer-text">
            team: matthew kim • sou hamura • brendan chung • sabrina nguyen • rachel seo • juntaek oh |{' '}
            <a 
              href="https://github.com/MatthewKim323/tft" 
              target="_blank" 
              rel="noopener noreferrer"
              className="footer-link"
            >
              <svg className="footer-icon" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              source
            </a>
          </p>
          
          <div className="footer-built-with">
            <p className="footer-built-label">built with</p>
            <div className="footer-tech-icons">
              <div className="footer-tech-icons-wrapper" ref={wrapperRef}>
                {iconSets.map((icon, index) => (
                  <a
                    key={index}
                    href={icon.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="tech-icon"
                    title={icon.name}
                  >
                    {icon.icon}
                  </a>
                ))}
              </div>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
}
