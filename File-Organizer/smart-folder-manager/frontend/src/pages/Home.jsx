import React from 'react';
import { useNavigate } from 'react-router-dom';
import '../styles/Home.css';

const Home = () => {
  const navigate = useNavigate();

  return (
    <div className="home-container">
      <div className="home-hero">
        <h1>Smart File Organizer</h1>
        <p>Intelligent file classification powered by AI</p>
        <button 
          className="btn btn-primary btn-large"
          onClick={() => navigate('/organize')}
        >
          Start Organizing
        </button>
      </div>

      <div className="home-features">
        <div className="feature-card">
          <div className="feature-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <h3>Multi-Select</h3>
          <p>Select multiple files at once and organize them all together</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2a4 4 0 0 1 4 4v2a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z"/>
              <path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2"/>
              <circle cx="12" cy="7" r="3"/>
            </svg>
          </div>
          <h3>AI Classification</h3>
          <p>Smart categorization based on filename patterns and metadata</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
          </div>
          <h3>Fast & Simple</h3>
          <p>Organize your files in seconds with an intuitive interface</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="1 4 1 10 7 10"/>
              <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
            </svg>
          </div>
          <h3>Undo Anytime</h3>
          <p>Easily undo operations if you change your mind</p>
        </div>
      </div>
    </div>
  );
};

export default Home;
