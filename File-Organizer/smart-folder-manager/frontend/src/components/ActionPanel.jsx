import React from 'react';
import '../styles/ActionPanel.css';

function ActionPanel({ onApprove, onSkip, disabled, currentIndex, totalFiles }) {
  const progressPercent = totalFiles > 0 ? ((currentIndex + 1) / totalFiles) * 100 : 0;

  return (
    <div className="action-panel">
      <div className="progress-section">
        <div className="progress-header">
          <span className="progress-label">Progress</span>
          <span className="progress-count">{currentIndex + 1} / {totalFiles}</span>
        </div>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progressPercent}%` }}></div>
        </div>
      </div>

      <div className="action-buttons-section">
        <button
          className="btn btn-primary btn-approve"
          onClick={onApprove}
          disabled={disabled}
        >
          <span className="icon">✓</span>
          Approve & Move
        </button>
        <button
          className="btn btn-secondary btn-skip"
          onClick={onSkip}
          disabled={disabled}
        >
          <span className="icon">→</span>
          Skip File
        </button>
      </div>

      <div className="action-stats">
        <div className="stat-item">
          <span className="stat-label">Files Remaining</span>
          <span className="stat-value">{Math.max(0, totalFiles - currentIndex - 1)}</span>
        </div>
      </div>
    </div>
  );
}

export default ActionPanel;
