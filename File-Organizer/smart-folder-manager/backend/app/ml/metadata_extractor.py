"""
Metadata extractor for smart folder naming
Extracts meaningful folder names from file names based on patterns, keywords, and subject analysis
"""
import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """
    Extracts folder names from filenames based on patterns and metadata
    Intelligently reads all metadata and creates folders based on content similarity
    
    Examples:
        - screenshot_1234.png -> "screenshot"
        - document_final_v2.pdf -> "document"
        - CSC314-Design-and-Analysis-of-Algorithms Syllabus -> "DAA"
        - Unit 1 - Introduction and Classical Ciphers - Crypto -> "Crypto"
    """
    
    # Common prefix patterns (at the beginning)
    PREFIX_PATTERNS = {
        "screenshot": r"^screenshot(?:_|\.)",
        "photo": r"^photo(?:_|\.)",
        "image": r"^image(?:_|\.)",
        "document": r"^document(?:_|\.)",
        "invoice": r"^invoice(?:_|\.)",
        "receipt": r"^receipt(?:_|\.)",
        "report": r"^report(?:_|\.)",
        "contract": r"^contract(?:_|\.)",
        "video": r"^video(?:_|\.)",
        "audio": r"^audio(?:_|\.)",
        "music": r"^music(?:_|\.)",
        "project": r"^project(?:_|\.)",
        "assignment": r"^assignment(?:_|\.)",
        "backup": r"^backup(?:_|\.)",
        "scan": r"^scan(?:_|\.)",
        "export": r"^export(?:_|\.)",
        "download": r"^download(?:_|\.)",
        "archive": r"^archive(?:_|\.)",
    }
    
    # Course subject abbreviation mappings based on keywords
    SUBJECT_MAPPINGS = {
        "DAA": [
            r"Design\s+and\s+Analysis\s+of\s+Algorithms",
            r"Data\s+Structures\s+and\s+Algorithms",
            r"Algorithm\s+Design",
            r"Analysis\s+of\s+Algorithms"
        ],
        "Crypto": [
            r"Cryptography|Cryptographic",
            r"Classical\s+Ciphers",
            r"Cipher",
            r"Encryption",
        ],
        "DBMS": [
            r"Database\s+Management\s+System",
            r"Database\s+Management",
            r"Database\s+System",
            r"Relational\s+Database",
            r"SQL"
        ],
        "OOP": [
            r"Object\s+Oriented\s+Programming",
            r"Object-Oriented",
            r"OOP"
        ],
        "Web": [
            r"Web\s+Development",
            r"Web\s+Design",
            r"HTML|CSS|JavaScript"
        ],
        "AI": [
            r"Artificial\s+Intelligence",
            r"Machine\s+Learning",
            r"Deep\s+Learning"
        ],
        "Networking": [
            r"Computer\s+Networks?",
            r"Network\s+Programming",
            r"TCP|UDP|HTTP"
        ],
        "Security": [
            r"Cybersecurity|Cyber\s+Security",
            r"Information\s+Security",
            r"Network\s+Security"
        ]
    }
    
    # Keywords that can appear anywhere in the name (high priority)
    KEYWORD_PATTERNS = {
        "Crypto": r"(?:^|-\s|_)Crypto(?:graphy|graphic)?(?:\s|$|-)",
        "Cryptography": r"(?:^|-\s|_)Crypto(?:graphy)?(?:\s|$|-)",
        "Security": r"(?:^|-\s|_)Security(?:\s|$|-)",
        "Networking": r"(?:^|-\s|_)Network(?:ing)?(?:\s|$|-)",
        "Database": r"(?:^|-\s|_)Database(?:\s|$|-)",
        "Web": r"(?:^|-\s|_)Web(?:Development)?(?:\s|$|-)",
        "Mobile": r"(?:^|-\s|_)Mobile(?:\s|$|-)",
        "AI": r"(?:^|-\s|_)(?:AI|Artificial Intelligence)(?:\s|$|-)",
        "Machine Learning": r"(?:^|-\s|_)Machine\s+Learning(?:\s|$|-)",
        "Data Science": r"(?:^|-\s|_)Data\s+Science(?:\s|$|-)",
        "Cloud": r"(?:^|-\s|_)Cloud(?:\s|$|-)",
        "DevOps": r"(?:^|-\s|_)DevOps(?:\s|$|-)",
        "Frontend": r"(?:^|-\s|_)Frontend(?:\s|$|-)",
        "Backend": r"(?:^|-\s|_)Backend(?:\s|$|-)",
        "Tutorial": r"(?:^|-\s|_)Tutorial(?:\s|$|-)",
        "Lecture": r"(?:^|-\s|_)Lecture(?:\s|$|-)",
        "Assignment": r"(?:^|-\s|_)Assignment(?:\s|$|-)",
    }
    
    @staticmethod
    def extract_folder_name(filename: str) -> Tuple[str, float]:
        """
        Extract folder name from filename based on pattern recognition
        Reads ALL metadata and finds best matching subject based on similarity
        
        Args:
            filename: The file name to extract metadata from
            
        Returns:
            Tuple of (folder_name, confidence)
            - folder_name: Suggested folder name
            - confidence: Confidence score (0.0-1.0)
        """
        # Remove extension
        name_without_ext = filename.rsplit(".", 1)[0] if "." in filename else filename
        name_lower = name_without_ext.lower()
        
        # Step 1: Try exact pattern matching at the beginning (highest priority)
        for prefix, pattern in MetadataExtractor.PREFIX_PATTERNS.items():
            if re.match(pattern, name_lower):
                return prefix, 0.95
        
        # Step 2: Try subject mapping (check if course title contains subject keywords)
        for subject, patterns in MetadataExtractor.SUBJECT_MAPPINGS.items():
            for pattern in patterns:
                if re.search(pattern, name_without_ext, re.IGNORECASE):
                    return subject, 0.93
        
        # Step 3: Try keyword patterns anywhere in the name (high priority)
        for keyword, pattern in MetadataExtractor.KEYWORD_PATTERNS.items():
            if re.search(pattern, name_without_ext, re.IGNORECASE):
                return keyword, 0.92
        
        # Step 4: Try course code extraction (CSC314 -> extract meaningful abbreviation from full title)
        # Pattern: COURSEXX- or COURSEXX- followed by descriptive text
        course_match = re.match(r"^([A-Z]+\d+)[- ](.+)$", name_without_ext)
        if course_match:
            course_code = course_match.group(1)
            course_title = course_match.group(2)
            
            # Check if course title matches any subject
            for subject, patterns in MetadataExtractor.SUBJECT_MAPPINGS.items():
                for pattern in patterns:
                    if re.search(pattern, course_title, re.IGNORECASE):
                        return subject, 0.91
            
            # If no subject found, try to extract from course title words
            title_words = re.split(r'[- ]', course_title)
            significant_words = [w for w in title_words if len(w) > 3 and w.lower() not in ['and', 'the', 'for', 'with', 'from', 'about']]
            
            if significant_words:
                # Try to create abbreviation from first few significant words
                abbrev = ''.join([w[0].upper() for w in significant_words[:3]])
                if len(abbrev) <= 4 and len(abbrev) >= 2:
                    return abbrev, 0.88
                elif len(significant_words) > 0:
                    return significant_words[0], 0.85
        
        # Step 5: Try simple underscore/dash splitting
        # Extract prefix before first number or underscore
        match = re.match(r"^([a-z_-]+?)(?:_|\d|-|\s)", name_lower)
        if match:
            prefix = match.group(1).replace("_", " ").title()
            # Clean up the prefix
            prefix = re.sub(r'[_-]', ' ', prefix).strip()
            if len(prefix) > 2:  # Minimum prefix length
                return prefix, 0.80
        
        # Step 6: Try CamelCase splitting
        match = re.match(r"^([A-Z][a-z]+)", name_without_ext)
        if match:
            prefix = match.group(1)
            return prefix, 0.75
        
        # Step 7: Default: use first word if has multiple words
        words = re.split(r'[\s_-]+', name_lower)
        if len(words) > 1 and len(words[0]) > 2:
            prefix = words[0].title()
            return prefix, 0.70
        
        # Step 8: Extract last meaningful word (useful for "Unit X - ... - Topic" patterns)
        words = [w.strip() for w in re.split(r'[-_]', name_without_ext) if w.strip()]
        if len(words) > 1:
            last_word = words[-1].strip()
            # Only use last word if it's meaningful (not just numbers)
            if last_word and not re.match(r'^\d+$', last_word) and len(last_word) > 2:
                return last_word, 0.68
        
        # Step 9: For files with only numbers/hashes (like screenshots), create a generic folder
        # This handles cases like: 1234567890.png, abc123def456.jpeg, etc.
        # For such files, we'll return the filename itself (without extension) as a unique folder
        if len(name_without_ext) > 0 and not re.match(r'^[a-zA-Z_]', name_without_ext):
            # This is a number/hash starting file
            # Extract first meaningful part if it contains letters
            if re.search(r'[a-zA-Z]', name_without_ext):
                letters_match = re.search(r'([a-zA-Z_]+)', name_without_ext)
                if letters_match:
                    return letters_match.group(1), 0.65
        
        # Step 10: Use full filename as folder if it's not just numbers
        if name_without_ext and not re.match(r'^\d+$', name_without_ext):
            # Clean up the name for use as folder
            clean_name = re.sub(r'[_-]', ' ', name_without_ext).title()
            if len(clean_name) > 2:
                return clean_name, 0.60
        
        # No clear metadata found
        return "", 0.0
    
    @staticmethod
    def extract_base_name(filename: str) -> str:
        """
        Extract the base name (prefix) from filename
        
        Examples:
            - screenshot_1234.png -> screenshot
            - photo_2024_01_15.jpg -> photo
            - document_final_v2.pdf -> document
        """
        folder_name, _ = MetadataExtractor.extract_folder_name(filename)
        return folder_name
    
    @staticmethod
    def extract_folder_name_with_content(filename: str, filepath: str = "") -> Tuple[str, float]:
        """
        Extract folder name from filename using BOTH METADATA and FILE CONTENT
        
        This enhanced method analyzes file content to improve metadata extraction,
        especially useful for files where content type differs from extension.
        
        Args:
            filename: The file name to extract metadata from
            filepath: Optional path to file for content analysis
            
        Returns:
            Tuple of (folder_name, confidence)
        """
        import os
        
        # First try standard filename-based extraction
        folder_name, confidence = MetadataExtractor.extract_folder_name(filename)
        
        # If we have a filepath and content analysis is possible, enhance detection
        if filepath and os.path.exists(filepath) and confidence < 0.85:
            try:
                file_size = os.path.getsize(filepath)
                # Only analyze reasonably sized files
                if file_size < 10 * 1024 * 1024:  # 10MB limit
                    try:
                        # Try to read file content
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read(5000)  # First 5KB
                        
                        content_lower = content.lower()
                        
                        # Enhance metadata based on content patterns
                        if "cryptography" in content_lower or "cipher" in content_lower or "encryption" in content_lower:
                            if confidence < 0.92:
                                return "Crypto", 0.90
                        
                        if "database" in content_lower or "sql" in content_lower or "query" in content_lower:
                            if confidence < 0.92:
                                return "DBMS", 0.88
                        
                        if "api" in content_lower or "endpoint" in content_lower or "rest" in content_lower:
                            if confidence < 0.92:
                                return "API", 0.87
                        
                        if "network" in content_lower or "socket" in content_lower or "tcp" in content_lower or "udp" in content_lower:
                            if confidence < 0.92:
                                return "Networking", 0.87
                        
                        if "machine learning" in content_lower or "neural" in content_lower or "model" in content_lower:
                            if confidence < 0.92:
                                return "ML", 0.85
                    except:
                        pass  # Content analysis failed, use filename-based only
            except:
                pass  # File access failed, use filename-based only
        
        # Return original filename-based extraction
        return folder_name, confidence
