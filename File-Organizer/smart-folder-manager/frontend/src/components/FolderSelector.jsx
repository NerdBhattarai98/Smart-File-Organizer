import React, { useState } from 'react';
import '../styles/FolderSelector.css';

function FolderSelector({ onFolderSelect, selectedFolder }) {
  const [customPath, setCustomPath] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);

  // Use absolute paths for this machine to avoid ~/ resolving to the wrong user.
  const commonFolders = [
    { label: 'Desktop', path: '/Users/pranil/Desktop' },
    { label: 'Documents', path: '/Users/pranil/Documents' },
    { label: 'Downloads', path: '/Users/pranil/Downloads' },
  ];

  const handleSelectFolder = (path) => {
    onFolderSelect(path);
  };

  const handleCustomSubmit = (e) => {
    e.preventDefault();
    if (customPath.trim()) {
      handleSelectFolder(customPath);
      setShowCustomInput(false);
      setCustomPath('');
    }
  };

  return (
    <div className="folder-selector">
      <h2>Select Folder</h2>
      <div className="folder-options">
        {commonFolders.map((folder) => (
          <button
            key={folder.path}
            className={`folder-btn ${selectedFolder === folder.path ? 'active' : ''}`}
            onClick={() => handleSelectFolder(folder.path)}
          >
            <span className="folder-icon">📁</span>
            <span className="folder-label">{folder.label}</span>
          </button>
        ))}
      </div>

      {!showCustomInput ? (
        <button
          className="custom-folder-btn"
          onClick={() => setShowCustomInput(true)}
        >
          + Custom Folder
        </button>
      ) : (
        <form onSubmit={handleCustomSubmit} className="custom-input-form">
          <input
            type="text"
            placeholder="Enter folder path..."
            value={customPath}
            onChange={(e) => setCustomPath(e.target.value)}
            autoFocus
            className="custom-path-input"
          />
          <div className="custom-input-buttons">
            <button type="submit" className="submit-btn">Add</button>
            <button
              type="button"
              className="cancel-btn"
              onClick={() => {
                setShowCustomInput(false);
                setCustomPath('');
              }}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {selectedFolder && (
        <div className="selected-folder-info">
          <p className="label">Current Folder:</p>
          <p className="path">{selectedFolder}</p>
        </div>
      )}
    </div>
  );
}

export default FolderSelector;
