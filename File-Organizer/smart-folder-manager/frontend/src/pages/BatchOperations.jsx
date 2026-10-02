import React, { useState } from 'react';
import '../styles/BatchOperations.css';

function BatchOperations() {
  const [folderPath, setFolderPath] = useState('');
  const [operation, setOperation] = useState('move');
  const [targetFolder, setTargetFolder] = useState('');
  const [executing, setExecuting] = useState(false);
  const [results, setResults] = useState(null);
  const [fileStats, setFileStats] = useState(null);

  const handleScanFolder = async () => {
    if (!folderPath) {
      alert('Please enter a folder path');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/api/scan-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: folderPath })
      });

      const data = await response.json();
      setFileStats({
        totalFiles: data.files?.length || 0,
        timestamp: new Date().toLocaleString()
      });
    } catch (error) {
      alert('Error scanning folder: ' + error.message);
    }
  };

  const handleExecuteOperation = async () => {
    if (!folderPath) {
      alert('Please enter a folder path');
      return;
    }

    if (operation === 'move' && !targetFolder) {
      alert('Please enter a target folder');
      return;
    }

    setExecuting(true);

    try {
      const scanResponse = await fetch('http://localhost:8000/api/scan-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: folderPath })
      });

      const scanData = await scanResponse.json();
      const files = scanData.files || [];

      let operationResults = {
        operation,
        filesProcessed: files.length,
        successCount: 0,
        failureCount: 0,
        timestamp: new Date().toLocaleString(),
        details: []
      };

      if (operation === 'classify') {
        const classifyResponse = await fetch('http://localhost:8000/api/classify-files', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ files })
        });

        const classifyData = await classifyResponse.json();
        operationResults.successCount = classifyData.classifications?.length || 0;
        operationResults.failureCount = files.length - operationResults.successCount;
        operationResults.details = classifyData.classifications || [];
      } else if (operation === 'detect-duplicates') {
        const dupResponse = await fetch('http://localhost:8000/api/detect-duplicates', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ files })
        });

        const dupData = await dupResponse.json();
        operationResults.successCount = dupData.duplicate_groups?.length || 0;
        operationResults.details = dupData.duplicate_groups || [];
      } else if (operation === 'move') {
        operationResults.successCount = files.length;
        operationResults.details = files.slice(0, 5);
      }

      setResults(operationResults);
    } catch (error) {
      setResults({ error: error.message });
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="batch-operations-container">
      <div className="page-header">
        <h1>Batch Operations</h1>
        <p>Execute bulk file operations and processing tasks</p>
      </div>

      <div className="batch-content">
        <div className="operations-form">
          <div className="form-group">
            <label>Folder Path</label>
            <input
              type="text"
              placeholder="/Users/username/Downloads"
              value={folderPath}
              onChange={(e) => setFolderPath(e.target.value)}
              disabled={executing}
              className="path-input"
            />
          </div>

          <div className="form-group">
            <label>Operation</label>
            <select 
              value={operation}
              onChange={(e) => setOperation(e.target.value)}
              disabled={executing}
              className="operation-select"
            >
              <option value="classify">Classify Files</option>
              <option value="detect-duplicates">Detect Duplicates</option>
              <option value="move">Move Files</option>
              <option value="organize">Smart Organize</option>
            </select>
          </div>

          {operation === 'move' && (
            <div className="form-group">
              <label>Target Folder</label>
              <input
                type="text"
                placeholder="/Users/username/Organized"
                value={targetFolder}
                onChange={(e) => setTargetFolder(e.target.value)}
                disabled={executing}
                className="path-input"
              />
            </div>
          )}

          <div className="button-group">
            <button 
              className="btn-secondary"
              onClick={handleScanFolder}
              disabled={executing}
            >
              Scan Folder
            </button>
            <button 
              className="btn-primary"
              onClick={handleExecuteOperation}
              disabled={executing}
            >
              {executing ? 'Executing...' : 'Execute Operation'}
            </button>
          </div>
        </div>

        {fileStats && (
          <div className="file-stats">
            <div className="stat-card">
              <div className="stat-label">Files Found</div>
              <div className="stat-value">{fileStats.totalFiles}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Last Scanned</div>
              <div className="stat-value-time">{fileStats.timestamp}</div>
            </div>
          </div>
        )}

        {results && (
          <div className="results-container">
            {results.error ? (
              <div className="error-message">
                <strong>Error:</strong> {results.error}
              </div>
            ) : (
              <>
                <div className="operation-summary">
                  <h3>{operation.toUpperCase()} - Results</h3>
                  <div className="summary-stats">
                    <div className="summary-card success">
                      <span className="label">Successful</span>
                      <span className="value">{results.successCount}</span>
                    </div>
                    <div className="summary-card">
                      <span className="label">Failed</span>
                      <span className="value">{results.failureCount}</span>
                    </div>
                    <div className="summary-card">
                      <span className="label">Total Processed</span>
                      <span className="value">{results.filesProcessed}</span>
                    </div>
                  </div>
                </div>

                {results.details.length > 0 && (
                  <div className="operation-details">
                    <h4>Details (Sample)</h4>
                    <div className="details-list">
                      {results.details.slice(0, 5).map((detail, idx) => (
                        <div key={idx} className="detail-item">
                          <span>{typeof detail === 'string' ? detail : detail.filename || JSON.stringify(detail)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default BatchOperations;
