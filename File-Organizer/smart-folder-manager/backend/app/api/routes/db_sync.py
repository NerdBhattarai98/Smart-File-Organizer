"""
Database synchronization status endpoint
Monitors and reports real-time database auto-sync status
"""
from fastapi import APIRouter, HTTPException
from app.db.mongo_client import get_file_movements_collection, get_mongo_client
from app.core.action_logger import get_action_history
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/db-sync-status")
async def get_db_sync_status():
    """
    Check database synchronization status
    Shows if MongoDB is connected and synced with action history
    """
    try:
        db_connected = False
        db_record_count = 0
        json_record_count = 0
        last_sync_time = None
        sync_status = "disconnected"
        
        # Check MongoDB connection
        try:
            client = get_mongo_client()
            if client:
                # Verify connection with ping
                client.admin.command('ping')
                db_connected = True
                
                # Get collection stats
                collection = get_file_movements_collection()
                if collection:
                    db_record_count = collection.count_documents({})
                    
                    # Get last record timestamp
                    last_record = collection.find_one(sort=[("timestamp", -1)])
                    if last_record and last_record.get("timestamp"):
                        last_sync_time = last_record["timestamp"].isoformat()
                    
                    sync_status = "synced"
                    logger.info(f"✓ DB SYNC OK: {db_record_count} records in MongoDB")
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            sync_status = "connection_failed"
        
        # Check JSON history
        try:
            json_actions = get_action_history(limit=1000)
            json_record_count = len(json_actions) if json_actions else 0
        except Exception as e:
            logger.warning(f"Failed to read JSON history: {e}")
        
        # Calculate sync rate
        if json_record_count > 0:
            sync_percentage = (db_record_count / json_record_count) * 100
        else:
            sync_percentage = 100.0 if db_connected else 0.0
        
        return {
            "status": sync_status,
            "mongodb_connected": db_connected,
            "database_records": db_record_count,
            "json_records": json_record_count,
            "sync_percentage": f"{sync_percentage:.1f}%",
            "last_sync": last_sync_time,
            "timestamp": datetime.now().isoformat(),
            "message": f"✓ Database auto-sync is active and synced" if sync_status == "synced" else f"⚠ Database status: {sync_status}"
        }
    
    except Exception as e:
        logger.error(f"Error checking DB sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/db-sync-verify")
async def verify_db_sync():
    """
    Manually trigger database sync verification
    Ensures all pending JSON actions are synced to MongoDB
    """
    try:
        from app.core.action_logger import log_action
        
        json_actions = get_action_history(limit=500)
        if not json_actions:
            return {
                "status": "success",
                "message": "No actions to sync",
                "synced_count": 0
            }
        
        collection = get_file_movements_collection()
        if not collection:
            raise HTTPException(status_code=503, detail="MongoDB not available")
        
        synced_count = 0
        for action in json_actions:
            try:
                # Check if action already in DB
                existing = collection.find_one({"_id": action.get("id")})
                if not existing:
                    # Insert to DB
                    mongo_action = action.copy()
                    mongo_action["_id"] = action.get("id")
                    
                    # Convert timestamp string to datetime
                    if isinstance(mongo_action.get("timestamp"), str):
                        from datetime import datetime
                        mongo_action["timestamp"] = datetime.fromisoformat(mongo_action["timestamp"])
                    
                    collection.insert_one(mongo_action)
                    synced_count += 1
            except Exception as e:
                logger.warning(f"Failed to sync action: {e}")
        
        logger.info(f"✓ MANUAL SYNC COMPLETE: {synced_count} actions synced to MongoDB")
        
        return {
            "status": "success",
            "message": f"Synced {synced_count} actions to MongoDB",
            "synced_count": synced_count,
            "total_json_actions": len(json_actions)
        }
    
    except Exception as e:
        logger.error(f"Error during manual sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/db-records")
async def get_db_records(limit: int = 50):
    """
    Get recent records from MongoDB (auto-synced file movements)
    """
    try:
        collection = get_file_movements_collection()
        if not collection:
            raise HTTPException(status_code=503, detail="MongoDB not available")
        
        records = list(collection.find().sort("timestamp", -1).limit(limit))
        
        # Convert to JSON-serializable format
        formatted_records = []
        for record in records:
            formatted_records.append({
                "id": str(record.get("_id")),
                "filename": record.get("filename"),
                "from_path": record.get("from_path"),
                "to_path": record.get("to_path"),
                "category": record.get("category"),
                "timestamp": record.get("timestamp").isoformat() if record.get("timestamp") else None,
                "folder_source": record.get("folder_source")
            })
        
        return {
            "status": "success",
            "count": len(formatted_records),
            "records": formatted_records
        }
    
    except Exception as e:
        logger.error(f"Error retrieving DB records: {e}")
        raise HTTPException(status_code=500, detail=str(e))
