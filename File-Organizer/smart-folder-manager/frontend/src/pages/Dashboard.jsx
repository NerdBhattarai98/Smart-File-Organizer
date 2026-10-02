import React, { useState, useCallback } from 'react';
import FolderSelector from '../components/FolderSelector';
import FileList from '../components/FileList';
import RecommendationPanel from '../components/RecommendationPanel';
import ActionPanel from '../components/ActionPanel';
import UndoButton from '../components/UndoButton';
import { scanFolder, classifyFiles, detectDuplicates, applyAction, undoAction } from '../services/api';
import '../styles/Dashboard.css';

const Dashboard = () => {
  const [selectedFolder, setSelectedFolder] = useState(null);
  const [files, setFiles] = useState([]);
  const [currentFileIndex, setCurrentFileIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [recommendations, setRecommendations] = useState({});
  const [duplicates, setDuplicates] = useState({});
  const [progress, setProgress] = useState({ current: 0, total: 0, approved: 0, skipped: 0 });
  const [actionHistory, setActionHistory] = useState([]);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  const currentFile = files[currentFileIndex];
  const currentRecommendation = currentFile ? recommendations[currentFile.id] : null;
  const isDuplicate = currentFile ? duplicates[currentFile.id] : false;

  // Handle folder selection and scanning
  const handleFolderSelect = useCallback(async (folderPath) => {
    try {
      setIsLoading(true);
      setError(null);
      setSelectedFolder(folderPath);

      // Scan folder
      const scanResult = await scanFolder(folderPath);
      const scannedFiles = scanResult.files.map((file, index) => ({
        id: index,
        ...file,
      }));
      setFiles(scannedFiles);
      setProgress({ current: 0, total: scannedFiles.length, approved: 0, skipped: 0 });

      // Classify files
      const classifyResult = await classifyFiles(scannedFiles);
      const recommendationsMap = {};
      classifyResult.results.forEach((result, index) => {
        recommendationsMap[index] = {
          category: result.predicted_category,
          confidence: result.confidence,
          suggestedPath: `/Organized/${result.predicted_category}/${result.filename}`,
        };
      });
      setRecommendations(recommendationsMap);

      // Detect duplicates
      const duplicateResult = await detectDuplicates(scannedFiles);
      const duplicatesMap = {};
      // Mark files that are in duplicate groups
      duplicateResult.duplicate_groups.forEach((group) => {
        group.files.forEach((filename) => {
          const fileIndex = scannedFiles.findIndex(f => f.name === filename);
          if (fileIndex >= 0) {
            duplicatesMap[fileIndex] = true;
          }
        });
      });
      setDuplicates(duplicatesMap);

      setCurrentFileIndex(0);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Approve and move file
  const handleApprove = useCallback(async (file) => {
    try {
      setIsProcessing(true);
      const recommendation = recommendations[file.id];

      if (!recommendation || !recommendation.suggestedPath) {
        setError('No recommendation available for this file');
        return;
      }

      await applyAction({
        filename: file.name,
        filepath: file.path,
        target_category: recommendation.category,
        confidence: recommendation.confidence,
        timestamp: new Date().toISOString(),
      });

      setSuccessMessage(`✓ ${file.name} moved to ${recommendation.category}`);
      setProgress(prev => ({
        ...prev,
        current: prev.current + 1,
        approved: prev.approved + 1,
      }));

      // Update action history tracking
      setActionHistory(prev => [...prev, { file_id: file.id, action: 'MOVED', timestamp: new Date() }]);

      moveToNextFile();
    } catch (err) {
      setError(`Failed to move file: ${err.message}`);
    } finally {
      setIsProcessing(false);
    }
  }, [recommendations]);

  // Skip file
  const handleSkip = useCallback(async (file) => {
    try {
      setProgress(prev => ({
        ...prev,
        current: prev.current + 1,
        skipped: prev.skipped + 1,
      }));
      moveToNextFile();
    } catch (err) {
      setError(`Failed to skip file: ${err.message}`);
    }
  }, []);

  // Move to next file
  const moveToNextFile = () => {
    if (currentFileIndex < files.length - 1) {
      setCurrentFileIndex(currentFileIndex + 1);
    } else {
      setSuccessMessage('✓ All files processed!');
    }
  };

  // Undo last action
  const handleUndo = useCallback(async () => {
    try {
      const result = await undoAction({});
      setSuccessMessage(`✓ Undo successful: ${result.restored_file.name}`);
      setProgress(prev => ({
        ...prev,
        approved: Math.max(0, prev.approved - 1),
      }));
      return result;
    } catch (err) {
      setError(`Failed to undo: ${err.message}`);
    }
  }, []);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>📁 Smart File Organizer</h1>
        <p>Intelligent file classification and organization</p>
      </header>

      {error && (
        <div className="alert alert-error">
          <span className="alert-icon">✕</span>
          {error}
          <button onClick={() => setError(null)} className="alert-close">×</button>
        </div>
      )}

      {successMessage && (
        <div className="alert alert-success">
          <span className="alert-icon">✓</span>
          {successMessage}
          <button onClick={() => setSuccessMessage(null)} className="alert-close">×</button>
        </div>
      )}

      <div className="dashboard-container">
        <aside className="sidebar">
          <FolderSelector onFolderSelect={handleFolderSelect} isLoading={isLoading} />
          <UndoButton onUndo={handleUndo} hasActions={actionHistory.length > 0} />
        </aside>

        <main className="main-content">
          <div className="content-grid">
            <div className="file-panel">
              <FileList 
                files={files} 
                currentIndex={currentFileIndex}
                onFileSelect={setCurrentFileIndex}
                duplicates={duplicates}
                loading={isLoading}
              />
            </div>

            <div className="recommendation-panel-wrapper">
              <RecommendationPanel
                file={currentFile}
                recommendation={currentRecommendation}
                isDuplicate={isDuplicate}
                onApprove={handleApprove}
                onSkip={handleSkip}
                isProcessing={isProcessing}
              />
            </div>
          </div>

          <div className="action-panel-wrapper">
            <ActionPanel
              onApprove={() => handleApprove(currentFile)}
              onSkip={() => handleSkip(currentFile)}
              disabled={isProcessing || !currentFile}
              currentIndex={currentFileIndex}
              totalFiles={files.length}
            />
          </div>
        </main>
      </div>
    </div>
  );
};

export default Dashboard;
