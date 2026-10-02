import React from 'react';
import '../styles/FileList.css';

function FileList({ files, currentIndex, onFileSelect, loading, duplicates }) {
  const getFileIcon = (extension) => {
    const iconMap = {
      'pdf': '📑',
      'doc': '📝', 'docx': '📝',
      'xls': '📊', 'xlsx': '📊',
      'jpg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'jpeg': '🖼️',
      'mp4': '🎬', 'mp3': '🎵',
      'zip': '📦', 'rar': '📦',
      'txt': '📄',
      'code': '💻',
    };
    return iconMap[extension?.toLowerCase()] || '📄';
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="file-list">
      <div className="list-header">
        <h3>Files ({files.length})</h3>
      </div>

      <div className="files-container">
        {files.length === 0 ? (
          <div className="empty-state">
            <p>No files scanned</p>
          </div>
        ) : (
          files.map((file, index) => {
            const isDuplicate = duplicates && duplicates[index];
            return (
              <div
                key={index}
                style={{
                  background: 'white',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  padding: '8px',
                  marginBottom: '6px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  minHeight: '50px'
                }}
                className={`file-item ${index === currentIndex ? 'active' : ''} ${isDuplicate ? 'duplicate' : ''}`}
                onClick={() => onFileSelect(index)}
              >
                <div className="file-icon" style={{ fontSize: '20px', flexShrink: 0 }}>{getFileIcon(file.extension)}</div>
                <div className="file-info" style={{ flex: 1, minWidth: 0 }}>
                  <div className="file-name" style={{ color: '#111827', fontWeight: 500, fontSize: '14px', marginBottom: '2px' }}>
                    {file.name || 'Unnamed'}
                  </div>
                  <div className="file-meta" style={{ color: '#6b7280', fontSize: '12px' }}>
                    {file.extension || 'unknown'} • {formatFileSize(file.size || 0)}
                  </div>
                </div>
                {isDuplicate && <span className="duplicate-badge">⚠️ Duplicate</span>}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

export default FileList;
