import React, { useState } from 'react';
import '../styles/Classification.css';

function Classification() {
  const [files, setFiles] = useState([]);
  const [folderPath, setFolderPath] = useState('');
  const [classifying, setClassifying] = useState(false);
  const [results, setResults] = useState([]);
  const [stats, setStats] = useState(null);

  const handleScanForClassification = async () => {
    if (!folderPath) {
      alert('Please enter a folder path');
      return;
    }

    setClassifying(true);
    try {
      const scanResponse = await fetch('http://localhost:8000/api/scan-folder', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ folder_path: folderPath })
      });

      const scanData = await scanResponse.json();
      setFiles(scanData.files || []);

      const classifyResponse = await fetch('http://localhost:8000/api/classify-files', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ files: scanData.files })
      });

      const classifyData = await classifyResponse.json();
      const classifications = classifyData.classifications || [];
      
      setResults(classifications);

      const categoryCounts = {};
      classifications.forEach(item => {
        const category = item.category || 'Unknown';
        categoryCounts[category] = (categoryCounts[category] || 0) + 1;
      });

      setStats({
        totalFiles: classifications.length,
        categories: categoryCounts,
        timestamp: new Date().toLocaleString()
      });
    } catch (error) {
      alert('Error classifying files: ' + error.message);
    } finally {
      setClassifying(false);
    }
  };

  return (
    <div className="classification-container">
      <div className="page-header">
        <h1>File Classification</h1>
        <p>Classify files by type and category using AI</p>
      </div>

      <div className="classification-content">
        <div className="scan-section">
          <div className="input-group">
            <label>Folder Path</label>
            <input
              type="text"
              placeholder="/Users/username/Downloads"
              value={folderPath}
              onChange={(e) => setFolderPath(e.target.value)}
              disabled={classifying}
              className="path-input"
            />
          </div>

          <button 
            className="btn-primary"
            onClick={handleScanForClassification}
            disabled={classifying}
          >
            {classifying ? 'Classifying...' : 'Classify Files'}
          </button>
        </div>

        {stats && (
          <div className="stats-section">
            <div className="stats-header">Classification Results</div>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-label">Total Files</div>
                <div className="stat-value">{stats.totalFiles}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Categories Found</div>
                <div className="stat-value">{Object.keys(stats.categories).length}</div>
              </div>
              <div className="stat-card">
                <div className="stat-label">Processed At</div>
                <div className="stat-value-time">{stats.timestamp}</div>
              </div>
            </div>

            <div className="categories-section">
              <h3>Categories Breakdown</h3>
              <div className="category-list">
                {Object.entries(stats.categories).map(([category, count]) => (
                  <div key={category} className="category-item">
                    <span className="category-name">{category}</span>
                    <span className="category-count">{count} files</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {results.length > 0 && (
          <div className="results-section">
            <h3>Detailed Classifications</h3>
            <div className="classifications-table">
              <div className="table-header">
                <div className="header-cell">Filename</div>
                <div className="header-cell">Category</div>
                <div className="header-cell">Confidence</div>
              </div>
              <div className="table-body">
                {results.map((result, idx) => (
                  <div key={idx} className="table-row">
                    <div className="cell">{result.filename || 'Unknown'}</div>
                    <div className="cell"><span className="badge">{result.category || 'Unknown'}</span></div>
                    <div className="cell">
                      <div className="confidence-bar">
                        <div className="confidence-fill" style={{ width: `${(result.confidence || 0) * 100}%` }}></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {!stats && files.length === 0 && (
          <div className="empty-state">
            <p>Enter a folder path and click "Classify Files" to begin</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default Classification;
