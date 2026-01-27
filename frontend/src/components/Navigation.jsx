import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import './Navigation.css';

export default function Navigation() {
  const [isSignedIn, setIsSignedIn] = useState(false);
  const location = useLocation();

  return (
    <nav className="nav-pill">
      <div className="nav-items">
        <NavLink 
          to="/home"
          className={({ isActive }) => `nav-item ${isActive || location.pathname === '/' ? 'active' : ''}`}
        >
          Home
        </NavLink>
        <NavLink 
          to="/dashboard"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          Dashboard
        </NavLink>
        <NavLink 
          to="/logs"
          className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
        >
          Logs
        </NavLink>
      </div>
      <button 
        className="nav-signin"
        onClick={() => setIsSignedIn(!isSignedIn)}
      >
        {isSignedIn ? 'Sign Out' : 'Sign In'}
      </button>
    </nav>
  );
}
