import { useEffect, useRef } from 'react';
import './Footer.css';

export default function Footer() {
  const wrapperRef = useRef(null);
  const animationRef = useRef(null);

  useEffect(() => {
    const wrapper = wrapperRef.current;
    if (!wrapper) return;

    let position = 0;
    const speed = 0.15; // Much slower speed
    let setWidth = 0;
    let isPaused = false;

    // Calculate one set's width (first 5 icons)
    const calculateSetWidth = () => {
      if (wrapper.children.length >= 10) {
        // More reliable: measure from first icon to 6th icon (start of second set)
        const firstIcon = wrapper.children[0];
        const sixthIcon = wrapper.children[5]; // Start of second set
        
        if (firstIcon && sixthIcon) {
          const firstRect = firstIcon.getBoundingClientRect();
          const sixthRect = sixthIcon.getBoundingClientRect();
          
          // Distance from start of first icon to start of sixth icon
          setWidth = sixthRect.left - firstRect.left;
          
          // Fallback: if measurement fails, calculate manually
          if (setWidth <= 0) {
            const gap = parseFloat(getComputedStyle(wrapper).gap) || 20;
            let totalWidth = 0;
            for (let i = 0; i < 5; i++) {
              const child = wrapper.children[i];
              totalWidth += child.offsetWidth || child.getBoundingClientRect().width;
              if (i < 4) totalWidth += gap;
            }
            setWidth = totalWidth;
          }
        }
      }
    };

    // Wait for DOM to be ready and layout to complete
    const init = () => {
      const tryCalculate = () => {
        requestAnimationFrame(() => {
          calculateSetWidth();
          if (setWidth === 0 && wrapper.children.length >= 10) {
            setTimeout(tryCalculate, 50);
          }
        });
      };
      tryCalculate();
    };
    init();

    const handleMouseEnter = () => { isPaused = true; };
    const handleMouseLeave = () => { isPaused = false; };
    
    wrapper.addEventListener('mouseenter', handleMouseEnter);
    wrapper.addEventListener('mouseleave', handleMouseLeave);

    let lastTime = performance.now();
    
    const animate = (currentTime) => {
      if (!isPaused && setWidth > 0) {
        const deltaTime = Math.min(currentTime - lastTime, 16.67); // Cap at 60fps
        const frameSpeed = (speed * deltaTime) / 16.67;
        position -= frameSpeed;
        
        // Seamless loop - when we scroll past one complete set, wrap back
        // This keeps the transform continuous with no visible jump
        if (position <= -setWidth) {
          position = position + setWidth;
        }
      }
      
      lastTime = currentTime;
      wrapper.style.transform = `translate3d(${position}px, 0, 0)`;
      wrapper.style.willChange = 'transform';
      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      wrapper.removeEventListener('mouseenter', handleMouseEnter);
      wrapper.removeEventListener('mouseleave', handleMouseLeave);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  const techIcons = [
    { name: 'React', url: 'https://react.dev', icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
        <circle cx="12" cy="12" r="2" fill="currentColor"/>
        <ellipse cx="12" cy="12" rx="11" ry="4.2" fill="none" stroke="currentColor" strokeWidth="1"/>
        <ellipse cx="12" cy="12" rx="11" ry="4.2" fill="none" stroke="currentColor" strokeWidth="1" transform="rotate(60 12 12)"/>
        <ellipse cx="12" cy="12" rx="11" ry="4.2" fill="none" stroke="currentColor" strokeWidth="1" transform="rotate(-60 12 12)"/>
      </svg>
    )},
    { name: 'Vite', url: 'https://vitejs.dev', icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12.089 0L1.525 4.804v5.994c0 8.46 4.893 16.24 10.564 19.198 5.67-2.958 10.563-10.737 10.563-19.198V4.804L12.089 0zm.636 2.12l9.165 3.9v5.678c0 7.696-4.25 14.63-9.165 17.24-4.915-2.61-9.165-9.544-9.165-17.24V6.02l9.165-3.9zM12 6.6c-2.406 0-4.36 1.953-4.36 4.36S9.594 15.32 12 15.32s4.36-1.953 4.36-4.36S14.406 6.6 12 6.6zm0 1.44c1.607 0 2.92 1.312 2.92 2.92S13.607 14.88 12 14.88 9.08 13.568 9.08 11.96s1.313-2.92 2.92-2.92z"/>
      </svg>
    )},
    { name: 'WebGL', url: 'https://developer.mozilla.org/en-US/docs/Web/API/WebGL_API', icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2L2 7v10l10 5 10-5V7L12 2zm0 2.18l8 4v8.64l-8 4-8-4V8.18l8-4zM4 9.09v5.82l6 3v-5.82l-6-3zm16 0l-6 3v5.82l6-3V9.09z"/>
      </svg>
    )},
    { name: 'Python', url: 'https://www.python.org', icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
        <path d="M9.585 11.692h4.328s2.432.039 2.432-2.35V5.94s-.13-2.996-2.432-2.996h-4.328s-2.432-.04-2.432 2.35v3.402s.13 2.996 2.432 2.996zm-1.19-6.56h4.328s1.664-.01 1.664 1.48v2.65s.008 1.48-1.664 1.48H8.395s-1.664.01-1.664-1.48V6.612s-.008-1.48 1.664-1.48zm9.21 6.56h4.328s2.432.039 2.432-2.35V5.94s-.13-2.996-2.432-2.996h-4.328s-2.432-.04-2.432 2.35v3.402s.13 2.996 2.432 2.996zm-1.19-6.56h4.328s1.664-.01 1.664 1.48v2.65s.008 1.48-1.664 1.48h-4.328s-1.664.01-1.664-1.48V6.612s-.008-1.48 1.664-1.48zM9.585 15.447h4.328s2.432.04 2.432 2.35v3.401s.13 2.997 2.432 2.997h4.328s2.432.04 2.432-2.35v-3.401s-.13-2.997-2.432-2.997h-4.328s-2.432-.04-2.432-2.35v-3.402s.13-2.996-2.432-2.996zm1.19 6.56h4.328s1.664.01 1.664-1.48v-2.65s.008-1.48-1.664-1.48h-4.328s-1.664-.01-1.664 1.48v2.65s.008 1.48 1.664 1.48z"/>
      </svg>
    )},
    { name: 'Node.js', url: 'https://nodejs.org', icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
        <path d="M11.998,24c-0.321,0-0.641-0.084-0.922-0.247l-2.936-1.737c-0.438-0.245-0.224-0.332-0.08-0.383 c0.585-0.203,0.703-0.25,1.328-0.604c0.065-0.037,0.151-0.023,0.218,0.017l2.256,1.339c0.082,0.045,0.197,0.045,0.272,0l8.795-5.076 c0.082-0.047,0.134-0.141,0.134-0.238V6.921c0-0.099-0.053-0.192-0.137-0.242l-8.791-5.072c-0.081-0.047-0.189-0.047-0.271,0 L3.075,6.68C2.99,6.729,2.936,6.825,2.936,6.921v10.15c0,0.097,0.054,0.191,0.139,0.24l2.409,1.392 c1.307,0.654,2.108-0.116,2.108-0.89V7.787c0-0.142,0.114-0.253,0.256-0.253h1.115c0.139,0,0.255,0.112,0.255,0.253v10.021 c0,1.745-0.95,2.745-2.604,2.745c-0.508,0-0.909,0-2.026-0.551L2.28,18.675c-0.57-0.329-0.922-0.945-0.922-1.604V6.921 c0-0.659,0.353-1.275,0.922-1.603l8.795-5.082c0.557-0.315,1.296-0.315,1.848,0l8.794,5.082c0.570,0.329,0.924,0.944,0.924,1.603 v10.15c0,0.659-0.354,1.265-0.924,1.604l-8.794,5.078C12.643,23.916,12.324,24,11.998,24z M19.099,13.993 c0-1.9-1.284-2.406-3.987-2.763c-2.731-0.361-3.009-0.548-3.009-1.187c0-0.528,0.235-1.233,2.258-1.233 c1.807,0,2.473,0.389,2.747,0.571c0.055,0.033,0.128,0.033,0.176-0.014l0.643-0.559 c0.044-0.038,0.071-0.103,0.071-0.167c0-0.112-0.068-0.22-0.174-0.28c-0.398-0.221-1.236-0.566-3.352-0.566 c-3.624,0-4.957,1.833-4.957,3.476c0,2.093,1.396,2.915,4.305,3.311c2.78,0.388,3.007,0.646,3.007,1.186 c0,0.697-0.412,1.38-2.42,1.38c-2.062,0-2.871-0.435-3.281-0.688c-0.056-0.035-0.13-0.035-0.186,0.01l-0.657,0.544 c-0.048,0.04-0.074,0.104-0.074,0.165c0,0.106,0.066,0.211,0.18,0.273c0.428,0.24,1.353,0.6,3.487,0.6 C16.277,17.993,19.099,16.491,19.099,13.993z"/>
      </svg>
    )}
  ];

  // Create multiple sets for seamless looping
  const iconSets = Array(3).fill(techIcons).flat();

  return (
    <footer className="app-footer">
      <div className="footer-content">
        <p className="footer-text">
          built for ds project pitchfire
        </p>
        <p className="footer-text">
          team: matthew kim • sou hamura • brendan chung • sabrina nguyen • rachel seo • juntaek oh |{' '}
          <a 
            href="https://github.com/MatthewKim323/tft" 
            target="_blank" 
            rel="noopener noreferrer"
            className="footer-link"
          >
            <svg className="footer-icon" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            source
          </a>
        </p>
        
        <div className="footer-built-with">
          <p className="footer-built-label">built with:</p>
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
  );
}
