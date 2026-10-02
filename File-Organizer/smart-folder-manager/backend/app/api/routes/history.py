import json
import os
from fastapi import APIRouter
from datetime import datetime
from app.db.mongo_client import get_file_movements_collection
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/history")
async def get_history():
    """Get all action history - from both MongoDB and JSON file"""
    try:
        actions = []
        
        # Try to get from MongoDB first (most recent data)
        try:
            collection = get_file_movements_collection()
            if collection is not None:
                # Get all documents sorted by timestamp (newest first)
                mongo_actions = list(collection.find().sort("timestamp", -1))  # No limit - get all
                # Convert MongoDB documents to JSON-serializable format
                for action in mongo_actions:
                    action_dict = {
                        "id": str(action.get("_id")) if action.get("_id") else action.get("id"),
                        "type": action.get("type"),
                        "action": action.get("type"),  # Backwards compatibility
                        "filename": action.get("filename"),
                        "from_path": action.get("from_path"),
                        "to_path": action.get("to_path"),
                        "category": action.get("category"),
                        "confidence": action.get("confidence"),
                        "folder_source": action.get("folder_source"),
                        "custom_folder_name": action.get("custom_folder_name"),
                        "timestamp": action.get("timestamp").isoformat() if action.get("timestamp") else None
                    }
                    actions.append(action_dict)
                logger.info(f"Retrieved {len(actions)} actions from MongoDB")
        except Exception as e:
            logger.warning(f"Failed to read from MongoDB: {e}. Falling back to JSON.")
        
        # If MongoDB failed or is empty, try JSON file
        if not actions:
            history_path = os.path.join(
                os.path.dirname(__file__),
                '../../logs/action_history.json'
            )
            
            if os.path.exists(history_path):
                with open(history_path, 'r') as f:
                    history_data = json.load(f)
                    # Handle both dict and list formats
                    if isinstance(history_data, dict):
                        actions = history_data.get("actions", [])
                    else:
                        actions = history_data if isinstance(history_data, list) else []
                    # Sort by timestamp if available
                    actions = sorted(actions, key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return {
            "actions": actions,
            "total": len(actions)
        }
    
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return {
            "actions": [],
            "total": 0,
            "error": str(e)
        }

@router.delete("/history/clear")
async def clear_history():
    """Clear all action history"""
    try:
        history_path = os.path.join(
            os.path.dirname(__file__),
            '../../logs/action_history.json'
        )
        
        if os.path.exists(history_path):
            with open(history_path, 'w') as f:
                json.dump({"actions": []}, f)
        
        # Also clear MongoDB
        try:
            collection = get_file_movements_collection()
            if collection is not None:
                collection.delete_many({})
                logger.info("Cleared MongoDB history")
        except Exception as e:
            logger.warning(f"Failed to clear MongoDB: {e}")
        
        return {"message": "History cleared successfully"}
    
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to clear history"
        }

@router.get("/history/stats")
async def get_history_stats():
    """Get action history statistics"""
    try:
        actions = []
        
        # Try MongoDB first
        try:
            collection = get_file_movements_collection()
            if collection is not None:
                mongo_actions = list(collection.find())
                actions = mongo_actions
        except Exception as e:
            logger.warning(f"Failed to read stats from MongoDB: {e}")
        
        # Fall back to JSON if needed
        if not actions:
            history_path = os.path.join(
                os.path.dirname(__file__),
                '../../logs/action_history.json'
            )
            
            if os.path.exists(history_path):
                with open(history_path, 'r') as f:
                    history_data = json.load(f)
                    if isinstance(history_data, dict):
                        actions = history_data.get("actions", [])
                    else:
                        actions = history_data if isinstance(history_data, list) else []
        
        stats = {
            "total_actions": len(actions),
            "moves": len([a for a in actions if isinstance(a, dict) and a.get("type") == "move"]),
            "classifications": len([a for a in actions if isinstance(a, dict) and a.get("type") == "classify"]),
            "undos": len([a for a in actions if isinstance(a, dict) and a.get("type") == "undo"])
        }
        
        return stats
    
    except Exception as e:
        logger.error(f"Error fetching history stats: {e}")
        return {
            "total_actions": 0,
            "moves": 0,
            "classifications": 0,
            "undos": 0,
            "error": str(e)
        }
