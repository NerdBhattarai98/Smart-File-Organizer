import React from 'react';
import '../styles/RecommendationPanel.css';

function RecommendationPanel({ recommendation, currentFile, duplicates, loading }) {
  if (!currentFile || !recommendation) {
    return (
      <div className="recommendation-panel empty">
        <div className="empty-state">
          <div className="empty-icon">🎯</div>
          <h3>No Recommendation</h3>
          <p>Loading or select a file...</p>
        </div>
      </div>
    );
  }

  const confidencePercent = (recommendation.confidence * 100).toFixed(1);
  
  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'high';
    if (confidence >= 0.6) return 'medium';
    return 'low';
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 0.8) return 'High Confidence';
    if (confidence >= 0.6) return 'Medium Confidence';
    return 'Low Confidence';
  };

  return (
    <div className="recommendation-panel">
      <div className="panel-header">
        <h3>AI Recommendation</h3>
        <p className="file-name">{currentFile.name}</p>
      </div>

      {duplicates && (
        <div className="warning-badge">
          <span className="warning-icon">⚠️</span>
          <div className="warning-content">
            <strong>Duplicates Found</strong>
            <p>{duplicates.files.length} similar files detected</p>
          </div>
        </div>
      )}

      <div className="recommendation-content">
        <div className="recommendation-item">
          <div className="label">Predicted Category</div>
          <div className={`value category-badge category-${recommendation.predicted_category.toLowerCase().replace(/\s+/g, '-')}`}>
            {recommendation.predicted_category}
          </div>
        </div>

        <div className="recommendation-item">
          <div className="label">Confidence Score</div>
          <div className="confidence-container">
            <div className="confidence-bar">
              <div
                className={`confidence-fill ${getConfidenceColor(recommendation.confidence)}`}
                style={{ width: `${confidencePercent}%` }}
              ></div>
            </div>
            <div className="confidence-info">
              <div className="confidence-text">{confidencePercent}%</div>
              <div className="confidence-label">{getConfidenceLabel(recommendation.confidence)}</div>
            </div>
          </div>
        </div>

        {recommendation.similar_files && recommendation.similar_files.length > 0 && (
          <div className="recommendation-item">
            <div className="label">Similar Files ({recommendation.similar_files.length})</div>
            <div className="similar-files">
              {recommendation.similar_files.slice(0, 3).map((file, idx) => (
                <div key={idx} className="similar-file-tag">
                  {file}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {duplicates && (
        <div className="collision-info">
          <p className="collision-label">⚠️ Collision Warning</p>
          <p className="collision-text">Similar file(s) already exist. Review duplicates before moving.</p>
        </div>
      )}
    </div>
  );
}

export default RecommendationPanel;
