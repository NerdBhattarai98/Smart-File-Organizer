"""
File collision detection and resolution
Detects when organizing files would create duplicates
Enhanced with similarity matching and comprehensive detection
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Tuple
import os
import logging
import hashlib
from pathlib import Path
from difflib import SequenceMatcher
import concurrent.futures

logger = logging.getLogger(__name__)
router = APIRouter()

# Thread pool for parallel hash calculation
HASH_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=4)

class CollisionFile(BaseModel):
    """Represents a file involved in a collision"""
    filename: str
    filepath: str
    size: int
    modified_time: float
    file_hash: Optional[str] = None

class CollisionGroup(BaseModel):
    """A group of files with potential collision"""
    collision_id: str
    target_folder: str
    files: List[CollisionFile]
    collision_type: str  # "duplicate_name", "same_content", "similar_name"
    recommendation: str

class CollisionCheckRequest(BaseModel):
    """Request to check for collisions"""
    files_to_organize: List[Dict]  # Files with their target folders: {filename, filepath, target_folder}
    target_folder: Optional[str] = None  # Base target folder (for backward compatibility)

class CollisionResolutionRequest(BaseModel):
    """Request to resolve collision - user chooses which file to keep"""
    collision_id: str
    keep_file_path: str  # Which file to keep
    action: str  # "keep_new", "keep_existing", "rename_new", "rename_existing"
    new_name: Optional[str] = None  # New name if renaming

def calculate_file_hash(filepath: str, chunk_size: int = 65536) -> Optional[str]:
    """Calculate MD5 hash of file content (optimized with larger chunks)"""
    try:
        # Skip hashing very large files
        file_size = os.path.getsize(filepath)
        if file_size > 500 * 1024 * 1024:  # > 500MB
            return None
            
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logger.warning(f"Failed to calculate hash for {filepath}: {e}")
        return None

def calculate_similarity(hash1: str, hash2: str, filename1: str, filename2: str) -> Tuple[float, str]:
    """
    Calculate similarity between two files
    Returns: (similarity_score 0-100, reason)
    - 100 = identical content
    - 80+ = very similar
    - 50+ = partial match (some content similar)
    """
    if hash1 == hash2:
        return 100, "Identical content"
    
    # Name similarity
    name_sim = SequenceMatcher(None, filename1.lower(), filename2.lower()).ratio()
    
    # If names are very similar, it's likely the same file
    if name_sim > 0.85:
        return 90 if name_sim == 1.0 else 85, "Same/very similar filename"
    
    # If names are somewhat similar
    if name_sim > 0.7:
        return 75, f"Similar filename ({int(name_sim*100)}% match)"
    
    return 0, "Different content and name"

def get_all_files_in_folder(folder_path: str) -> Dict[str, Dict]:
    """Get all files in folder with their metadata"""
    files = {}
    try:
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            for root, dirs, filenames in os.walk(folder_path):
                for filename in filenames:
                    filepath = os.path.join(root, filename)
                    try:
                        file_stat = os.stat(filepath)
                        files[filename] = {
                            "path": filepath,
                            "size": file_stat.st_size,
                            "modified": file_stat.st_mtime,
                            "hash": None  # Will calculate on demand
                        }
                    except Exception as e:
                        logger.warning(f"Failed to stat {filepath}: {e}")
    except Exception as e:
        logger.warning(f"Failed to scan folder {folder_path}: {e}")
    return files

@router.post("/check-collisions")
async def check_collisions(request: CollisionCheckRequest):
    """
    Comprehensive collision detection:
    1. FOLDER-LEVEL: Multiple files going to same folder (with same/different names)
    2. FILE-LEVEL: Exact filename matches in target folder
    3. CONTENT-LEVEL: Identical content with different names
    """
    try:
        collisions = []
        collision_groups = {}
        
        # Normalize request: extract target folders for each file
        target_folder_mapping = {}  # Map each file to its target folder
        
        for file_obj in request.files_to_organize:
            if isinstance(file_obj, dict):
                filename = file_obj.get('filename')
                target_folder = file_obj.get('target_folder') or request.target_folder
            else:
                filename = file_obj.filename
                target_folder = request.target_folder
            
            if filename and target_folder:
                if target_folder not in target_folder_mapping:
                    target_folder_mapping[target_folder] = []
                target_folder_mapping[target_folder].append(file_obj)
        
        logger.info(f"🔍 COLLISION CHECK: {len(request.files_to_organize)} files → {len(target_folder_mapping)} target folders")
        for folder, files in target_folder_mapping.items():
            logger.info(f"  Folder: {folder} ← {len(files)} files: {[f.get('filename') if isinstance(f, dict) else f.filename for f in files]}")
        
        # IMPORTANT: Check if target folders exist and have files - create them if needed for checking
        for target_folder in list(target_folder_mapping.keys()):
            # Ensure parent directory exists for path operations
            parent = os.path.dirname(target_folder)
            if parent and not os.path.exists(parent):
                try:
                    os.makedirs(parent, exist_ok=True)
                except Exception as e:
                    logger.warning(f"Could not create parent dir {parent}: {e}")
        
        # CHECK 0: Detect intra-batch collisions (duplicate filenames in this batch)
        # Build filename mapping for files in this batch
        batch_filenames = {}  # filename → [file_obj1, file_obj2, ...]
        for file_obj in request.files_to_organize:
            if isinstance(file_obj, dict):
                filename = file_obj.get('filename')
                filepath = file_obj.get('filepath')
            else:
                filename = file_obj.filename
                filepath = file_obj.filepath
            
            if filename:
                filename_lower = filename.lower()
                if filename_lower not in batch_filenames:
                    batch_filenames[filename_lower] = []
                batch_filenames[filename_lower].append({
                    'file_obj': file_obj,
                    'filename': filename,
                    'filepath': filepath
                })
        
        # Process intra-batch duplicates
        for filename_lower, file_list in batch_filenames.items():
            if len(file_list) > 1:
                # Multiple files with same name in this batch - collision!
                logger.info(f"SAME-NAME COLLISION DETECTED!")
                logger.info(f"   Filename: '{file_list[0]['filename']}'")
                logger.info(f"   Count: {len(file_list)} files with this exact name")
                for idx, f in enumerate(file_list, 1):
                    logger.info(f"     {idx}. {f['filepath']}")
                
                for i in range(len(file_list) - 1):
                    file1 = file_list[i]
                    file2 = file_list[i + 1]
                    
                    # Calculate hashes
                    hash1 = calculate_file_hash(file1['filepath'])
                    hash2 = calculate_file_hash(file2['filepath'])
                    
                    collision_id = f"intra_batch_{filename_lower}_{i}"
                    
                    logger.info(f"   Pair {i+1}: Comparing hashes...")
                    logger.info(f"     File 1: {hash1}")
                    logger.info(f"     File 2: {hash2}")
                    logger.info(f"     Match: {hash1 == hash2}")
                    
                    collision_groups[collision_id] = {
                        "collision_id": collision_id,
                        "target_folder": "Source folder (same batch)",
                        "collision_type": "intra_batch_duplicate" if hash1 == hash2 else "intra_batch_name_collision",
                        "similarity_score": 100 if hash1 == hash2 else 95,
                        "recommendation": "Files with same name are being organized in this batch. Choose which to keep or rename.",
                        "reason": f"Multiple files named '{file1['filename']}' in this batch",
                        "files": [
                            {
                                "filename": file1['filename'],
                                "filepath": file1['filepath'],
                                "size": os.path.getsize(file1['filepath']) if os.path.exists(file1['filepath']) else 0,
                                "modified_time": os.path.getmtime(file1['filepath']) if os.path.exists(file1['filepath']) else 0,
                                "file_hash": hash1,
                                "status": "file_in_batch",
                                "type": "file_1"
                            },
                            {
                                "filename": file2['filename'],
                                "filepath": file2['filepath'],
                                "size": os.path.getsize(file2['filepath']) if os.path.exists(file2['filepath']) else 0,
                                "modified_time": os.path.getmtime(file2['filepath']) if os.path.exists(file2['filepath']) else 0,
                                "file_hash": hash2,
                                "status": "file_in_batch",
                                "type": "file_2"
                            }
                        ]
                    }
                    logger.info(f"  → {collision_id}: {file1['filepath']} vs {file2['filepath']}")
        
        for target_folder, files_for_folder in target_folder_mapping.items():
            # Get all existing files in THIS target folder
            existing_files = get_all_files_in_folder(target_folder)
            logger.info(f"  Checking target folder: {target_folder}")
            logger.info(f"    Existing files in target: {len(existing_files)} files - {list(existing_files.keys())}")
            
            # Build lookup by filename
            existing_by_name = {}
            for filename, info in existing_files.items():
                existing_by_name[filename.lower()] = {
                    "filename": filename,
                    "path": info["path"],
                    "size": info["size"],
                    "modified": info["modified"]
                }
            
            # Pre-calculate hashes for existing files
            existing_hashes = {}
            for filename, info in existing_files.items():
                file_hash = calculate_file_hash(info["path"])
                if file_hash:
                    existing_hashes[filename.lower()] = file_hash
            
            # Process each file going to THIS target folder
            for file_idx, file_obj in enumerate(files_for_folder):
                if isinstance(file_obj, dict):
                    filename = file_obj.get('filename')
                    filepath = file_obj.get('filepath')
                    file_size = file_obj.get('size', 0)
                    file_modified = file_obj.get('modified_time', 0)
                else:
                    filename = file_obj.filename
                    filepath = file_obj.filepath
                    file_size = file_obj.size
                    file_modified = file_obj.modified_time
                
                logger.info(f"    [File {file_idx+1}/{len(files_for_folder)}] Processing: {filename}")
                
                new_hash = calculate_file_hash(filepath)
                collision_found = False
                
                # CHECK 1: Exact name match in target folder
                existing_info = existing_by_name.get(filename.lower())
                
                if existing_info:
                    logger.info(f"      ✓ Name match found: {existing_info['filename']}")
                    existing_hash = existing_hashes.get(filename.lower())
                    
                    if new_hash and existing_hash and new_hash == existing_hash:
                        # 100% identical content - skip
                        collision_type = "identical_duplicate"
                        reason = "File already exists with identical content (safe to skip)"
                        similarity_score = 100
                        logger.info(f"      → identical_duplicate (same name, same content)")
                    else:
                        # Same name, different content - REAL collision
                        collision_type = "name_collision_different_content"
                        reason = f"File with same name exists with different content in '{os.path.basename(target_folder)}'"
                        similarity_score = 95
                        logger.info(f"      → NAME COLLISION DETECTED! (same name, different content)")
                        collision_found = True
                else:
                    logger.info(f"      ✗ No name match in target")
                    collision_type = None
                
                # Report if REAL collision
                if collision_found:
                    collision_id = f"{target_folder}_{filename}_{similarity_score}"
                    logger.info(f"      🚨 RECORDING COLLISION: {collision_type}")
                    
                    collision_groups[collision_id] = {
                        "collision_id": collision_id,
                        "target_folder": target_folder,
                        "collision_type": collision_type,
                        "similarity_score": similarity_score,
                        "recommendation": generate_recommendation(similarity_score, collision_type),
                        "reason": reason,
                        "files": [
                            {
                                "filename": filename,
                                "filepath": filepath,
                                "size": file_size,
                                "modified_time": file_modified,
                                "file_hash": new_hash,
                                "status": "new_file",
                                "type": "new"
                            },
                            {
                                "filename": existing_info["filename"],
                                "filepath": existing_info["path"],
                                "size": existing_info["size"],
                                "modified_time": existing_info["modified"],
                                "file_hash": existing_hashes.get(filename.lower()),
                                "status": "existing_file",
                                "type": "existing"
                            }
                        ]
                    }
                    collision_found = True
                
                # CHECK 2: Content-based collision (same file, different name)
                if new_hash and not collision_found:
                    for existing_filename, existing_hash in existing_hashes.items():
                        if new_hash == existing_hash and existing_filename != filename.lower():
                            existing_info = existing_by_name.get(existing_filename)
                            if existing_info:
                                collision_type = "content_collision_different_name"
                                reason = f"File has same content as '{existing_filename}' in '{os.path.basename(target_folder)}' (content-based duplicate)"
                                similarity_score = 100
                                
                                collision_id = f"{target_folder}_{filename}_content_{existing_filename}"
                                
                                collision_groups[collision_id] = {
                                    "collision_id": collision_id,
                                    "target_folder": target_folder,
                                    "collision_type": collision_type,
                                    "similarity_score": similarity_score,
                                    "recommendation": generate_recommendation(similarity_score, collision_type),
                                    "reason": reason,
                                    "files": [
                                        {
                                            "filename": filename,
                                            "filepath": filepath,
                                            "size": file_size,
                                            "modified_time": file_modified,
                                            "file_hash": new_hash,
                                            "status": "new_file",
                                            "type": "new"
                                        },
                                        {
                                            "filename": existing_info["filename"],
                                            "filepath": existing_info["path"],
                                            "size": existing_info["size"],
                                            "modified_time": existing_info["modified"],
                                            "file_hash": existing_hash,
                                            "status": "existing_file",
                                            "type": "existing"
                                        }
                                    ]
                                }
                                collision_found = True
                                logger.info(f"✓ Content-based collision detected: '{filename}' matches '{existing_filename}' in '{os.path.basename(target_folder)}'")
                                break
        
        collisions = list(collision_groups.values())
        
        # Sort by similarity score (highest first)
        collisions = sorted(collisions, key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        logger.info(f"✓ Collision detection complete: {len(collisions)} collisions found across {len(target_folder_mapping)} folders")
        for c in collisions:
            logger.info(f"  • {c['collision_type']}: {c['reason']}")
        
        return {
            "has_collisions": len(collisions) > 0,
            "collision_count": len(collisions),
            "collisions": collisions,
            "total_files_to_organize": sum(len(f) for f in target_folder_mapping.values()),
            "files_with_collisions": len(set(c["files"][0]["filepath"] for c in collisions))
        }
    
    except Exception as e:
        logger.error(f"Error checking collisions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_recommendation(similarity_score: int, collision_type: str) -> str:
    """Generate user-friendly recommendation based on collision type and similarity"""
    if "identical" in collision_type:
        return "🔴 Files are completely identical. Recommend keeping existing file and skipping new one."
    elif "content_collision" in collision_type:
        return "🔴 Same file content with different names. Recommend keeping existing file to avoid duplication."
    elif "name_collision_different_content" in collision_type:
        return "🟠 Same filename with different content. Choose which version to keep."
    elif "name_collision" in collision_type:
        return "🟡 Files have same name. Choose to keep, skip, or rename one."
    else:
        return f"🟡 Potential collision detected ({similarity_score}%). Review both files."

@router.post("/resolve-collision")
async def resolve_collision(request: CollisionResolutionRequest):
    """
    Resolve a collision by choosing which file to keep
    """
    try:
        action = request.action
        keep_path = request.keep_file_path
        collision_id = request.collision_id
        
        if action == "keep_new":
            # Remove existing file
            if os.path.exists(keep_path):
                os.remove(keep_path)
                logger.info(f"Removed existing file: {keep_path}")
            return {
                "status": "resolved",
                "action": "removed_existing",
                "message": f"Removed existing file. New file will be organized."
            }
        
        elif action == "keep_existing":
            # Skip organizing new file
            logger.info(f"Skipping new file, keeping existing: {keep_path}")
            return {
                "status": "resolved",
                "action": "skipped_new",
                "message": f"Skipped new file, kept existing one."
            }
        
        elif action == "rename_new":
            # Rename new file
            if request.new_name:
                logger.info(f"Renaming new file to: {request.new_name}")
                return {
                    "status": "resolved",
                    "action": "renamed_new",
                    "new_name": request.new_name,
                    "message": f"New file will be renamed to: {request.new_name}"
                }
        
        elif action == "rename_existing":
            # Rename existing file
            if request.new_name:
                logger.info(f"Renaming existing file to: {request.new_name}")
                return {
                    "status": "resolved",
                    "action": "renamed_existing",
                    "new_name": request.new_name,
                    "message": f"Existing file will be renamed to: {request.new_name}"
                }
        
        raise HTTPException(status_code=400, detail="Invalid resolution action")
    
    except Exception as e:
        logger.error(f"Error resolving collision: {e}")
        raise HTTPException(status_code=500, detail=str(e))
