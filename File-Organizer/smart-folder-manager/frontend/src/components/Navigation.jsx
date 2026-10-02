import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import '../styles/Navigation.css';

function Navigation() {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="navbar">
      <div className="nav-container">
        <Link to="/" className="nav-logo">
          <span className="logo-icon">📁</span>
          Smart File Organizer
        </Link>

        <div className="nav-menu">
          <Link 
            to="/" 
            className={`nav-link ${isActive('/') ? 'active' : ''}`}
          >
            Home
          </Link>
          <Link 
            to="/organize" 
            className={`nav-link ${isActive('/organize') ? 'active' : ''}`}
          >
            Organize
          </Link>
          <Link 
            to="/processing" 
            className={`nav-link ${isActive('/processing') ? 'active' : ''}`}
          >
            Processing
          </Link>
          <Link 
            to="/classification" 
            className={`nav-link ${isActive('/classification') ? 'active' : ''}`}
          >
            Classification
          </Link>
          <Link 
            to="/batch-operations" 
            className={`nav-link ${isActive('/batch-operations') ? 'active' : ''}`}
          >
            Batch Operations
          </Link>
          <Link 
            to="/duplicates" 
            className={`nav-link ${isActive('/duplicates') ? 'active' : ''}`}
          >
            Duplicates
          </Link>
          <Link 
            to="/history" 
            className={`nav-link ${isActive('/history') ? 'active' : ''}`}
          >
            History
          </Link>
          <Link 
            to="/settings" 
            className={`nav-link ${isActive('/settings') ? 'active' : ''}`}
          >
            Settings
          </Link>
        </div>
      </div>
    </nav>
  );
}

export default Navigation;
