"""
Folder scanning module
Extracts file metadata from directories
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
import hashlib
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class FileMetadata(BaseModel):
    name: str
    path: str
    extension: str
    size: int
    modified: float
    hash: Optional[str] = None

class ScanResponse(BaseModel):
    folder_path: str
    files_count: int
    files: List[FileMetadata]
    status: str

def calculate_file_hash(file_path: str, algorithm: str = "md5") -> str:
    """Calculate MD5 hash of a file (faster than SHA256 for collision detection)"""
    hash_obj = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):  # Increased chunk size for speed
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        return ""

@router.post("/")
async def scan_folder(request: dict):
    """
    Scan a folder and extract file metadata
    """
    try:
        folder_path = request.get("folder_path")
        
        if not folder_path:
            raise HTTPException(status_code=400, detail="folder_path is required")
        
        # Expand user path (~)
        folder_path = os.path.expanduser(folder_path)
        logger.info(f"Scanning folder: {folder_path}")
        
        if not os.path.exists(folder_path):
            logger.error(f"Folder not found: {folder_path}")
            raise HTTPException(status_code=404, detail=f"Folder not found: {folder_path}")
        
        if not os.path.isdir(folder_path):
            logger.error(f"Path is not a directory: {folder_path}")
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {folder_path}")
        
        files = []
        skipped_count = 0
        error_message = None
        
        # Scan directory
        try:
            dir_items = os.listdir(folder_path)
            logger.info(f"Found {len(dir_items)} items in {folder_path}")
        except PermissionError as e:
            logger.warning(f"Permission denied accessing {folder_path}: {e}")
            error_message = f"Limited access to {folder_path}. Some files may be inaccessible."
            # Return empty result instead of raising exception
            return ScanResponse(
                folder_path=folder_path,
                files_count=0,
                files=[],
                status="partial"
            )
        except Exception as e:
            logger.error(f"Error listing directory {folder_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Error listing directory: {e}")
        
        for filename in dir_items:
            # Skip hidden files and system files
            if filename.startswith('.'):
                skipped_count += 1
                continue
                
            file_path = os.path.join(folder_path, filename)
            
            # Skip directories and symbolic links (single stat call)
            try:
                stat_info = os.stat(file_path)
                if not os.path.isfile(file_path):
                    continue
                # Skip empty files and very large files (> 2GB)
                if stat_info.st_size == 0 or stat_info.st_size > 2 * 1024 * 1024 * 1024:
                    skipped_count += 1
                    continue
            except OSError:
                skipped_count += 1
                continue
            
            try:
                extension = os.path.splitext(filename)[1].lstrip('.')
                
                # Optimize: Only hash files < 500MB for collision detection
                file_hash = ""
                if stat_info.st_size < 500 * 1024 * 1024:
                    file_hash = calculate_file_hash(file_path)
                
                file_meta = FileMetadata(
                    name=filename,
                    path=file_path,
                    extension=extension,
                    size=stat_info.st_size,
                    modified=stat_info.st_mtime,
                    hash=file_hash
                )
                files.append(file_meta)
            except PermissionError:
                logger.warning(f"Permission denied accessing file {filename}")
                skipped_count += 1
                continue
            except Exception as e:
                logger.warning(f"Error processing file {filename}: {e}")
                skipped_count += 1
                continue
        
        logger.info(f"Scanned folder {folder_path}: found {len(files)} files, skipped {skipped_count}")
        
        return ScanResponse(
            folder_path=folder_path,
            files_count=len(files),
            files=files,
            status="success"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))
