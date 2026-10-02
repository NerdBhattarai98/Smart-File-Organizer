import React, { useState } from 'react';
import '../styles/Duplicates.css';

function Duplicates() {
  const [duplicates, setDuplicates] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFolder, setSelectedFolder] = useState('');

  const handleScanDuplicates = async () => {
    if (!selectedFolder) {
      alert('Please select a folder');
      return;
    }

    setIsLoading(true);
    try {
      const scanResponse = await fetch('http://localhost:8000/api/scan-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: selectedFolder })
      });
      const scanData = await scanResponse.json();

      const duplicateResponse = await fetch('http://localhost:8000/api/detect-duplicates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ files: scanData.files })
      });
      const duplicateData = await duplicateResponse.json();
      setDuplicates(duplicateData.duplicate_groups || []);
    } catch (error) {
      console.error('Failed to scan duplicates:', error);
      alert('Failed to scan for duplicates');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="duplicates-container">
      <div className="page-header">
        <h1>Duplicate Detection</h1>
        <p>Find and manage duplicate files in your storage</p>
      </div>

      <div className="duplicates-content">
        <div className="scan-section">
          <div className="input-group">
            <input
              type="text"
              placeholder="Enter folder path..."
              value={selectedFolder}
              onChange={(e) => setSelectedFolder(e.target.value)}
              className="path-input"
            />
            <button 
              onClick={handleScanDuplicates}
              disabled={isLoading}
              className="btn-primary"
            >
              {isLoading ? 'Scanning...' : 'Scan for Duplicates'}
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="loading-state">
            <p>Scanning for duplicates...</p>
          </div>
        ) : duplicates.length === 0 ? (
          <div className="empty-state">
            <p>No duplicates found or no scan performed</p>
          </div>
        ) : (
          <div className="duplicates-list">
            <h2>Found {duplicates.length} Duplicate Groups</h2>
            {duplicates.map((group, index) => (
              <div key={index} className="duplicate-group">
                <div className="group-header">
                  <h3 className="group-title">{group.files[0]}</h3>
                  <span className="group-count">{group.files.length} copies</span>
                </div>
                <div className="group-files">
                  {group.files.map((file, fileIndex) => (
                    <div key={fileIndex} className="file-row">
                      <div className="file-info">
                        <div className="file-name">{file}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Duplicates;
