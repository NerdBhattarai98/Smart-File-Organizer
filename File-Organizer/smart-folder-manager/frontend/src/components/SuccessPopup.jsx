import React, { useEffect, useState } from 'react';
import '../styles/SuccessPopup.css';

const SuccessPopup = ({ isVisible, successCount, failedCount, onClose }) => {
  const [isAnimating, setIsAnimating] = useState(isVisible);

  useEffect(() => {
    if (isVisible) {
      setIsAnimating(true);
      // Auto-close after 5 seconds
      const timer = setTimeout(() => {
        setIsAnimating(false);
        setTimeout(onClose, 300); // Wait for animation to finish
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [isVisible, onClose]);

  if (!isVisible && !isAnimating) return null;

  return (
    <div className={`success-popup ${isAnimating ? 'show' : 'hide'}`}>
      <div className="popup-content">
        <div className="popup-icon">✓</div>
        <h2 className="popup-title">Organization Complete!</h2>
        <div className="popup-stats">
          <div className="stat success">
            <span className="stat-number">{successCount}</span>
            <span className="stat-label">Files Organized</span>
          </div>
          {failedCount > 0 && (
            <div className="stat warning">
              <span className="stat-number">{failedCount}</span>
              <span className="stat-label">Skipped/Failed</span>
            </div>
          )}
        </div>
        <button className="popup-close" onClick={onClose}>
          Close
        </button>
      </div>
    </div>
  );
};

export default SuccessPopup;
