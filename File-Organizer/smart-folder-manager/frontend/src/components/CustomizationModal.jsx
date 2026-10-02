import React, { useState, useMemo } from 'react';
import '../styles/CustomizationModal.css';

const CustomizationModal = ({ files, recommendations, onConfirm, onCancel }) => {
  const [customizations, setCustomizations] = useState({});
  const [activeTab, setActiveTab] = useState('folders');

  // Group files by category
  const filesByCategory = useMemo(() => {
    const grouped = {};
    files.forEach((file, idx) => {
      if (recommendations[idx]) {
        const category = recommendations[idx].category;
        if (!grouped[category]) {
          grouped[category] = [];
        }
        grouped[category].push({ idx, filename: typeof file === 'string' ? file : file.name });
      }
    });
    return grouped;
  }, [files, recommendations]);

  const handleFolderNameChange = (category, newName) => {
    setCustomizations(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        folderName: newName,
      }
    }));
  };

  const handleCategoryChange = (fileIdx, newCategory) => {
    setCustomizations(prev => ({
      ...prev,
      [`file_${fileIdx}`]: {
        ...prev[`file_${fileIdx}`],
        newCategory: newCategory,
      }
    }));
  };

  const handleConfirm = () => {
    onConfirm(customizations);
  };

  const categories = Object.keys(filesByCategory);

  return (
    <div className="customization-modal-overlay">
      <div className="customization-modal">
        <div className="modal-header">
          <h2>Customize Before Organizing</h2>
          <button className="btn-close" onClick={onCancel}>×</button>
        </div>

        <div className="modal-tabs">
          <button
            className={`tab-button ${activeTab === 'folders' ? 'active' : ''}`}
            onClick={() => setActiveTab('folders')}
          >
            Rename Folders ({categories.length})
          </button>
          <button
            className={`tab-button ${activeTab === 'categories' ? 'active' : ''}`}
            onClick={() => setActiveTab('categories')}
          >
            Recategorize Files ({files.length})
          </button>
        </div>

        <div className="modal-content">
          {activeTab === 'folders' && (
            <div className="folder-customization">
              <div className="customization-list">
                {categories.map(category => (
                  <div key={category} className="customization-item">
                    <div className="item-label">
                      <span className="original-name">{category}</span>
                      <span className="file-count">{filesByCategory[category].length} files</span>
                    </div>
                    <input
                      type="text"
                      className="customization-input"
                      placeholder={`Rename "${category}" to...`}
                      value={customizations[category]?.folderName || ''}
                      onChange={(e) => handleFolderNameChange(category, e.target.value)}
                    />
                    {customizations[category]?.folderName && (
                      <span className="preview">→ {customizations[category].folderName}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'categories' && (
            <div className="file-recategorization">
              <div className="customization-list">
                {files.map((file, idx) => {
                  const filename = typeof file === 'string' ? file : file.name;
                  const currentCategory = recommendations[idx]?.category || 'Uncategorized';
                  const newCategory = customizations[`file_${idx}`]?.newCategory;
                  
                  return (
                    <div key={idx} className="customization-item">
                      <div className="item-label">
                        <span className="file-name-label">{filename}</span>
                      </div>
                      <div className="category-selector">
                        <span className="current-category">{newCategory || currentCategory}</span>
                        <select
                          className="category-dropdown"
                          value={newCategory || currentCategory}
                          onChange={(e) => handleCategoryChange(idx, e.target.value)}
                        >
                          <option value={currentCategory}>{currentCategory}</option>
                          {['Images', 'Videos', 'Documents', 'Audio', 'Archives', 'Applications', 'Other'].map(cat => (
                            <option key={cat} value={cat}>{cat}</option>
                          ))}
                        </select>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button className="btn-cancel" onClick={onCancel}>Cancel</button>
          <button className="btn-confirm" onClick={handleConfirm}>
            Proceed with Customizations
          </button>
        </div>
      </div>
    </div>
  );
};

export default CustomizationModal;
