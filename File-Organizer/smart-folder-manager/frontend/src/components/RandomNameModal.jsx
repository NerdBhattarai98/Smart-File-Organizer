import React, { useState, useEffect } from 'react';
import '../styles/RandomNameModal.css';

const RandomNameModal = ({ file, isOpen, onClose, onRename, onSkip }) => {
  const [newName, setNewName] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (file && file.suggested_name) {
      setNewName(file.suggested_name);
    }
    setError('');
  }, [file, isOpen]);

  const handleRename = () => {
    if (!newName.trim()) {
      setError('Please enter a new name');
      return;
    }

    // Validate filename
    if (newName.includes('/') || newName.includes('\\')) {
      setError('Invalid characters in filename');
      return;
    }

    const originalExt = file.filename.includes('.') ? file.filename.split('.').pop() : '';
    const proposedName = newName.trim();
    const hasExtension = proposedName.includes('.') && proposedName.split('.').pop() !== '';
    const safeName = !hasExtension && originalExt
      ? `${proposedName}.${originalExt}`
      : proposedName;

    onRename(file.filename, safeName);
    setNewName('');
  };

  const handleSkip = () => {
    onSkip(file.filename);
    setNewName('');
  };

  if (!isOpen || !file) {
    return null;
  }

  return (
    <div className="modal-overlay">
      <div className="random-name-modal">
        <div className="modal-header">
          <h2>🔀 Rename Random File</h2>
          <button className="modal-close" onClick={handleSkip}>×</button>
        </div>

        <div className="modal-content">
          <p className="file-info">
            <strong>File:</strong> {file.filename}
          </p>
          
          <div className="reason-box">
            <span className="reason-label">Detected as:</span>
            <span className="reason-text">{file.random_reason}</span>
          </div>

          <div className="input-group">
            <label>New filename:</label>
            <input
              type="text"
              value={newName}
              onChange={(e) => {
                setNewName(e.target.value);
                setError('');
              }}
              placeholder="Enter new filename"
              autoFocus
              onKeyPress={(e) => {
                if (e.key === 'Enter') handleRename();
              }}
            />
            {error && <span className="error">{error}</span>}
          </div>

          <div className="suggestion-text">
            💡 Suggested: {file.suggested_name}
          </div>
        </div>

        <div className="modal-actions">
          <button className="btn-skip" onClick={handleSkip}>
            Skip (Organize as-is)
          </button>
          <button className="btn-rename" onClick={handleRename}>
            ✓ Rename & Organize
          </button>
        </div>
      </div>
    </div>
  );
};

export default RandomNameModal;
