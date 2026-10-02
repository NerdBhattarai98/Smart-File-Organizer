import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import UndoHistory from '../components/UndoHistory';
import '../styles/History.css';

function History() {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [viewMore, setViewMore] = useState(false);
  const ITEMS_PER_PAGE = 5;
  const MAX_ITEMS = 25;

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/history');
        const data = await response.json();
        setHistory(data.actions || []);
      } catch (error) {
        console.error('Failed to fetch history:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchHistory();
    
    // Poll for new history every 2 seconds to sync with organization
    const pollInterval = setInterval(fetchHistory, 2000);
    
    return () => clearInterval(pollInterval);
  }, []);

  const handleClearHistory = async () => {
    if (window.confirm('Are you sure you want to clear all history?')) {
      try {
        await fetch('http://localhost:8000/api/history/clear', { method: 'DELETE' });
        setHistory([]);
      } catch (error) {
        console.error('Failed to clear history:', error);
      }
    }
  };

  return (
    <div className="history-container">
      <div className="page-header">
        <h1>Action History</h1>
        <p>View and manage all file organization actions</p>
      </div>

      <div className="history-cta-banner">
        <div className="history-cta-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
        </div>
        <div className="history-cta-text">
          <h3>View History & Undo</h3>
          <p>Review, filter by date, and undo your file organization changes</p>
        </div>
        <button className="history-cta-btn" onClick={() => navigate('/organize')}>
          Go To Organizer
        </button>
      </div>

      <div className="history-content">
        <div className="undo-history-section">
          <UndoHistory historyData={history} />
        </div>

        <div className="action-log-section">
          <div className="section-header">
            <h2>Action Log</h2>
            {history.length > 0 && (
              <button className="btn-danger" onClick={handleClearHistory}>
                Clear History
              </button>
            )}
          </div>

          {isLoading ? (
            <div className="loading-state">
              <p>Loading history...</p>
            </div>
          ) : history.length === 0 ? (
            <div className="empty-state">
              <p>No actions recorded yet</p>
            </div>
          ) : (
            <div className="history-table">
              <div className="table-header">
                <div className="table-cell">Filename</div>
                <div className="table-cell">Action</div>
                <div className="table-cell">Category</div>
                <div className="table-cell">Timestamp</div>
              </div>

              {/* View More Button */}
              {history.length > ITEMS_PER_PAGE && !viewMore && (
                <div className="view-more-section-table">
                  <p className="items-info-table">
                    Showing {Math.min(ITEMS_PER_PAGE, history.length)} of {Math.min(history.length, MAX_ITEMS)} items
                  </p>
                  <button
                    className="btn-view-more-table"
                    onClick={() => setViewMore(true)}
                  >
                    View More ({history.length - ITEMS_PER_PAGE} more)
                  </button>
                </div>
              )}

              {history.slice(0, viewMore ? MAX_ITEMS : ITEMS_PER_PAGE).reverse().map((action, index) => (
                <div key={index} className="table-row">
                  <div className="table-cell">{action.filename}</div>
                  <div className="table-cell">
                    <span className="action-badge">{action.type}</span>
                  </div>
                  <div className="table-cell">{action.category || 'N/A'}</div>
                  <div className="table-cell">
                    {new Date(action.timestamp).toLocaleString()}
                  </div>
                </div>
              ))}

              {/* View Less Button */}
              {viewMore && history.length > ITEMS_PER_PAGE && (
                <button
                  className="btn-view-less-table"
                  onClick={() => setViewMore(false)}
                >
                  Show Less
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default History;
