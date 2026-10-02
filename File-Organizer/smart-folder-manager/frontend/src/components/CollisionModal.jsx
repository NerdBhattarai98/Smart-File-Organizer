import React, { useState } from 'react';
import '../styles/CollisionModal.css';

const CollisionModal = ({ collisions, onResolve, onSkip }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [resolutionChoice, setResolutionChoice] = useState(null);
  const [customName, setCustomName] = useState('');

  if (!collisions || collisions.length === 0) {
    return null;
  }

  const currentCollision = collisions[currentIndex];
  
  // Safety checks
  if (!currentCollision || !Array.isArray(currentCollision.files) || currentCollision.files.length < 2) {
    return null;
  }
  
  // Find files with flexible matching
  const newFile = currentCollision.files.find(f => f && (f.status === 'new_file' || f.type === 'new'));
  const existingFile = currentCollision.files.find(f => f && (f.status === 'existing_file' || f.type === 'existing'));
  
  // Fallback to array order if filtering fails
  const fileNew = newFile || (currentCollision.files[0] && currentCollision.files[0].filename ? currentCollision.files[0] : null);
  const fileExisting = existingFile || (currentCollision.files[1] && currentCollision.files[1].filename ? currentCollision.files[1] : null);
  
  // Final validation
  if (!fileNew || !fileExisting) {
    return null;
  }

  const handleResolve = (action, newName = null) => {
    const keepPath = action === 'keep_new' ? fileNew.filepath : fileExisting.filepath;
    onResolve(currentCollision.collision_id, keepPath, action, newName);
    
    if (currentIndex < collisions.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setResolutionChoice(null);
      setCustomName('');
    }
  };

  const handleSkipAll = () => {
    onSkip();
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  return (
    <div className="collision-modal-overlay">
      <div className="collision-modal">
        <div className="collision-header">
          <h2>⚠️ File Collision Detected</h2>
          <p className="collision-counter">
            Collision {currentIndex + 1} of {collisions.length}
          </p>
        </div>

        <div className="collision-info">
          <p className="collision-type">
            {currentCollision.collision_type.includes('same_content') ? '🔄 Duplicate Content' : '📁 Name Conflict'}
          </p>
          <p className="collision-detail">{currentCollision.recommendation}</p>
        </div>

        <div className="collision-files">
          <div className="file-comparison">
            <div className="file-column new-file">
              <div className="file-label">📄 New File (Being Organized)</div>
              <div className="file-details">
                <div className="file-name">{fileNew?.filename || 'Unknown'}</div>
                <div className="file-size">{formatFileSize(fileNew?.size || 0)}</div>
                <div className="file-path">{fileNew?.filepath || 'N/A'}</div>
                <div className="file-time">Modified: {fileNew?.modified_time ? formatDate(fileNew.modified_time) : 'N/A'}</div>
              </div>
              <button
                className="btn-keep btn-keep-new"
                onClick={() => setResolutionChoice('keep_new')}
              >
                Keep This File
              </button>
            </div>

            <div className="file-vs">VS</div>

            <div className="file-column existing-file">
              <div className="file-label">📂 Existing File (In Target Folder)</div>
              <div className="file-details">
                <div className="file-name">{fileExisting?.filename || 'Unknown'}</div>
                <div className="file-size">{formatFileSize(fileExisting?.size || 0)}</div>
                <div className="file-path">{fileExisting?.filepath || 'N/A'}</div>
                <div className="file-time">Modified: {fileExisting?.modified_time ? formatDate(fileExisting.modified_time) : 'N/A'}</div>
              </div>
              <button
                className="btn-keep btn-keep-existing"
                onClick={() => setResolutionChoice('keep_existing')}
              >
                Keep This File
              </button>
            </div>
          </div>
        </div>

        {resolutionChoice && (
          <div className="collision-resolution">
            {resolutionChoice === 'keep_new' && (
              <div className="resolution-options">
                <button
                  className="btn-action btn-remove-existing"
                  onClick={() => handleResolve('keep_new')}
                >
                  Remove Existing File
                </button>
                <button
                  className="btn-action btn-rename"
                  onClick={() => setResolutionChoice('rename_new')}
                >
                  Rename New File Instead
                </button>
              </div>
            )}

            {resolutionChoice === 'keep_existing' && (
              <div className="resolution-options">
                <button
                  className="btn-action btn-skip"
                  onClick={() => handleResolve('keep_existing')}
                >
                  Skip Organizing This File
                </button>
                <button
                  className="btn-action btn-rename"
                  onClick={() => setResolutionChoice('rename_existing')}
                >
                  Rename Existing File Instead
                </button>
              </div>
            )}

            {resolutionChoice === 'rename_new' && (
              <div className="resolution-options">
                <input
                  type="text"
                  className="rename-input"
                  placeholder="Enter new name..."
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  autoFocus
                />
                <button
                  className="btn-action btn-confirm"
                  onClick={() => handleResolve('rename_new', customName)}
                  disabled={!customName.trim()}
                >
                  Rename & Organize
                </button>
              </div>
            )}

            {resolutionChoice === 'rename_existing' && (
              <div className="resolution-options">
                <input
                  type="text"
                  className="rename-input"
                  placeholder="Enter new name..."
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  autoFocus
                />
                <button
                  className="btn-action btn-confirm"
                  onClick={() => handleResolve('rename_existing', customName)}
                  disabled={!customName.trim()}
                >
                  Rename Existing
                </button>
              </div>
            )}
          </div>
        )}

        <div className="collision-actions">
          <button className="btn-nav btn-nav-prev" onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))} disabled={currentIndex === 0}>
            ← Previous
          </button>
          <button className="btn-nav btn-nav-next" onClick={() => setCurrentIndex(Math.min(collisions.length - 1, currentIndex + 1))} disabled={currentIndex === collisions.length - 1}>
            Next →
          </button>
          <button className="btn-cancel" onClick={handleSkipAll}>
            Cancel Organization
          </button>
        </div>
      </div>
    </div>
  );
};

export default CollisionModal;
