import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { useEffect, useRef, useState } from 'react';
import Navigation from './components/Navigation';
import Footer from './components/Footer';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Logs from './pages/Logs';
import './App.css';

function AppContent() {
  const location = useLocation();
  const [showNavAndFooter, setShowNavAndFooter] = useState(false);
  const [isHomePage, setIsHomePage] = useState(false);
  const [homeLoadComplete, setHomeLoadComplete] = useState(false);
  const previousPathRef = useRef(null);
  const navigationKeyRef = useRef(sessionStorage.getItem('navKey') || null);

  // Check if we're on home page and detect navigation vs refresh
  useEffect(() => {
    const isHome = location.pathname === '/' || location.pathname === '/home';
    setIsHomePage(isHome);
    
    // Generate a navigation key for this session
    if (!navigationKeyRef.current) {
      navigationKeyRef.current = Date.now().toString();
      sessionStorage.setItem('navKey', navigationKeyRef.current);
    }
    
    // Check if path changed (navigation) or same (refresh)
    const pathChanged = previousPathRef.current !== null && previousPathRef.current !== location.pathname;
    
    if (pathChanged) {
      // Navigation occurred
      if (isHome) {
        // Navigating to home, don't show orb
        setHomeLoadComplete(true);
        setShowNavAndFooter(true);
      } else {
        // Navigating away from home
        setShowNavAndFooter(true);
      }
    } else if (isHome) {
      // Same path on home = refresh or first load, show orb
      setHomeLoadComplete(false);
      setShowNavAndFooter(false);
    } else {
      // On other pages, show nav immediately
      setShowNavAndFooter(true);
    }
    
    previousPathRef.current = location.pathname;
  }, [location.pathname]);

  const handleHomeLoadComplete = () => {
    setHomeLoadComplete(true);
    setShowNavAndFooter(true);
  };

  // Show orb on initial home load (first visit or refresh, not navigation)
  const isInitialHomeLoad = isHomePage && !homeLoadComplete;

  return (
    <div className="app">
      {showNavAndFooter && (
        <>
          <Navigation />
          {isHomePage && <Footer />}
        </>
      )}
      <div className="page-transition-wrapper" key={location.pathname}>
        <Routes location={location}>
          <Route 
            path="/" 
            element={<Home isInitialLoad={isInitialHomeLoad} onLoadComplete={handleHomeLoadComplete} />} 
          />
          <Route 
            path="/home" 
            element={<Home isInitialLoad={isInitialHomeLoad} onLoadComplete={handleHomeLoadComplete} />} 
          />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/logs" element={<Logs />} />
        </Routes>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
