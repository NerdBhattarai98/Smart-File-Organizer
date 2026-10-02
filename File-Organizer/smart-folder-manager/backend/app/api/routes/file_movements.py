"""
File movement history routes
Retrieves file organization history from MongoDB
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging
from app.db.mongo_client import get_file_movements_collection
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

class FileMovementRecord(BaseModel):
    id: str
    filename: str
    original_path: str
    new_path: str
    category: str
    confidence: float
    folder_source: str
    timestamp: str

class FileMovementResponse(BaseModel):
    status: str
    records: List[FileMovementRecord]
    total: int

@router.get("/file-movements")
async def get_file_movements(
    limit: int = 50,
    skip: int = 0,
    filename: Optional[str] = None,
    original_path: Optional[str] = None
):
    """
    Get file movement history from MongoDB
    Query parameters:
    - limit: max records to return (default 50)
    - skip: number of records to skip (for pagination)
    - filename: filter by filename (optional)
    - original_path: filter by original path (optional)
    """
    try:
        collection = get_file_movements_collection()
        if not collection:
            raise HTTPException(status_code=503, detail="MongoDB not connected")
        
        # Build filter query
        filter_query = {}
        if filename:
            filter_query["filename"] = {"$regex": filename, "$options": "i"}
        if original_path:
            filter_query["original_path"] = {"$regex": original_path, "$options": "i"}
        
        # Query MongoDB
        total = collection.count_documents(filter_query)
        records = list(
            collection.find(filter_query)
            .sort("timestamp", -1)
            .limit(limit)
            .skip(skip)
        )
        
        # Convert to response format
        movements = []
        for record in records:
            movements.append(FileMovementRecord(
                id=record.get("id", ""),
                filename=record.get("filename", ""),
                original_path=record.get("from_path", ""),
                new_path=record.get("to_path", ""),
                category=record.get("category", ""),
                confidence=record.get("confidence", 0.0),
                folder_source=record.get("folder_source", ""),
                timestamp=record.get("timestamp").isoformat() if isinstance(record.get("timestamp"), datetime) else str(record.get("timestamp"))
            ))
        
        logger.info(f"Retrieved {len(movements)} file movements from MongoDB")
        
        return FileMovementResponse(
            status="success",
            records=movements,
            total=total
        )
    
    except Exception as e:
        logger.error(f"Error retrieving file movements: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")

@router.get("/file-movement-stats")
async def get_file_movement_stats():
    """
    Get statistics about file movements
    Returns: total moves, by category, by folder source
    """
    try:
        collection = get_file_movements_collection()
        if not collection:
            raise HTTPException(status_code=503, detail="MongoDB not connected")
        
        total = collection.count_documents({})
        
        # Aggregation pipeline for stats
        stats = list(collection.aggregate([
            {
                "$group": {
                    "_id": "$category",
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}}
        ]))
        
        source_stats = list(collection.aggregate([
            {
                "$group": {
                    "_id": "$folder_source",
                    "count": {"$sum": 1}
                }
            }
        ]))
        
        return {
            "status": "success",
            "total_movements": total,
            "by_category": {stat["_id"]: stat["count"] for stat in stats},
            "by_folder_source": {stat["_id"]: stat["count"] for stat in source_stats}
        }
    
    except Exception as e:
        logger.error(f"Error calculating stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating stats: {str(e)}")

@router.get("/file-path-history/{file_id}")
async def get_file_path_history(file_id: str):
    """
    Get complete history of a specific file's movements
    file_id: the action_id from a movement record
    """
    try:
        collection = get_file_movements_collection()
        if not collection:
            raise HTTPException(status_code=503, detail="MongoDB not connected")
        
        record = collection.find_one({"id": file_id})
        if not record:
            raise HTTPException(status_code=404, detail="File movement record not found")
        
        # Find all movements involving the same filename
        movements = list(
            collection.find({"filename": record.get("filename")})
            .sort("timestamp", 1)
        )
        
        history = []
        for mov in movements:
            history.append({
                "action_id": mov.get("id"),
                "from_path": mov.get("from_path"),
                "to_path": mov.get("to_path"),
                "category": mov.get("category"),
                "timestamp": mov.get("timestamp").isoformat() if isinstance(mov.get("timestamp"), datetime) else str(mov.get("timestamp"))
            })
        
        return {
            "status": "success",
            "filename": record.get("filename"),
            "total_movements": len(history),
            "history": history
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving file history: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving history: {str(e)}")
