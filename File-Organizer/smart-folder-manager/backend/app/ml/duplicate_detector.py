"""
Duplicate detection using hash + image perceptual hashing
"""
import logging
from typing import List, Dict
from collections import defaultdict
import difflib
import hashlib
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class DuplicateDetector:
    """
    Detects duplicate and near-duplicate files using:
    1. Hash-based exact duplicate detection (strongest)
    2. Perceptual image hashing for visually identical images
    3. Filename-based similarity for near-duplicates
    """
    
    def __init__(self, similarity_threshold: float = 0.75):
        """
        Initialize detector
        similarity_threshold: 0-1, files above this are considered duplicates
        """
        self.similarity_threshold = similarity_threshold
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
        try:
            from PIL import Image
            self.Image = Image
            self.has_pil = True
        except ImportError:
            self.has_pil = False
            logger.warning("PIL not available - image perceptual hashing disabled")
    
    def find_duplicates(self, files: List[Dict]) -> List[Dict]:
        """
        Find duplicate files using multi-level detection
        Returns list of duplicate groups
        """
        if not files:
            return []
        
        duplicate_groups = []
        processed = set()
        
        # Step 1: Hash-based exact duplicate detection (STRONGEST)
        hash_map = defaultdict(list)
        for file_obj in files:
            file_hash = file_obj.get("hash", "").strip()
            # Only process non-empty hashes
            if file_hash and len(file_hash) > 0:
                hash_map[file_hash].append({
                    "name": file_obj["name"],
                    "path": file_obj.get("path", ""),
                    "full_obj": file_obj
                })
        
        # Create groups from exact hash matches
        for file_hash, file_entries in hash_map.items():
            if len(file_entries) > 1:
                filenames = [e["name"] for e in file_entries]
                group = {
                    "group_id": file_hash[:8],
                    "files": filenames,
                    "similarity_score": 1.0,  # Exact match via hash
                    "detection_method": "Hash-based (exact duplicate)"
                }
                duplicate_groups.append(group)
                processed.update(filenames)
                logger.info(f"✓ Found {len(filenames)} identical files via hash: {filenames[0]}")
        
        # Step 2: Perceptual image hashing for identical images (same visual content, different filenames)
        unprocessed_files = [f for f in files if f["name"] not in processed]
        image_files = [f for f in unprocessed_files if self._is_image(f.get("name", ""))]
        
        if self.has_pil and len(image_files) > 1:
            image_hash_map = defaultdict(list)
            for file_obj in image_files:
                file_path = file_obj.get("path", "")
                if file_path and os.path.exists(file_path):
                    perceptual_hash = self._get_image_hash(file_path)
                    if perceptual_hash:
                        image_hash_map[perceptual_hash].append(file_obj["name"])
            
            # Create groups from perceptual image matches
            for perceptual_hash, filenames in image_hash_map.items():
                if len(filenames) > 1:
                    group = {
                        "group_id": perceptual_hash[:8],
                        "files": filenames,
                        "similarity_score": 1.0,  # Visually identical
                        "detection_method": "Perceptual hash (visually identical images)"
                    }
                    duplicate_groups.append(group)
                    processed.update(filenames)
                    logger.info(f"✓ Found {len(filenames)} visually identical images: {filenames[0]}")
        
        # Step 3: Filename-based similarity for near-duplicates
        unprocessed_files = [f for f in files if f["name"] not in processed]
        
        for i, file1 in enumerate(unprocessed_files):
            if file1["name"] in processed:
                continue
            
            group = [file1["name"]]
            similarity_score = None
            
            for file2 in unprocessed_files[i+1:]:
                if file2["name"] in processed:
                    continue
                
                similarity = self._calculate_similarity(
                    file1["name"],
                    file2["name"]
                )
                
                if similarity >= self.similarity_threshold:
                    group.append(file2["name"])
                    similarity_score = similarity
                    processed.add(file2["name"])
            
            if len(group) > 1:
                processed.add(file1["name"])
                dup_group = {
                    "group_id": hashlib.md5("|".join(sorted(group)).encode()).hexdigest()[:8],
                    "files": group,
                    "similarity_score": similarity_score or self.similarity_threshold,
                    "detection_method": "Filename similarity"
                }
                duplicate_groups.append(dup_group)
                logger.info(f"✓ Found {len(group)} similar filenames: {group[0]}")
        
        logger.info(f"✓ Duplicate detection complete: {len(duplicate_groups)} groups found")
        return duplicate_groups
    
    def _is_image(self, filename: str) -> bool:
        """Check if file is an image"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.image_extensions
    
    def _get_image_hash(self, file_path: str) -> str:
        """
        Get perceptual hash of image for comparing visually identical images
        Uses average hash algorithm (simple but effective for identical images)
        """
        if not self.has_pil or not os.path.exists(file_path):
            return ""
        
        try:
            img = self.Image.open(file_path)
            
            # Resize to 8x8 for quick comparison
            img = img.resize((8, 8), self.Image.Resampling.LANCZOS)
            
            # Convert to grayscale
            img = img.convert('L')
            
            # Get pixel values
            pixels = list(img.getdata())
            
            # Calculate average
            avg = sum(pixels) / len(pixels)
            
            # Create hash: 1 if pixel > avg, 0 otherwise
            hash_bits = ''.join(['1' if p > avg else '0' for p in pixels])
            
            # Convert to hex
            return hex(int(hash_bits, 2))[2:].zfill(16)
        except Exception as e:
            logger.warning(f"Could not hash image {file_path}: {e}")
            return ""
    
    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """
        Calculate similarity between two filenames
        Uses SequenceMatcher for string similarity
        Returns: 0-1 similarity score
        """
        # Normalize names (remove extension, lowercase)
        base1 = self._normalize_filename(name1)
        base2 = self._normalize_filename(name2)
        
        # Calculate similarity ratio
        similarity = difflib.SequenceMatcher(None, base1, base2).ratio()
        
        return similarity
    
    def _normalize_filename(self, filename: str) -> str:
        """
        Normalize filename for comparison
        """
        # Remove extension
        if "." in filename:
            name = filename.rsplit(".", 1)[0]
        else:
            name = filename
        
        # Lowercase and remove spaces
        name = name.lower().replace(" ", "").replace("-", "").replace("_", "")
        
        return name
    
    def _tfidf_similarity(self, files: List[Dict]) -> Dict[str, float]:
        """
        TF-IDF based similarity (more sophisticated)
        Not currently used but available for future enhancement
        """
        # This would require scikit-learn
        # For now, using simpler difflib approach
        pass
