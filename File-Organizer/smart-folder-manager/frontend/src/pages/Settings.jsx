import React, { useState, useEffect } from 'react';
import '../styles/Settings.css';

function Settings() {
  const [settings, setSettings] = useState({
    useMetadata: true,
    autoClassify: true,
    showNotifications: true,
    defaultFolder: localStorage.getItem('defaultFolder') || ''
  });

  const [saved, setSaved] = useState(false);

  const handleToggle = (key) => {
    setSettings(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleInputChange = (e) => {
    setSettings(prev => ({
      ...prev,
      defaultFolder: e.target.value
    }));
  };

  const handleSaveSettings = () => {
    localStorage.setItem('settings', JSON.stringify(settings));
    localStorage.setItem('defaultFolder', settings.defaultFolder);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const handleResetSettings = () => {
    if (window.confirm('Reset all settings to default?')) {
      const defaultSettings = {
        useMetadata: true,
        autoClassify: true,
        showNotifications: true,
        defaultFolder: ''
      };
      setSettings(defaultSettings);
      localStorage.removeItem('settings');
      localStorage.removeItem('defaultFolder');
    }
  };

  return (
    <div className="settings-container">
      <div className="page-header">
        <h1>Settings</h1>
        <p>Configure application preferences and behavior</p>
      </div>

      {saved && <div className="success-message">Settings saved successfully</div>}

      <div className="settings-content">
        <div className="settings-section">
          <div className="section-header">
            <h2>Organization Preferences</h2>
            <p>Configure how files are organized</p>
          </div>
          <div className="section-body">
            <div className="setting-item">
              <label className="setting-label">Use Metadata-Based Naming</label>
              <p className="setting-description">
                Create folders based on filename patterns (e.g., screenshot_1234 creates a 'screenshot' folder)
              </p>
              <div className="toggle-container">
                <button
                  className={`toggle-switch ${settings.useMetadata ? 'active' : ''}`}
                  onClick={() => handleToggle('useMetadata')}
                >
                  <span className="toggle-slider"></span>
                </button>
              </div>
            </div>

            <div className="setting-item">
              <label className="setting-label">Auto-Classify Files</label>
              <p className="setting-description">
                Automatically apply machine learning classification to files
              </p>
              <div className="toggle-container">
                <button
                  className={`toggle-switch ${settings.autoClassify ? 'active' : ''}`}
                  onClick={() => handleToggle('autoClassify')}
                >
                  <span className="toggle-slider"></span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="settings-section">
          <div className="section-header">
            <h2>Notifications</h2>
            <p>Control notification preferences</p>
          </div>
          <div className="section-body">
            <div className="setting-item">
              <label className="setting-label">Enable Notifications</label>
              <p className="setting-description">
                Show notifications for completed operations and alerts
              </p>
              <div className="toggle-container">
                <button
                  className={`toggle-switch ${settings.showNotifications ? 'active' : ''}`}
                  onClick={() => handleToggle('showNotifications')}
                >
                  <span className="toggle-slider"></span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="settings-section">
          <div className="section-header">
            <h2>Default Folder</h2>
            <p>Set your default folder for quick access</p>
          </div>
          <div className="section-body">
            <div className="setting-item">
              <label className="setting-label">Default Folder Path</label>
              <input
                type="text"
                placeholder="/Users/username/Downloads"
                value={settings.defaultFolder}
                onChange={handleInputChange}
                className="folder-input"
              />
            </div>
          </div>
        </div>

        <div className="action-buttons">
          <button className="btn-primary" onClick={handleSaveSettings}>
            Save Settings
          </button>
          <button className="btn-secondary" onClick={handleResetSettings}>
            Reset to Default
          </button>
        </div>
      </div>
    </div>
  );
}

export default Settings;
