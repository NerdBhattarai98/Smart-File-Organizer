import React, { useState } from 'react';
import '../styles/Processing.css';

function Processing() {
  const [processing, setProcessing] = useState(false);
  const [folderPath, setFolderPath] = useState('');
  const [processResult, setProcessResult] = useState(null);
  const [progress, setProgress] = useState(0);
  const [currentFile, setCurrentFile] = useState('');

  const handleProcessFolder = async () => {
    if (!folderPath) {
      alert('Please enter a folder path');
      return;
    }

    setProcessing(true);
    setProgress(0);
    setProcessResult(null);

    try {
      const response = await fetch('http://localhost:8000/api/scan-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: folderPath })
      });

      const data = await response.json();
      
      if (data.files) {
        setProgress(50);
        setCurrentFile(`Processing ${data.files.length} files...`);
        
        const classifyResponse = await fetch('http://localhost:8000/api/classify-files', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ files: data.files })
        });

        const classifyData = await classifyResponse.json();
        setProgress(100);
        setCurrentFile('Processing complete');
        
        setProcessResult({
          filesFound: data.files.length,
          filesClassified: classifyData.classifications?.length || 0,
          timestamp: new Date().toLocaleString(),
          files: data.files.slice(0, 10)
        });
      }
    } catch (error) {
      setProcessResult({ error: error.message });
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="processing-container">
      <div className="page-header">
        <h1>File Processing</h1>
        <p>Scan and process files in a folder</p>
      </div>

      <div className="processing-content">
        <div className="input-section">
          <div className="input-group">
            <label>Folder Path</label>
            <input
              type="text"
              placeholder="/Users/username/Downloads"
              value={folderPath}
              onChange={(e) => setFolderPath(e.target.value)}
              disabled={processing}
              className="path-input"
            />
          </div>

          <button 
            className="btn-primary"
            onClick={handleProcessFolder}
            disabled={processing}
          >
            {processing ? 'Processing...' : 'Start Processing'}
          </button>
        </div>

        {processing && (
          <div className="progress-section">
            <div className="progress-info">
              <span className="file-name">{currentFile}</span>
              <span className="progress-percent">{progress}%</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }}></div>
            </div>
          </div>
        )}

        {processResult && !processing && (
          <div className="result-section">
            {processResult.error ? (
              <div className="error-message">
                <strong>Error:</strong> {processResult.error}
              </div>
            ) : (
              <>
                <div className="result-stats">
                  <div className="stat-card">
                    <div className="stat-label">Files Found</div>
                    <div className="stat-value">{processResult.filesFound}</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Files Classified</div>
                    <div className="stat-value">{processResult.filesClassified}</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Processed At</div>
                    <div className="stat-value-time">{processResult.timestamp}</div>
                  </div>
                </div>

                <div className="files-preview">
                  <h3>Files Found (Sample)</h3>
                  <ul className="file-list">
                    {processResult.files.map((file, idx) => (
                      <li key={idx} className="file-item">
                        <span className="file-name">{file}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default Processing;
