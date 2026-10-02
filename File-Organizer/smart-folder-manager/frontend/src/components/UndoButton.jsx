import React from 'react';
import '../styles/UndoButton.css';

function UndoButton({ onUndo, disabled, actionCount }) {
  return (
    <div className="undo-container">
      <button
        className={`undo-button ${disabled ? 'disabled' : ''}`}
        onClick={onUndo}
        disabled={disabled}
        title={disabled ? 'No actions to undo' : 'Undo last action'}
      >
        <span className="undo-icon">↶</span>
        <span className="undo-text">Undo</span>
      </button>

      {actionCount > 0 && (
        <div className="action-count-badge">
          {actionCount}
        </div>
      )}
    </div>
  );
}

export default UndoButton;
