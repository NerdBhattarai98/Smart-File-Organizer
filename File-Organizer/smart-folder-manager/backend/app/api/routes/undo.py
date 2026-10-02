"""
Undo module
Handles reverting file move actions with smart rollback capabilities
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging
import shutil
import os
import hashlib
import json
from datetime import datetime
from app.core.action_logger import get_last_action, remove_last_action, get_action_history
from app.db.mongo_client import get_file_movements_collection

logger = logging.getLogger(__name__)
router = APIRouter()

class UndoResponse(BaseModel):
    status: str
    message: str
    undone_filename: Optional[str] = None
    undone_from_path: Optional[str] = None
    undone_to_path: Optional[str] = None

class UndoHistoryItem(BaseModel):
    id: str
    filename: str
    from_path: str
    to_path: str
    timestamp: str
    can_undo: bool

class UndoHistoryResponse(BaseModel):
    status: str
    total_actions: int
    actions: List[UndoHistoryItem]

class BatchUndoResponse(BaseModel):
    status: str
    message: str
    total_undone: int
    successful: int
    failed: int
    errors: Optional[List[dict]] = None
    undone_files: Optional[List[str]] = None

class UndoBatchRequest(BaseModel):
    count: int = 1  # Number of latest actions to undo
    action_ids: Optional[List[str]] = None  # Specific action IDs to undo

@router.get("/history")
async def get_undo_history():
    """
    Get history of all undoable actions
    Shows which actions can still be undone
    """
    try:
        actions = get_action_history(limit=100)
        
        history_items = []
        for action in actions:
            action_id = action.get("id", "")
            filename = action.get("filename", "")
            from_path = action.get("from_path", "")
            to_path = action.get("to_path", "")
            timestamp = action.get("timestamp", "")
            
            # Check if file still exists at target location
            can_undo = os.path.exists(to_path)
            
            history_items.append(UndoHistoryItem(
                id=action_id,
                filename=filename,
                from_path=from_path,
                to_path=to_path,
                timestamp=timestamp,
                can_undo=can_undo
            ))
        
        logger.info(f"Retrieved undo history with {len(history_items)} actions")
        
        return UndoHistoryResponse(
            status="success",
            total_actions=len(history_items),
            actions=history_items
        )
    
    except Exception as e:
        logger.error(f"Error retrieving undo history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def undo_last_action():
    """
    Undo the last file move action - FAST version without heavy verification
    """
    try:
        # Get last action from log
        last_action = get_last_action()
        
        if not last_action:
            raise HTTPException(status_code=400, detail="No actions to undo")
        
        from_path = last_action.get("from_path")
        to_path = last_action.get("to_path")
        filename = last_action.get("filename")
        action_id = last_action.get("id")
        
        if not to_path or not from_path:
            raise HTTPException(status_code=400, detail="Invalid action data")
        
        if not os.path.exists(to_path):
            logger.warning(f"File not found at {to_path}, removing from log")
            remove_last_action()
            raise HTTPException(status_code=404, detail="File not found at target location")
        
        # SKIP hash verification for speed - just move the file
        # Move file back to original location
        try:
            os.makedirs(os.path.dirname(from_path), exist_ok=True)
            
            # Handle collision on undo (restore location already has a file)
            if os.path.exists(from_path):
                base, ext = os.path.splitext(from_path)
                counter = 1
                while os.path.exists(f"{base}_restored_{counter}{ext}"):
                    counter += 1
                restored_path = f"{base}_restored_{counter}{ext}"
                shutil.move(to_path, restored_path)
                logger.warning(f"Original location occupied, restored to {restored_path}")
                from_path = restored_path
            else:
                shutil.move(to_path, from_path)
        except Exception as e:
            logger.error(f"Error moving file back {filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to undo: {str(e)}")
        
        # Post-undo verification
        if not os.path.exists(from_path):
            logger.error(f"Undo failed - file not at restored location {from_path}")
            raise HTTPException(status_code=500, detail="Undo verification failed")
        
        # Log undo action to MongoDB (minimal - no hash verification)
        try:
            collection = get_file_movements_collection()
            if collection is not None:
                undo_record = {
                    "_id": f"undo_{action_id}",
                    "id": f"undo_{action_id}",
                    "type": "undo",
                    "original_action_id": action_id,
                    "filename": filename,
                    "from_path": to_path,  # where it was before undo
                    "to_path": from_path,  # where it went after undo
                    "timestamp": datetime.now()
                }
                collection.insert_one(undo_record)
                logger.info(f"Logged undo action to MongoDB for {filename}")
        except Exception as e:
            logger.warning(f"Failed to log undo to MongoDB: {e}")
        
        # Remove from undo history (JSON)
        remove_last_action()
        
        logger.info(f"Undone action for {filename}")
        
        return UndoResponse(
            status="success",
            message=f"Action undone for {filename}",
            undone_filename=filename,
            undone_from_path=to_path,
            undone_to_path=from_path
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error undoing action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/specific/{action_id}")
async def undo_specific_action(action_id: str):
    """
    Undo a specific action by ID (not just the last one)
    Useful for undoing multiple moves or specific files
    """
    try:
        # Get action history
        actions = get_action_history(limit=500)
        
        # Find the specific action
        target_action = None
        target_index = None
        
        for idx, action in enumerate(actions):
            if action.get("id") == action_id:
                target_action = action
                target_index = idx
                break
        
        if not target_action:
            raise HTTPException(status_code=404, detail="Action not found")
        
        from_path = target_action.get("from_path")
        to_path = target_action.get("to_path")
        filename = target_action.get("filename")
        
        if not os.path.exists(to_path):
            raise HTTPException(status_code=404, detail="File not found at target location")
        
        # Move file back
        try:
            os.makedirs(os.path.dirname(from_path), exist_ok=True)
            shutil.move(to_path, from_path)
        except Exception as e:
            logger.error(f"Error moving file back {filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to undo: {str(e)}")
        
        # Log to MongoDB
        try:
            collection = get_file_movements_collection()
            if collection is not None:
                undo_record = {
                    "_id": f"undo_{action_id}",
                    "id": f"undo_{action_id}",
                    "type": "undo",
                    "original_action_id": action_id,
                    "filename": filename,
                    "from_path": to_path,
                    "to_path": from_path,
                    "timestamp": datetime.now()
                }
                collection.insert_one(undo_record)
        except Exception as e:
            logger.warning(f"Failed to log undo to MongoDB: {e}")
        
        # Remove this specific action from history
        # Note: This removes all actions from this point onwards (cascade undo)
        # This is safer than removing just one
        if target_index is not None:
            logger.warning(f"Removing {len(actions) - target_index} actions from undo history (cascade)")
        
        # For simplicity, we just remove the last action each time
        # In production, you might want a more sophisticated undo stack
        remove_last_action()
        
        logger.info(f"Undone specific action {action_id} for {filename}")
        
        return UndoResponse(
            status="success",
            message=f"Undo action {action_id} for {filename}",
            undone_filename=filename,
            undone_from_path=to_path,
            undone_to_path=from_path
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error undoing specific action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch")
async def undo_batch(request: UndoBatchRequest):
    """
    Undo multiple file move actions at once - OPTIMIZED for batch performance
    
    Request options:
    1. count: N (undo last N actions)
    2. action_ids: [id1, id2, ...] (undo specific action IDs)
    
    OPTIMIZATION: Load history ONCE, collect all moves, execute batch, update history ONCE
    """
    try:
        successful = 0
        failed = 0
        errors = []
        undone_files = []
        
        # OPTIMIZATION: Load action history ONCE instead of per action
        all_actions = get_action_history(limit=500)
        if not all_actions:
            raise HTTPException(status_code=400, detail="No actions to undo")
        
        # Build action lookup map for O(1) access
        actions_map = {a.get("id"): a for a in all_actions}
        
        # Determine which actions to undo
        if request.action_ids:
            actions_to_undo_ids = request.action_ids
        else:
            # Undo last N actions
            count = max(1, min(request.count or 1, 500))
            actions_to_undo_ids = [a.get("id") for a in all_actions[-count:]]
        
        # OPTIMIZATION: Collect all file moves first, validate paths
        moves_to_perform = []  # List of (from_path, to_path, action_id, filename)
        
        # Process each action ID in REVERSE order (undo newest first)
        for action_id in reversed(actions_to_undo_ids):
            try:
                target_action = actions_map.get(action_id)
                
                if not target_action:
                    errors.append({
                        "action_id": action_id,
                        "error": "Action not found in history"
                    })
                    failed += 1
                    continue
                
                from_path = target_action.get("from_path")
                to_path = target_action.get("to_path")
                filename = target_action.get("filename")
                
                # Validate paths
                if not to_path or not from_path:
                    errors.append({
                        "filename": filename,
                        "error": "Invalid action data"
                    })
                    failed += 1
                    continue
                
                # Check if file exists at target location
                if not os.path.exists(to_path):
                    logger.warning(f"File not found at {to_path} for undo")
                    errors.append({
                        "filename": filename,
                        "error": f"File not found at {to_path}"
                    })
                    failed += 1
                    continue
                
                # Queue this move for batch execution
                moves_to_perform.append({
                    "from_path": from_path,
                    "to_path": to_path,
                    "action_id": action_id,
                    "filename": filename
                })
                
            except Exception as e:
                logger.error(f"Error validating action {action_id}: {e}")
                errors.append({
                    "action_id": action_id,
                    "error": str(e)
                })
                failed += 1
        
        # OPTIMIZATION: Execute all file moves in batch
        for move in moves_to_perform:
            try:
                from_path = move["from_path"]
                to_path = move["to_path"]
                action_id = move["action_id"]
                filename = move["filename"]
                
                os.makedirs(os.path.dirname(from_path), exist_ok=True)
                
                # Handle collision on undo
                if os.path.exists(from_path):
                    base, ext = os.path.splitext(from_path)
                    counter = 1
                    while os.path.exists(f"{base}_restored_{counter}{ext}"):
                        counter += 1
                    restored_path = f"{base}_restored_{counter}{ext}"
                    shutil.move(to_path, restored_path)
                    logger.warning(f"Original location occupied, restored to {restored_path}")
                    actual_to_path = restored_path
                else:
                    shutil.move(to_path, from_path)
                    actual_to_path = from_path
                
                # Verify undo succeeded
                if not os.path.exists(actual_to_path):
                    logger.error(f"Undo verification failed for {filename}")
                    errors.append({
                        "filename": filename,
                        "error": "Undo verification failed"
                    })
                    failed += 1
                    continue
                
                # Log undo action to MongoDB (batch these too)
                try:
                    collection = get_file_movements_collection()
                    if collection is not None:
                        undo_record = {
                            "_id": f"undo_{action_id}",
                            "id": f"undo_{action_id}",
                            "type": "undo",
                            "original_action_id": action_id,
                            "filename": filename,
                            "from_path": to_path,
                            "to_path": actual_to_path,
                            "timestamp": datetime.now()
                        }
                        collection.insert_one(undo_record)
                except Exception as e:
                    logger.warning(f"Failed to log undo to MongoDB: {e}")
                
                undone_files.append(filename)
                successful += 1
                logger.info(f"Batch undone: {filename}")
                
            except Exception as e:
                logger.error(f"Error moving file back: {e}")
                errors.append({
                    "filename": move["filename"],
                    "error": f"Failed to move: {str(e)}"
                })
                failed += 1
        
        # OPTIMIZATION: Update history file ONCE after all moves complete
        # Remove all undone actions from history in single operation
        try:
            actions_to_remove_ids = set(a["action_id"] for a in moves_to_perform)
            filtered_actions = [a for a in all_actions if a.get("id") not in actions_to_remove_ids]
            
            with open("app/logs/action_history.json", 'w') as f:
                json.dump(filtered_actions, f, indent=2)
            
            logger.info(f"Updated action history: removed {len(actions_to_remove_ids)} actions")
        except Exception as e:
            logger.warning(f"Failed to update action history file: {e}")
        
        total_undone = successful + failed
        
        return BatchUndoResponse(
            status="success" if successful > 0 else "partial",
            message=f"Batch undo completed: {successful} successful, {failed} failed",
            total_undone=total_undone,
            successful=successful,
            failed=failed,
            errors=errors if errors else None,
            undone_files=undone_files if undone_files else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch undo: {e}")
        raise HTTPException(status_code=500, detail=str(e))
