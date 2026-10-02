"""
Random filename detector
Identifies files with random names (numbers, hashes, UUIDs) that should be renamed
"""
import re
from typing import Tuple

class RandomFilenameDetector:
    """
    Detects if a filename appears to be random/meaningless
    Examples of random names:
    - 47f1b200-8b2e-11ea-8fa1-ab106189aeb0.jpeg (UUID)
    - 1234567890.png (timestamp)
    - abc123def456.jpg (random letters+numbers)
    - a1b2c3d4e5f6.pdf (alternating random)
    
    Returns: (is_random, confidence)
    """
    
    # UUID pattern
    UUID_PATTERN = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
    
    # Unix timestamp pattern (10 digits)
    TIMESTAMP_PATTERN = r'^\d{10}(\.\d+)?$'
    
    # Hash patterns (MD5, SHA1, SHA256)
    MD5_PATTERN = r'^[a-f0-9]{32}$'
    SHA1_PATTERN = r'^[a-f0-9]{40}$'
    SHA256_PATTERN = r'^[a-f0-9]{64}$'
    
    # Random hex string pattern (long hex without meaningful structure)
    LONG_HEX_PATTERN = r'^[a-f0-9]{16,}$'
    
    # Random alphanumeric (lots of letters and numbers mixed)
    RANDOM_ALPHANUMERIC_PATTERN = r'^[a-zA-Z0-9]{12,}$'
    
    @staticmethod
    def is_random_filename(filename: str) -> Tuple[bool, float, str]:
        """
        Check if filename appears to be random
        
        Args:
            filename: The filename to check (without extension)
            
        Returns:
            Tuple of (is_random, confidence_score, reason)
            - is_random: True if filename appears random
            - confidence_score: 0.0-1.0 confidence that it's random
            - reason: Why it's considered random (UUID, timestamp hash, etc.)
        """
        # Remove extension
        name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        name_lower = name.lower()
        
        # Check for UUID
        if re.match(RandomFilenameDetector.UUID_PATTERN, name_lower):
            return True, 0.95, "UUID format"
        
        # Check for MD5/SHA hashes
        if re.match(RandomFilenameDetector.MD5_PATTERN, name_lower):
            return True, 0.92, "MD5 hash"
        if re.match(RandomFilenameDetector.SHA1_PATTERN, name_lower):
            return True, 0.92, "SHA1 hash"
        if re.match(RandomFilenameDetector.SHA256_PATTERN, name_lower):
            return True, 0.92, "SHA256 hash"
        
        # Check for Unix timestamp
        if re.match(RandomFilenameDetector.TIMESTAMP_PATTERN, name):
            return True, 0.85, "Unix timestamp"
        
        # Check for long hex strings
        if len(name) > 15 and re.match(RandomFilenameDetector.LONG_HEX_PATTERN, name_lower):
            return True, 0.88, "Hex string"
        
        # Check for random alphanumeric (all letters/numbers, mixed, no clear words)
        if len(name) >= 12 and re.match(RandomFilenameDetector.RANDOM_ALPHANUMERIC_PATTERN, name):
            # Check if it contains mostly vowels OR mostly consonants (not a real word pattern)
            vowels = sum(1 for c in name_lower if c in 'aeiou')
            consonants = sum(1 for c in name_lower if c.isalpha() and c not in 'aeiou')
            total_letters = vowels + consonants
            
            if total_letters > 0:
                vowel_ratio = vowels / total_letters
                # Real words typically have 35-45% vowels
                # Random names are usually outside this range
                if vowel_ratio < 0.20 or vowel_ratio > 0.70:
                    return True, 0.75, "Random alphanumeric (unnatural vowel distribution)"
        
        # Check for common patterns that indicate random generation
        # Pattern: alternating or highly mixed letters and numbers
        if len(name) >= 8:
            # Count transitions between letters and numbers
            transitions = 0
            for i in range(len(name) - 1):
                curr_is_letter = name[i].isalpha()
                next_is_letter = name[i+1].isalpha()
                if curr_is_letter != next_is_letter:
                    transitions += 1
            
            transition_ratio = transitions / (len(name) - 1) if len(name) > 1 else 0
            
            # Real filenames have fewer transitions
            # Random names have high transition frequency
            if transition_ratio > 0.5:  # More than 50% transitions = likely random
                return True, 0.72, "Highly fragmented name (letters and numbers alternating)"
        
        return False, 0.0, ""
    
    @staticmethod
    def suggest_meaningful_name(filename: str) -> str:
        """
        Suggest a meaningful name for a random filename
        Based on file type and timestamp if available
        """
        # Remove extension
        name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        ext = filename.rsplit('.', 1)[1] if '.' in filename else ""
        
        # Extract timestamp if present
        timestamp_match = re.search(r'\d{10}', name)
        if timestamp_match:
            from datetime import datetime
            try:
                timestamp = int(timestamp_match.group())
                dt = datetime.fromtimestamp(timestamp)
                suggested = f"File_{dt.strftime('%Y%m%d_%H%M%S')}"
                if ext:
                    suggested = f"{suggested}.{ext}"
                return suggested
            except:
                pass
        
        # Generic suggestion based on file type
        if ext:
            file_type_map = {
                'jpg': 'Photo', 'jpeg': 'Photo', 'png': 'Image', 'gif': 'Image',
                'mp4': 'Video', 'mov': 'Video', 'avi': 'Video',
                'mp3': 'Audio', 'wav': 'Audio', 'flac': 'Audio',
                'pdf': 'Document', 'docx': 'Document', 'txt': 'Document',
                'zip': 'Archive', 'rar': 'Archive', '7z': 'Archive',
            }
            file_type = file_type_map.get(ext.lower(), 'File')
            return f"{file_type}_1.{ext}"
        
        return "Renamed_File"
