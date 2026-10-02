"""
Action logging module
Logs all file operations for undo functionality
Stores in both JSON (for undo) and MongoDB (for history tracking)
"""
import json
import os
import logging
from datetime import datetime
from typing import Optional, Dict, List
import uuid
from app.db.mongo_client import get_file_movements_collection

logger = logging.getLogger(__name__)

# Action history file
ACTION_LOG_FILE = "app/logs/action_history.json"

def ensure_log_file():
    """Ensure log file exists"""
    os.makedirs(os.path.dirname(ACTION_LOG_FILE), exist_ok=True)
    if not os.path.exists(ACTION_LOG_FILE):
        with open(ACTION_LOG_FILE, 'w') as f:
            json.dump([], f)

def log_action(
    action_type: str,
    filename: str,
    from_path: str,
    to_path: str,
    category: str,
    confidence: float,
    folder_source: str = "category",
    custom_folder_name: Optional[str] = None
) -> str:
    """
    Log a file action to both JSON and MongoDB
    Args:
        action_type: Type of action (move, classify, undo)
        filename: Name of the file
        from_path: Original file path
        to_path: New file path
        category: Category assigned
        confidence: Confidence score
        folder_source: Source of folder name (category, metadata, or custom)
        custom_folder_name: Custom folder name provided by user (if any)
    Returns: action_id
    """
    try:
        ensure_log_file()
        
        action_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        action = {
            "id": action_id,
            "type": action_type,
            "filename": filename,
            "from_path": from_path,
            "to_path": to_path,
            "category": category,
            "confidence": confidence,
            "folder_source": folder_source,
            "custom_folder_name": custom_folder_name,  # Track custom folder name
            "timestamp": timestamp
        }
        
        # Log to JSON (for undo functionality)
        with open(ACTION_LOG_FILE, 'r') as f:
            actions = json.load(f)
        
        actions.append(action)
        
        with open(ACTION_LOG_FILE, 'w') as f:
            json.dump(actions, f, indent=2)
        
        # Log to MongoDB (for permanent history) - AUTO-UPDATE in real-time
        try:
            collection = get_file_movements_collection()
            if collection is not None:
                # Add MongoDB-specific fields
                mongo_action = action.copy()
                mongo_action["_id"] = action_id
                mongo_action["timestamp"] = datetime.fromisoformat(timestamp)  # MongoDB uses datetime objects
                result = collection.insert_one(mongo_action)
                logger.info(f"✓ AUTO-SYNCED to DB: {action_id} | {filename} → {to_path}")
                return action_id
            else:
                logger.warning(f"MongoDB unavailable, retrying connection for {action_id}")
        except Exception as e:
            logger.error(f"Failed to AUTO-SYNC to MongoDB: {e}. Continuing with JSON log.")
        
        logger.info(f"Logged action {action_id}: {action_type} {filename}")
        
        return action_id
    
    except Exception as e:
        logger.error(f"Error logging action: {e}")
        return ""

def get_last_action() -> Optional[Dict]:
    """
    Get the last logged action
    """
    try:
        ensure_log_file()
        
        with open(ACTION_LOG_FILE, 'r') as f:
            actions = json.load(f)
        
        if actions:
            return actions[-1]
        return None
    
    except Exception as e:
        logger.error(f"Error reading last action: {e}")
        return None

def remove_last_action() -> bool:
    """
    Remove the last logged action (for undo)
    """
    try:
        ensure_log_file()
        
        with open(ACTION_LOG_FILE, 'r') as f:
            actions = json.load(f)
        
        if actions:
            removed = actions.pop()
            
            with open(ACTION_LOG_FILE, 'w') as f:
                json.dump(actions, f, indent=2)
            
            logger.info(f"Removed action {removed.get('id')}")
            return True
        
        return False
    
    except Exception as e:
        logger.error(f"Error removing last action: {e}")
        return False

def get_action_history(limit: int = 50) -> List[Dict]:
    """
    Get action history
    """
    try:
        ensure_log_file()
        
        with open(ACTION_LOG_FILE, 'r') as f:
            actions = json.load(f)
        
        return actions[-limit:]
    
    except Exception as e:
        logger.error(f"Error reading action history: {e}")
        return []

def clear_action_history() -> bool:
    """
    Clear all action history
    """
    try:
        with open(ACTION_LOG_FILE, 'w') as f:
            json.dump([], f)
        
        logger.info("Cleared action history")
        return True
    
    except Exception as e:
        logger.error(f"Error clearing action history: {e}")
        return False
