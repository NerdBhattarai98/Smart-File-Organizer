const API_BASE_URL = 'http://localhost:8000/api';

// Scan folder for files
export const scanFolder = async (folderPath) => {
  try {
    const response = await fetch(`${API_BASE_URL}/scan-folder/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ folder_path: folderPath }),
    });

    if (!response.ok) {
      // Surface backend detail so the user knows if a path is wrong or blocked.
      let detail = 'Scan folder failed';
      try {
        const data = await response.json();
        detail = data?.detail || detail;
      } catch (err) {
        // ignore parse errors, fall back to text
        const txt = await response.text();
        if (txt) detail = txt;
      }
      throw new Error(detail);
    }

    return await response.json();
  } catch (error) {
    console.error('Scan error:', error);
    throw error;
  }
};

// Classify files and get predictions
export const classifyFiles = async (files) => {
  try {
    const response = await fetch(`${API_BASE_URL}/classify-files/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ files }),
    });
    
    if (!response.ok) throw new Error('Classification failed');
    return await response.json();
  } catch (error) {
    console.error('Classification error:', error);
    throw error;
  }
};

// Detect duplicates
export const detectDuplicates = async (files) => {
  try {
    const response = await fetch(`${API_BASE_URL}/detect-duplicates/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ files }),
    });
    
    if (!response.ok) throw new Error('Duplicate detection failed');
    return await response.json();
  } catch (error) {
    console.error('Duplicate detection error:', error);
    throw error;
  }
};

// Apply action (move file)
export const applyAction = async (actionData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/actions/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(actionData),
    });
    
    if (!response.ok) throw new Error('Action failed');
    return await response.json();
  } catch (error) {
    console.error('Action error:', error);
    throw error;
  }
};

// Batch apply actions (organize multiple files at once) - MUCH FASTER
export const batchApplyActions = async (actions) => {
  try {
    const response = await fetch(`${API_BASE_URL}/apply-action/batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ actions }),
    });
    
    if (!response.ok) throw new Error('Batch action failed');
    return await response.json();
  } catch (error) {
    console.error('Batch action error:', error);
    throw error;
  }
};

// Undo last action
export const undoAction = async (actionData) => {
  try {
    const response = await fetch(`${API_BASE_URL}/undo/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(actionData || {}),
    });
    
    if (!response.ok) throw new Error('Undo failed');
    return await response.json();
  } catch (error) {
    console.error('Undo error:', error);
    throw error;
  }
};

// Get undo history
export const getUndoHistory = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/undo/history`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) throw new Error('Failed to get undo history');
    return await response.json();
  } catch (error) {
    console.error('Undo history error:', error);
    throw error;
  }
};

// Undo specific action by ID
export const undoSpecificAction = async (actionId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/undo/specific/${actionId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    });
    
    if (!response.ok) throw new Error('Failed to undo specific action');
    return await response.json();
  } catch (error) {
    console.error('Undo specific action error:', error);
    throw error;
  }
};

// Batch undo multiple actions
export const batchUndoActions = async (count = 1, actionIds = null) => {
  try {
    const response = await fetch(`${API_BASE_URL}/undo/batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        count: actionIds ? undefined : count,
        action_ids: actionIds,
      }),
    });
    
    if (!response.ok) throw new Error('Failed to batch undo actions');
    return await response.json();
  } catch (error) {
    console.error('Batch undo error:', error);
    throw error;
  }
};

// Check for file collisions before organizing
export const checkCollisions = async (filesToOrganize, targetFolder) => {
  try {
    const response = await fetch(`${API_BASE_URL}/collisions/check-collisions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        files_to_organize: filesToOrganize,
        target_folder: targetFolder,
      }),
    });
    
    if (!response.ok) throw new Error('Failed to check collisions');
    return await response.json();
  } catch (error) {
    console.error('Collision check error:', error);
    throw error;
  }
};

// Resolve a file collision
export const resolveCollision = async (collisionId, keepFilePath, action, newName = null) => {
  try {
    const response = await fetch(`${API_BASE_URL}/collisions/resolve-collision`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        collision_id: collisionId,
        keep_file_path: keepFilePath,
        action: action,
        new_name: newName,
      }),
    });
    
    if (!response.ok) throw new Error('Failed to resolve collision');
    return await response.json();
  } catch (error) {
    console.error('Collision resolution error:', error);
    throw error;
  }
};

export default {
  scanFolder,
  classifyFiles,
  detectDuplicates,
  applyAction,
  batchApplyActions,
  undoAction,
  getUndoHistory,
  undoSpecificAction,
  batchUndoActions,
  checkCollisions,
  resolveCollision,
};
