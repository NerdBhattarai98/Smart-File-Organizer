"""
Duplicate detection module
Uses hash-based exact detection, perceptual image hashing, and filename similarity
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import logging
from app.ml.duplicate_detector import DuplicateDetector

logger = logging.getLogger(__name__)
router = APIRouter()

class DuplicateGroup(BaseModel):
    group_id: str
    files: List[str]
    similarity_score: float
    detection_method: Optional[str] = "Unknown"

class DuplicateResponse(BaseModel):
    status: str
    duplicate_groups: List[DuplicateGroup]
    total_duplicates: int

# Initialize detector
detector = DuplicateDetector()

@router.post("/")
async def detect_duplicates(request: dict):
    """
    Detect duplicate and near-duplicate files
    """
    try:
        files = request.get("files", [])
        
        if not files:
            return DuplicateResponse(
                status="success",
                duplicate_groups=[],
                total_duplicates=0
            )
        
        # Extract file names and hashes
        file_data = []
        for file_obj in files:
            file_data.append({
                "name": file_obj.get("name"),
                "hash": file_obj.get("hash"),
                "extension": file_obj.get("extension")
            })
        
        # Find duplicates
        duplicate_groups = detector.find_duplicates(file_data)
        
        total_dups = sum(len(group["files"]) for group in duplicate_groups)
        
        logger.info(f"Found {len(duplicate_groups)} duplicate groups ({total_dups} files)")
        
        return DuplicateResponse(
            status="success",
            duplicate_groups=duplicate_groups,
            total_duplicates=total_dups
        )
    
    except Exception as e:
        logger.error(f"Error detecting duplicates: {e}")
        return DuplicateResponse(
            status="error",
            duplicate_groups=[],
            total_duplicates=0
        )
