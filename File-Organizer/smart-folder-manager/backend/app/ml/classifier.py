"""
File classifier using rule-based, content-based and ML approaches
"""
import os
from typing import Tuple
import logging
import mimetypes
import json

logger = logging.getLogger(__name__)

class FileClassifier:
    """
    Classifies files into categories based on:
    1. File extension mapping (primary)
    2. File content analysis (secondary)
    3. Rule-based keyword matching
    4. MIME type detection
    """
    
    # Category keywords
    CATEGORY_KEYWORDS = {
        "Documents": ["document", "doc", "report", "pdf", "txt", "letter", "form", "resume", "cv", "proposal"],
        "Images": ["photo", "picture", "image", "screenshot", "jpeg", "jpg", "png", "gif", "visual"],
        "Videos": ["video", "movie", "film", "mp4", "avi", "mov", "mkv", "recording"],
        "Audio": ["music", "song", "audio", "podcast", "mp3", "wav", "flac", "voice"],
        "Code": ["code", "script", "programming", "python", "javascript", "java", "cpp", "src", "lib"],
        "Archives": ["zip", "rar", "7z", "tar", "gz", "compress", "backup"],
        "Spreadsheets": ["sheet", "excel", "csv", "xls", "xlsx", "data", "table", "calc"],
        "Presentations": ["presentation", "slide", "ppt", "pptx", "keynote", "odp"]
    }
    
    # File extension to category mapping
    EXTENSION_MAP = {
        # Documents
        "pdf": "Documents", "doc": "Documents", "docx": "Documents", "txt": "Documents",
        "odt": "Documents", "rtf": "Documents", "pages": "Documents", "tex": "Documents",
        "md": "Documents", "markdown": "Documents",
        
        # Images
        "jpg": "Images", "jpeg": "Images", "png": "Images", "gif": "Images",
        "bmp": "Images", "svg": "Images", "ico": "Images", "webp": "Images",
        "tiff": "Images", "psd": "Images", "ai": "Images",
        
        # Videos
        "mp4": "Videos", "avi": "Videos", "mov": "Videos", "mkv": "Videos",
        "flv": "Videos", "wmv": "Videos", "webm": "Videos", "m4v": "Videos",
        "m2ts": "Videos", "mts": "Videos",
        
        # Audio
        "mp3": "Audio", "wav": "Audio", "flac": "Audio", "aac": "Audio",
        "m4a": "Audio", "wma": "Audio", "ogg": "Audio", "aiff": "Audio",
        
        # Code
        "py": "Code", "js": "Code", "java": "Code", "cpp": "Code", "c": "Code",
        "h": "Code", "cs": "Code", "php": "Code", "rb": "Code", "go": "Code",
        "ts": "Code", "jsx": "Code", "tsx": "Code", "html": "Code", "css": "Code",
        "scss": "Code", "json": "Code", "xml": "Code", "yaml": "Code", "yml": "Code",
        "sh": "Code", "bash": "Code", "sql": "Code", "r": "Code", "pl": "Code",
        
        # Archives
        "zip": "Archives", "rar": "Archives", "7z": "Archives", "tar": "Archives",
        "gz": "Archives", "bz2": "Archives", "xz": "Archives", "iso": "Archives",
        
        # Spreadsheets
        "xls": "Spreadsheets", "xlsx": "Spreadsheets", "csv": "Spreadsheets",
        "ods": "Spreadsheets", "tsv": "Spreadsheets", "numbers": "Spreadsheets",
        
        # Presentations
        "ppt": "Presentations", "pptx": "Presentations", "odp": "Presentations",
        "key": "Presentations"
    }
    
    # Content signatures for file type detection
    CONTENT_SIGNATURES = {
        "pdf": (b"%PDF", "Documents"),
        "zip": (b"PK\x03\x04", "Archives"),
        "rar": (b"Rar!\x1a\x07", "Archives"),
        "gif": (b"GIF8", "Images"),
        "jpeg": (b"\xff\xd8\xff", "Images"),
        "png": (b"\x89PNG", "Images"),
        "mp3": (b"ID3", "Audio"),
        "mp4": (b"\x00\x00\x00\x20ftyp", "Videos"),
        "json": (b"{", "Code"),  # Often starts with {
    }

    def __init__(self):
        """Initialize classifier"""
        self.categories = list(set(self.EXTENSION_MAP.values()))
    
    def analyze_content(self, filepath: str) -> Tuple[str, float]:
        """
        Analyze file content to determine type
        Returns: (category, confidence)
        """
        try:
            if not os.path.exists(filepath) or not os.path.isfile(filepath):
                return "Uncategorized", 0.0
            
            file_size = os.path.getsize(filepath)
            
            # Don't analyze very large files
            if file_size > 10 * 1024 * 1024:  # 10MB
                return "Uncategorized", 0.0
            
            # Try to read file header for binary signature detection
            try:
                with open(filepath, 'rb') as f:
                    header = f.read(512)  # Read first 512 bytes
                
                # Check binary signatures
                for sig_bytes, category in self.CONTENT_SIGNATURES.values():
                    if header.startswith(sig_bytes):
                        return category, 0.92
            except:
                pass
            
            # Try to read as text for content analysis
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(5000)  # Read first 5KB
                
                content_lower = content.lower()
                
                # Code detection - look for programming patterns
                code_indicators = ['def ', 'function', 'class ', 'import ', 'require(', 
                                 'console.log', 'print(', 'return ', 'if ', 'for ',
                                 '<?php', '<%', '<%=', 'SELECT', 'INSERT', 'UPDATE']
                code_count = sum(1 for indicator in code_indicators if indicator in content_lower)
                if code_count >= 2:
                    return "Code", 0.85
                
                # JSON detection
                if content.strip().startswith('{') and '"' in content:
                    try:
                        json.loads(content)
                        return "Code", 0.90
                    except:
                        pass
                
                # CSV/TSV detection
                lines = content.split('\n')
                if len(lines) > 1:
                    first_line = lines[0]
                    if (',' in first_line or '\t' in first_line) and len(first_line.split(',')) > 2:
                        return "Spreadsheets", 0.80
                
                # Markdown detection
                if '# ' in content or '## ' in content or '[' in content and '](' in content:
                    return "Documents", 0.85
                
                # HTML/XML detection
                if content.strip().startswith('<') and ('html' in content_lower or 'xml' in content_lower):
                    return "Code", 0.88
                
                # Natural language text (likely document)
                word_count = len(content.split())
                if word_count > 20:
                    return "Documents", 0.75
                
            except Exception as e:
                logger.debug(f"Error analyzing text content: {e}")
                pass
            
            return "Uncategorized", 0.0
        
        except Exception as e:
            logger.warning(f"Error analyzing file content: {e}")
            return "Uncategorized", 0.0
    
    def classify(self, filename: str, filepath: str = "", extension: str = "") -> Tuple[str, float]:
        """
        Classify a file based on content, metadata, and extension
        Returns: (category, confidence)
        
        UPDATED PRIORITY:
        1. Content Analysis (92%+) - if filepath provided, analyze actual file content
        2. Filename Metadata/Keywords (85-92%) - extract meaning from filename
        3. MIME type detection (70%) - system MIME type detection
        4. Extension mapping (60%) - fallback to extension mapping
        5. Heuristics (50%) - simple pattern matching
        """
        confidence = 0.5
        category = "Uncategorized"
        
        # Get extension if not provided
        if not extension and "." in filename:
            extension = filename.split(".")[-1].lower()
        
        # RULE 1: CONTENT ANALYSIS (HIGHEST PRIORITY - 92%+ confidence)
        # If filepath provided, analyze actual file content
        if filepath and os.path.exists(filepath):
            content_category, content_confidence = self.analyze_content(filepath)
            if content_confidence > 0.7:
                logger.debug(f"Classified {filename} as {content_category} (CONTENT ANALYSIS, confidence: {content_confidence})")
                return content_category, content_confidence
        
        # RULE 2: FILENAME METADATA/KEYWORDS (85-92% confidence)
        # Use keyword matching in filename as high-priority secondary classification
        filename_lower = filename.lower()
        for cat, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    logger.debug(f"Classified {filename} as {cat} (METADATA KEYWORD: {keyword}, confidence: 0.88)")
                    return cat, 0.88
        
        # RULE 3: MIME TYPE DETECTION (70% confidence)
        # System-level MIME type detection
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            if 'image' in mime_type:
                logger.debug(f"Classified {filename} as Images (MIME TYPE, confidence: 0.70)")
                return "Images", 0.70
            elif 'video' in mime_type:
                logger.debug(f"Classified {filename} as Videos (MIME TYPE, confidence: 0.70)")
                return "Videos", 0.70
            elif 'audio' in mime_type:
                logger.debug(f"Classified {filename} as Audio (MIME TYPE, confidence: 0.70)")
                return "Audio", 0.70
            elif 'text' in mime_type:
                logger.debug(f"Classified {filename} as Documents (MIME TYPE, confidence: 0.70)")
                return "Documents", 0.70
        
        # RULE 4: EXTENSION MAPPING (60% confidence - REDUCED from 95%)
        # Extension is now a fallback, not primary classification method
        if extension and extension in self.EXTENSION_MAP:
            category = self.EXTENSION_MAP[extension]
            confidence = 0.60
            logger.debug(f"Classified {filename} as {category} (EXTENSION FALLBACK, confidence: {confidence})")
            return category, confidence
        
        # RULE 5: SIMPLE HEURISTICS (50% confidence)
        # Final fallback for unknown extensions that look programmatic
        if extension:
            if extension in ['py', 'js', 'java', 'go', 'rb']:
                category = "Code"
            elif extension in ['mp3', 'wav', 'flac', 'aac']:
                category = "Audio"
            elif extension in ['jpg', 'png', 'gif', 'webp']:
                category = "Images"
            elif extension in ['mp4', 'mov', 'avi', 'mkv']:
                category = "Videos"
            
            if category != "Uncategorized":
                logger.debug(f"Classified {filename} as {category} (HEURISTIC, confidence: 0.50)")
                return category, 0.50
        
        logger.debug(f"Could not classify {filename}, returning Uncategorized")
        return category, confidence
