import React, { useState, useEffect } from 'react';
import { getUndoHistory, undoSpecificAction, batchUndoActions } from '../services/api';
import '../styles/UndoHistory.css';

const UndoHistory = ({ historyData }) => {
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [selectedActions, setSelectedActions] = useState(new Set());
  const [selectedDate, setSelectedDate] = useState('');
  const [filteredHistory, setFilteredHistory] = useState([]);
  const [viewMore, setViewMore] = useState(false);
  const ITEMS_PER_PAGE = 5;
  const MAX_ITEMS = 35;

  useEffect(() => {
    // Use data from parent if provided, otherwise load it
    if (historyData && historyData.length > 0) {
      setHistory(historyData);
    } else {
      loadHistory();
    }
  }, [historyData]);

  useEffect(() => {
    // Filter history by date when selectedDate changes
    if (selectedDate) {
      const filtered = history.filter(action => {
        const actionDate = action.timestamp?.split('T')[0]; // Get YYYY-MM-DD
        return actionDate === selectedDate;
      });
      setFilteredHistory(filtered);
    } else {
      setFilteredHistory(history);
    }
    setSelectedActions(new Set());
    setViewMore(false);
  }, [selectedDate, history]);

  const loadHistory = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await getUndoHistory();
      setHistory(response.actions || []);
    } catch (err) {
      setError(err.message || 'Failed to load undo history');
      setTimeout(() => setError(null), 3000);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUndo = async (actionId) => {
    try {
      setError(null);
      await undoSpecificAction(actionId);
      setSuccess('Action undone successfully');
      setTimeout(() => setSuccess(null), 3000);
      // Reload history after successful undo
      loadHistory();
    } catch (err) {
      setError(err.message || 'Failed to undo action');
      setTimeout(() => setError(null), 3000);
    }
  };

  const handleSelectAction = (actionId) => {
    const newSelected = new Set(selectedActions);
    if (newSelected.has(actionId)) {
      newSelected.delete(actionId);
    } else {
      newSelected.add(actionId);
    }
    setSelectedActions(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedActions.size === filteredHistory.length) {
      setSelectedActions(new Set());
    } else {
      setSelectedActions(new Set(filteredHistory.map(a => a.id)));
    }
  };

  const handleUndoAll = async () => {
    const targetHistory = selectedDate ? filteredHistory : history;
    
    if (targetHistory.length === 0) {
      setError(selectedDate ? 'No files organized on this date' : 'No actions to undo');
      setTimeout(() => setError(null), 3000);
      return;
    }

    try {
      setError(null);
      // Undo all actions by using count parameter
      const response = await batchUndoActions(targetHistory.length, null);
      
      if (response.successful > 0) {
        setSuccess(`Successfully undone ${response.successful} change(s)${selectedDate ? ` from ${selectedDate}` : ''}`);
        if (response.failed > 0) {
          setError(`Failed to undo ${response.failed} file(s)`);
        }
      } else {
        setError('No files were undone');
      }
      
      setTimeout(() => setSuccess(null), 3000);
      setSelectedActions(new Set());
      setSelectedDate('');
      loadHistory();
    } catch (err) {
      setError(err.message || 'Failed to undo all changes');
      setTimeout(() => setError(null), 3000);
    }
  };

  const handleBatchUndo = async () => {
    if (selectedActions.size === 0) {
      setError('Please select files to undo');
      setTimeout(() => setError(null), 3000);
      return;
    }

    try {
      setError(null);
      const actionIds = Array.from(selectedActions);
      const response = await batchUndoActions(1, actionIds);
      
      if (response.successful > 0) {
        setSuccess(`Successfully undone ${response.successful} file(s)`);
        if (response.failed > 0) {
          setError(`Failed to undo ${response.failed} file(s)`);
        }
      } else {
        setError('No files were undone');
      }
      
      setTimeout(() => setSuccess(null), 3000);
      setSelectedActions(new Set());
      // Reload history after successful undo
      loadHistory();
    } catch (err) {
      setError(err.message || 'Failed to batch undo actions');
      setTimeout(() => setError(null), 3000);
    }
  };

  const getFileIcon = (filename) => {
    const ext = filename.split('.').pop()?.toLowerCase();
    if (['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'].includes(ext)) return '🖼️';
    if (['mp4', 'mov', 'avi', 'mkv'].includes(ext)) return '🎬';
    if (['mp3', 'wav', 'flac', 'aac'].includes(ext)) return '🎵';
    if (['pdf'].includes(ext)) return '📄';
    if (['doc', 'docx', 'txt', 'rtf'].includes(ext)) return '📝';
    if (['xls', 'xlsx', 'csv'].includes(ext)) return '📊';
    if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return '📦';
    return '📁';
  };

  const formatDate = (timestamp) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const getFolderName = (path) => {
    return path?.split('/')?.pop() || 'Unknown';
  };

  return (
    <div className="undo-history">
      <div className="history-header">
        <h2>Undo History</h2>
        <button 
          className="btn-refresh"
          onClick={loadHistory}
          disabled={isLoading}
        >
          {isLoading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {error && <div className="toast error">{error}</div>}
      {success && <div className="toast success">{success}</div>}

      {/* Date Filter Section */}
      <div className="date-filter-section">
        <label htmlFor="date-filter">Filter by Date:</label>
        <input
          id="date-filter"
          type="date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          className="date-input"
        />
        {selectedDate && (
          <button
            className="btn-clear-filter"
            onClick={() => setSelectedDate('')}
          >
            Clear Filter
          </button>
        )}
      </div>

      {isLoading && <div className="loading">Loading history...</div>}

      {!isLoading && history.length === 0 && (
        <div className="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
          <p>No actions available to undo</p>
        </div>
      )}

      {!isLoading && history.length > 0 && filteredHistory.length === 0 && selectedDate && (
        <div className="empty-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
          <p>No files organized on {selectedDate}</p>
        </div>
      )}

      {!isLoading && filteredHistory.length > 0 && (
        <>
          <div className="batch-controls">
            <div className="controls-left">
              <button
                className="btn-undo-all"
                onClick={handleUndoAll}
                title="Undo all changes at once"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="1 4 1 10 7 10"/>
                  <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
                </svg>
                Undo All Changes
              </button>
            </div>
            <div className="controls-right">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={selectedActions.size === filteredHistory.length && filteredHistory.length > 0}
                  onChange={handleSelectAll}
                />
                <span>Select All</span>
              </label>
              {selectedActions.size > 0 && (
                <span className="selection-count">{selectedActions.size} selected</span>
              )}
              {selectedActions.size > 0 && (
                <button
                  className="btn-batch-undo"
                  onClick={handleBatchUndo}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="1 4 1 10 7 10"/>
                    <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
                  </svg>
                  Undo {selectedActions.size} File{selectedActions.size !== 1 ? 's' : ''}
                </button>
              )}
            </div>
          </div>

          {/* View More Button */}
          {filteredHistory.length > ITEMS_PER_PAGE && !viewMore && (
            <div className="view-more-section">
              <p className="items-info">
                Showing {Math.min(ITEMS_PER_PAGE, filteredHistory.length)} of {Math.min(filteredHistory.length, MAX_ITEMS)} items
              </p>
              <button
                className="btn-view-more"
                onClick={() => setViewMore(true)}
              >
                View More ({filteredHistory.length - ITEMS_PER_PAGE} more)
              </button>
            </div>
          )}

          <div className="history-list">
            {filteredHistory.slice(0, viewMore ? MAX_ITEMS : ITEMS_PER_PAGE).map((action, idx) => (
              <div 
                key={action.id} 
                className={`history-item ${!action.can_undo ? 'disabled' : ''}`}
              >
                <div className="item-checkbox">
                  <input
                    type="checkbox"
                    checked={selectedActions.has(action.id)}
                    onChange={() => handleSelectAction(action.id)}
                    disabled={!action.can_undo}
                  />
                </div>
                <div className="item-info">
                  <div className="item-header">
                    <span className="file-icon">{getFileIcon(action.filename)}</span>
                    <span className="file-name">{action.filename}</span>
                    {!action.can_undo && <span className="badge-unavailable">File Not Found</span>}
                  </div>
                  <div className="item-paths">
                    <div className="path-group">
                      <span className="path-label">From:</span>
                      <span className="path-value" title={action.from_path}>
                        {getFolderName(action.from_path)}
                      </span>
                    </div>
                    <svg className="arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <line x1="5" y1="12" x2="19" y2="12"/>
                      <polyline points="12 5 19 12 12 19"/>
                    </svg>
                    <div className="path-group">
                      <span className="path-label">To:</span>
                      <span className="path-value" title={action.to_path}>
                        {getFolderName(action.to_path)}
                      </span>
                    </div>
                  </div>
                  <div className="item-meta">
                    <span className="timestamp">
                      {formatDate(action.timestamp)}
                    </span>
                  </div>
                </div>
                <button
                  className="btn-undo-item"
                  onClick={() => handleUndo(action.id)}
                  disabled={!action.can_undo}
                  title={!action.can_undo ? 'File not found' : 'Undo this action'}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="1 4 1 10 7 10"/>
                    <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
                  </svg>
                  Undo
                </button>
              </div>
            ))}
          </div>

          {/* View Less Button */}
          {viewMore && filteredHistory.length > ITEMS_PER_PAGE && (
            <button
              className="btn-view-less"
              onClick={() => setViewMore(false)}
            >
              Show Less
            </button>
          )}
        </>
      )}
    </div>
  );
};

export default UndoHistory;
