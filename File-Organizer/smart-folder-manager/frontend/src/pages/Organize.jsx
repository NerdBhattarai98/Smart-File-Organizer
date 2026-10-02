import React, { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { scanFolder, classifyFiles, applyAction, batchApplyActions, undoAction, batchUndoActions, getUndoHistory, checkCollisions, resolveCollision } from '../services/api';
import CustomizationModal from '../components/CustomizationModal';
import CollisionModal from '../components/CollisionModal';
import SuccessPopup from '../components/SuccessPopup';
import RandomNameModal from '../components/RandomNameModal';
import '../styles/Organize.css';

const Organize = () => {
  const navigate = useNavigate();
  const [selectedFolder, setSelectedFolder] = useState('');
  const [customFolder, setCustomFolder] = useState('');
  const [activeQuickFolder, setActiveQuickFolder] = useState(null);
  const [files, setFiles] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [isOrganizing, setIsOrganizing] = useState(false);
  const [recommendations, setRecommendations] = useState({});
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [actionHistory, setActionHistory] = useState([]);
  const [organizationComplete, setOrganizationComplete] = useState(false);
  const [showCustomizationModal, setShowCustomizationModal] = useState(false);
  const [collisions, setCollisions] = useState([]);
  const [showCollisionModal, setShowCollisionModal] = useState(false);
  const [customizations, setCustomizations] = useState({});
  const [showSuccessPopup, setShowSuccessPopup] = useState(false);
  const [successStats, setSuccessStats] = useState({ successCount: 0, failedCount: 0 });
  const [showRandomNameModal, setShowRandomNameModal] = useState(false);
  const [randomNameQueue, setRandomNameQueue] = useState([]);
  const [currentRandomFile, setCurrentRandomFile] = useState(null);
  const [renamedFiles, setRenamedFiles] = useState({});  // Map of old name -> new name

  // Use the actual user home to avoid resolving to /Users/user on macOS.
  const homeDir = '/Users/pranil';

  const quickFolders = [
    { id: 'desktop', name: 'Desktop', path: `${homeDir}/Desktop`, icon: 'desktop' },
    { id: 'documents', name: 'Documents', path: `${homeDir}/Documents`, icon: 'documents' },
    { id: 'downloads', name: 'Downloads', path: `${homeDir}/Downloads`, icon: 'downloads' },
  ];

  const handleQuickFolderSelect = (folder) => {
    setActiveQuickFolder(folder.id);
    setSelectedFolder(folder.path);
    setFiles([]);
    setSelectedFiles(new Set());
    setOrganizationComplete(false);
  };

  const handleCustomFolderSelect = () => {
    if (customFolder.trim()) {
      setActiveQuickFolder('custom');
      setSelectedFolder(customFolder);
      setFiles([]);
      setSelectedFiles(new Set());
      setOrganizationComplete(false);
    }
  };

  const handleScanFolder = useCallback(async () => {
    if (!selectedFolder.trim()) {
      setError('Please select a folder first');
      setTimeout(() => setError(null), 3000);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      setOrganizationComplete(false);
      setSelectedFiles(new Set());

      const scanResult = await scanFolder(selectedFolder);
      const scannedFiles = scanResult.files || [];
      setFiles(scannedFiles);

      if (scannedFiles.length > 0) {
        const classifyResult = await classifyFiles(scannedFiles);
        const recSource = classifyResult?.results || classifyResult?.classifications || [];
        const recommendationsMap = {};
        const randomFiles = [];  // Collect files with random names

        recSource.forEach((result, index) => {
          // PRIMARY: Use metadata_folder if available (derived from file content/meaning)
          // FALLBACK: Use predicted_category if metadata extraction failed
          const folderName = result.metadata_folder || result.predicted_category || result.category || 'Uncategorized';
          const confidence = result.metadata_confidence ?? result.confidence ?? result.confidence_score ?? result.score ?? 0.5;
          recommendationsMap[index] = {
            category: folderName,  // This is now the metadata folder name or category
            folderName: folderName,  // Explicit metadata folder name
            confidence,
            fileType: result.predicted_category,  // Keep original category for reference
          };
          
          // Check for random filenames
          if (result.is_random_name) {
            randomFiles.push({
              filename: result.filename,
              random_reason: result.random_reason,
              suggested_name: result.suggested_name
            });
          }
        });

        setRecommendations(recommendationsMap);
        
        // If there are random files, show rename modal for first one
        if (randomFiles.length > 0) {
          setRandomNameQueue(randomFiles);
          setCurrentRandomFile(randomFiles[0]);
          setShowRandomNameModal(true);
        }
        
        setSuccessMessage(`Found ${scannedFiles.length} files`);
        setTimeout(() => setSuccessMessage(null), 3000);
      } else {
        setSuccessMessage('No files found in this folder');
        setTimeout(() => setSuccessMessage(null), 3000);
      }
    } catch (err) {
      setError(err.message || 'Error scanning folder');
      setTimeout(() => setError(null), 3000);
    } finally {
      setIsLoading(false);
    }
  }, [selectedFolder]);

  const handleSelectFile = (index) => {
    const newSelected = new Set(selectedFiles);
    if (newSelected.has(index)) {
      newSelected.delete(index);
    } else {
      newSelected.add(index);
    }
    setSelectedFiles(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedFiles.size === files.length) {
      setSelectedFiles(new Set());
    } else {
      setSelectedFiles(new Set(files.map((_, i) => i)));
    }
  };

  const handleOrganize = useCallback(async () => {
    if (selectedFiles.size === 0) {
      setError('Please select files to organize');
      setTimeout(() => setError(null), 3000);
      return;
    }

    // Show customization modal
    setShowCustomizationModal(true);
  }, [selectedFiles]);

  const handleCustomizationConfirm = useCallback(async (customizationsData) => {
    setShowCustomizationModal(false);
    setCustomizations(customizationsData);
    
    try {
      setIsOrganizing(true);
      setError(null);

      // Build collision check request
      console.log('🔍 Starting collision detection...');
      const filesToCheck = [];
      
      for (const fileIndex of selectedFiles) {
        const file = files[fileIndex];
        const recommendation = recommendations[fileIndex];
        if (!file || !recommendation) continue;
        
        const filename = typeof file === 'string' ? file : file.name;
        const filepath = typeof file === 'string' ? `${selectedFolder}/${file}` : file.path;
        const fileSize = file.size || 0;
        const fileModified = file.modified || Date.now() / 1000;

        // Determine target folder - ensure it's an absolute path
        let targetFolder = selectedFolder;
        const category = recommendation.category || 'Other';
        
        // Apply customizations if any
        if (customizationsData[category]?.folderName) {
          targetFolder = `${selectedFolder}/${customizationsData[category].folderName}`;
        } else if (customizationsData[`file_${fileIndex}`]?.folderName) {
          targetFolder = `${selectedFolder}/${customizationsData[`file_${fileIndex}`].folderName}`;
        } else {
          targetFolder = `${selectedFolder}/${category}`;
        }

        filesToCheck.push({
          filename,
          filepath,
          size: fileSize,
          modified_time: fileModified,
          target_folder: targetFolder
        });
      }

      console.log('Files to check:', filesToCheck.map(f => ({ name: f.filename, target: f.target_folder })));
      console.log('Selected folder:', selectedFolder);
      console.log('Total files to organize:', filesToCheck.length);

      // Check for collisions
      console.log('Calling collision check API with:', { filesToCheckCount: filesToCheck.length, selectedFolder });
      let collisionResult;
      try {
        collisionResult = await checkCollisions(filesToCheck, selectedFolder);
        console.log('Collision check result:', collisionResult);
      } catch (apiErr) {
        console.error('Collision check API error:', apiErr);
        console.log('Proceeding without collision check...');
        collisionResult = { has_collisions: false, collisions: [] };
      }

      if (collisionResult?.has_collisions) {
        console.log(`Found ${collisionResult.collision_count} collision(s)`);
        console.log('Setting collisions state:', collisionResult.collisions);
        setCollisions(collisionResult.collisions);
        setShowCollisionModal(true);
        setIsOrganizing(false);
        console.log('Collision modal should now be visible');
        return;
      }

      console.log('No collisions, proceeding with organization...');
      // If no collisions, proceed with organization
      await performOrganization(customizationsData);
    } catch (err) {
      console.error('Organization error:', err);
      setError(err.message || 'Error during organization');
      setIsOrganizing(false);
      setTimeout(() => setError(null), 3000);
    }
  }, [selectedFiles, files, recommendations, selectedFolder]);

  const performOrganization = useCallback(async (customizationsData) => {
    try {
      const newHistory = [];
      const actions = [];
      let successCount = 0;

      // Build all actions first (don't execute yet)
      for (const fileIndex of selectedFiles) {
        const file = files[fileIndex];
        const recommendation = recommendations[fileIndex];
        if (!file || !recommendation) continue;

        let targetCategory = recommendation.fileType || recommendation.category;  // File type for logging
        let folderName = recommendation.folderName || recommendation.category;  // Metadata folder or category

        // Check for folder name customization (highest priority)
        if (customizationsData[recommendation.category]?.folderName) {
          folderName = customizationsData[recommendation.category].folderName;
        } else if (customizationsData[`file_${fileIndex}`]?.folderName) {
          folderName = customizationsData[`file_${fileIndex}`].folderName;
        }

        // Check for category customization
        if (customizationsData[`file_${fileIndex}`]?.newCategory) {
          targetCategory = customizationsData[`file_${fileIndex}`].newCategory;
          folderName = customizationsData[`file_${fileIndex}`].newCategory;  // Use custom category as folder name too
        }

        actions.push({
          filename: typeof file === 'string' ? file : file.name,
          filepath: typeof file === 'string' ? `${selectedFolder}/${file}` : file.path,
          target_category: targetCategory,
          custom_folder_name: folderName,  // ALWAYS use metadata folder name or customization
          confidence: recommendation.confidence,
          use_metadata: true,
        });

        newHistory.push({
          action: 'move',
          filename: typeof file === 'string' ? file : file.name,
          category: targetCategory,
          timestamp: new Date().toISOString(),
        });
      }

      // Execute all actions at once (MUCH FASTER - 4-5x speedup)
      if (actions.length > 0) {
        const result = await batchApplyActions(actions);
        
        // Update action IDs from response
        if (result.action_ids) {
          result.action_ids.forEach((id, idx) => {
            if (newHistory[idx]) {
              newHistory[idx].action_id = id;
            }
          });
        }
        
        successCount = result.successful || actions.length;
      }

      setActionHistory([...actionHistory, ...newHistory]);
      setOrganizationComplete(true);
      setSuccessMessage(`Successfully organized ${successCount} files`);
      
      // Show success popup with stats
      setSuccessStats({
        successCount: successCount,
        failedCount: result?.failed || 0
      });
      setShowSuccessPopup(true);
      setIsOrganizing(false);
      
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err) {
      setError(err.message || 'Error organizing files');
      setIsOrganizing(false);
      setTimeout(() => setError(null), 3000);
    }
  }, [selectedFiles, files, recommendations, selectedFolder, actionHistory]);

  const handleCollisionResolve = useCallback(async (collisionId, keepFilePath, action, newName) => {
    try {
      const result = await resolveCollision(collisionId, keepFilePath, action, newName);
      
      // Continue with organization after resolving collision
      const remainingCollisions = collisions.filter(c => c.collision_id !== collisionId);
      if (remainingCollisions.length === 0) {
        setShowCollisionModal(false);
        setCollisions([]);
        // Proceed with organization
        await performOrganization(customizations);
      } else {
        setCollisions(remainingCollisions);
      }
    } catch (err) {
      setError(err.message || 'Error resolving collision');
      setTimeout(() => setError(null), 3000);
    }
  }, [collisions, customizations]);

  const handleCollisionSkip = useCallback(() => {
    setShowCollisionModal(false);
    setCollisions([]);
    setIsOrganizing(false);
    setError('Organization cancelled due to file collisions');
    setTimeout(() => setError(null), 3000);
  }, []);

  const handleRandomNameRename = useCallback((oldName, newName) => {
    // Update the mapping
    setRenamedFiles(prev => ({
      ...prev,
      [oldName]: newName
    }));
    
    // Rename the file in files array
    const fileIndex = files.findIndex(f => (typeof f === 'string' ? f : f.name) === oldName);
    if (fileIndex >= 0) {
      const updatedFiles = [...files];
      if (typeof updatedFiles[fileIndex] === 'string') {
        updatedFiles[fileIndex] = newName;
      } else {
        updatedFiles[fileIndex] = { ...updatedFiles[fileIndex], name: newName };
      }
      setFiles(updatedFiles);
    }
    
    // Move to next random file or close modal
    const remainingQueue = randomNameQueue.slice(1);
    if (remainingQueue.length > 0) {
      setRandomNameQueue(remainingQueue);
      setCurrentRandomFile(remainingQueue[0]);
    } else {
      setShowRandomNameModal(false);
      setRandomNameQueue([]);
      setCurrentRandomFile(null);
    }
  }, [files, randomNameQueue]);

  const handleRandomNameSkip = useCallback(() => {
    // Move to next random file or close modal
    const remainingQueue = randomNameQueue.slice(1);
    if (remainingQueue.length > 0) {
      setRandomNameQueue(remainingQueue);
      setCurrentRandomFile(remainingQueue[0]);
    } else {
      setShowRandomNameModal(false);
      setRandomNameQueue([]);
      setCurrentRandomFile(null);
    }
  }, [randomNameQueue]);

  const handleUndo = useCallback(async () => {
    try {
      // Get current undo history to know how many actions to undo
      const historyResponse = await getUndoHistory();
      const totalActions = historyResponse.total_actions || 0;

      if (totalActions === 0) {
        setError('No actions to undo');
        setTimeout(() => setError(null), 3000);
        return;
      }

      // Undo all actions at once using batch undo
      const response = await batchUndoActions(totalActions, null);
      
      if (response.successful > 0) {
        setSuccessMessage(`Successfully undone all ${response.successful} change(s)`);
        if (response.failed > 0) {
          setError(`Failed to undo ${response.failed} file(s)`);
        }
      } else {
        setError('No files were undone');
      }
      
      setTimeout(() => {
        setSuccessMessage(null);
        setError(null);
      }, 3000);
      
      setActionHistory([]);
    } catch (err) {
      setError(err.message || 'Error undoing all changes');
      setTimeout(() => setError(null), 3000);
    }
  }, []);

  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(ext)) return 'image';
    if (['mp4', 'mov', 'avi', 'mkv'].includes(ext)) return 'video';
    if (['mp3', 'wav', 'flac', 'aac'].includes(ext)) return 'audio';
    if (['pdf'].includes(ext)) return 'pdf';
    if (['doc', 'docx', 'txt', 'rtf'].includes(ext)) return 'doc';
    if (['xls', 'xlsx', 'csv'].includes(ext)) return 'spreadsheet';
    if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return 'archive';
    return 'file';
  };

  return (
    <div className="organize-page">
      <header className="page-header">
        <h1>File Organizer</h1>
        <p>Select folder → Choose files → Organize instantly</p>
      </header>

      {/* History CTA */}
      <div className="history-cta">
        <div className="cta-content">
          <div className="cta-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
          <div className="cta-text">
            <h3>View History & Undo</h3>
            <p>Review, filter by date, and undo your file organization changes</p>
          </div>
          <button 
            className="cta-button"
            onClick={() => navigate('/history')}
          >
            Open History
          </button>
        </div>
      </div>

      {/* Messages */}
      {error && <div className="toast error">{error}</div>}
      {successMessage && <div className="toast success">{successMessage}</div>}

      <div className="organize-layout">
        {/* Folder Selection Section */}
        <section className="folder-section">
          <h2>Select Folder</h2>
          
          <div className="quick-folders">
            {quickFolders.map((folder) => (
              <button
                key={folder.id}
                className={`quick-folder-btn ${activeQuickFolder === folder.id ? 'active' : ''}`}
                onClick={() => handleQuickFolderSelect(folder)}
              >
                <div className="folder-icon">
                  {folder.icon === 'desktop' && (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
                      <line x1="8" y1="21" x2="16" y2="21"/>
                      <line x1="12" y1="17" x2="12" y2="21"/>
                    </svg>
                  )}
                  {folder.icon === 'documents' && (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                      <polyline points="14 2 14 8 20 8"/>
                      <line x1="16" y1="13" x2="8" y2="13"/>
                      <line x1="16" y1="17" x2="8" y2="17"/>
                    </svg>
                  )}
                  {folder.icon === 'downloads' && (
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                      <polyline points="7 10 12 15 17 10"/>
                      <line x1="12" y1="15" x2="12" y2="3"/>
                    </svg>
                  )}
                </div>
                <span>{folder.name}</span>
              </button>
            ))}
          </div>

          <div className="custom-folder">
            <label>Custom Folder Path</label>
            <div className="custom-folder-input">
              <input
                type="text"
                placeholder="/Users/pranil/Downloads"
                value={customFolder}
                onChange={(e) => setCustomFolder(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleCustomFolderSelect()}
              />
              <button 
                className="btn-select"
                onClick={handleCustomFolderSelect}
                disabled={!customFolder.trim()}
              >
                Select
              </button>
            </div>
          </div>

          {selectedFolder && (
            <div className="selected-path">
              <span className="path-label">Selected:</span>
              <span className="path-value">{selectedFolder}</span>
            </div>
          )}

          <button
            className="btn-scan"
            onClick={handleScanFolder}
            disabled={isLoading || !selectedFolder}
          >
            {isLoading ? 'Scanning...' : 'Scan Folder'}
          </button>
        </section>

        {/* Files Section */}
        <section className="files-section">
          <div className="files-header">
            <h2>Files {files.length > 0 && `(${files.length})`}</h2>
            {files.length > 0 && (
              <div className="files-actions">
                <button className="btn-text" onClick={handleSelectAll}>
                  {selectedFiles.size === files.length ? 'Deselect All' : 'Select All'}
                </button>
                <span className="selected-count">{selectedFiles.size} selected</span>
              </div>
            )}
          </div>

          <div className="files-grid">
            {files.length === 0 ? (
              <div className="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
                </svg>
                <p>Select a folder and click Scan to view files</p>
              </div>
            ) : (
              files.map((file, idx) => {
                const filename = typeof file === 'string' ? file : file.name;
                const recommendation = recommendations[idx];
                return (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '1rem',
                      padding: '12px 16px',
                      background: '#ffffff',
                      border: '1px solid #e5e7eb',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease'
                    }}
                    className={`file-card ${selectedFiles.has(idx) ? 'selected' : ''}`}
                    onClick={() => handleSelectFile(idx)}
                  >
                    <div className="file-checkbox">
                      <input
                        type="checkbox"
                        checked={selectedFiles.has(idx)}
                        onChange={() => handleSelectFile(idx)}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </div>
                    <div className="file-info" style={{ flex: 1, minWidth: 0, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
                      <span className="file-name" style={{ fontSize: '15px', fontWeight: '600', color: '#000000', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={filename}>
                        {filename || 'Unnamed File'}
                      </span>
                      {recommendation && (
                        <span className="file-category" style={{ fontSize: '12px', padding: '4px 12px', background: 'rgba(99, 102, 241, 0.2)', color: '#6366f1', borderRadius: '12px', whiteSpace: 'nowrap' }}>
                          {recommendation.category}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </section>

        {/* Action Section */}
        <section className="action-section">
          <div className="action-buttons">
            <button
              className="btn-organize"
              onClick={handleOrganize}
              disabled={isOrganizing || selectedFiles.size === 0}
            >
              {isOrganizing ? 'Organizing...' : `Organize ${selectedFiles.size} File${selectedFiles.size !== 1 ? 's' : ''}`}
            </button>
            
            {selectedFiles.size > 0 && !showCustomizationModal && (
              <button
                className="btn-customize"
                onClick={() => setShowCustomizationModal(true)}
              >
                ✎ Customize Before Organizing
              </button>
            )}
          </div>

          {actionHistory.length > 0 && (
            <button className="btn-undo" onClick={handleUndo}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="1 4 1 10 7 10"/>
                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
              </svg>
              Undo All Changes
            </button>
          )}

          {organizationComplete && (
            <div className="completion-message">
              Organization complete! {actionHistory.length} files organized.
            </div>
          )}
        </section>

        {/* Random Name Modal */}
        {showRandomNameModal && currentRandomFile && (
          <RandomNameModal
            file={currentRandomFile}
            isOpen={showRandomNameModal}
            onClose={() => setShowRandomNameModal(false)}
            onRename={handleRandomNameRename}
            onSkip={handleRandomNameSkip}
          />
        )}

        {/* Collision Modal */}
        {showCollisionModal && (
          <CollisionModal
            collisions={collisions}
            onResolve={handleCollisionResolve}
            onSkip={handleCollisionSkip}
          />
        )}

        {/* Customization Modal */}
        {showCustomizationModal && (
          <CustomizationModal
            files={Array.from(selectedFiles).map(idx => ({
              name: typeof files[idx] === 'string' ? files[idx] : files[idx].name,
              index: idx,
              category: recommendations[idx]?.category || 'Other'
            }))}
            recommendations={recommendations}
            selectedFiles={selectedFiles}
            onConfirm={handleCustomizationConfirm}
            onCancel={() => setShowCustomizationModal(false)}
          />
        )}

        {/* Success Popup */}
        <SuccessPopup
          isVisible={showSuccessPopup}
          successCount={successStats.successCount}
          failedCount={successStats.failedCount}
          onClose={() => setShowSuccessPopup(false)}
        />
      </div>
    </div>
  );
};

export default Organize;
