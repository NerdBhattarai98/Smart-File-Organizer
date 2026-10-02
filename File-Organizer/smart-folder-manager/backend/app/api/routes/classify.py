"""
File classification module
Uses ML models to predict file categories and extract metadata for organization
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import logging
from app.ml.classifier import FileClassifier
from app.ml.metadata_extractor import MetadataExtractor
from app.ml.random_detector import RandomFilenameDetector

logger = logging.getLogger(__name__)
router = APIRouter()

class ClassificationResult(BaseModel):
    filename: str
    predicted_category: str
    confidence: float
    metadata_folder: Optional[str] = None
    metadata_confidence: Optional[float] = None
    similar_files: Optional[List[str]] = None
    is_random_name: Optional[bool] = None
    random_reason: Optional[str] = None
    suggested_name: Optional[str] = None

class ClassifyResponse(BaseModel):
    status: str
    results: List[ClassificationResult]

# Initialize classifiers
classifier = FileClassifier()
metadata_extractor = MetadataExtractor()

@router.post("/")
async def classify_files(request: dict):
    """
    Classify files using ML models with content analysis
    RETURNS BOTH:
    1. Category (from file type detection)
    2. Metadata folder (from filename metadata extraction)
    
    Organization should use metadata_folder primarily, category as fallback
    """
    try:
        files = request.get("files", [])
        
        if not files:
            return ClassifyResponse(status="success", results=[])
        
        results = []
        
        for file_obj in files:
            filename = file_obj.get("name", "")
            filepath = file_obj.get("path", "")
            extension = file_obj.get("extension", "")
            
            # Check if filename is random/meaningless
            is_random, random_confidence, random_reason = RandomFilenameDetector.is_random_filename(filename)
            suggested_name = None
            if is_random and random_confidence > 0.70:
                suggested_name = RandomFilenameDetector.suggest_meaningful_name(filename)
            
            # Get file type classification (based on content/metadata/extension)
            category, confidence = classifier.classify(
                filename=filename,
                filepath=filepath,
                extension=extension
            )
            
            # Get metadata folder name (for organization)
            # Uses content analysis if filepath is provided
            metadata_folder, metadata_confidence = MetadataExtractor.extract_folder_name_with_content(
                filename, 
                filepath
            )
            
            result = ClassificationResult(
                filename=filename,
                predicted_category=category,
                confidence=confidence,
                metadata_folder=metadata_folder if metadata_folder else None,
                metadata_confidence=metadata_confidence if metadata_folder else None,
                similar_files=[],
                is_random_name=is_random and random_confidence > 0.70,
                random_reason=random_reason if (is_random and random_confidence > 0.70) else None,
                suggested_name=suggested_name
            )
            results.append(result)
        
        logger.info(f"Classified {len(results)} files with metadata extraction")
        
        return ClassifyResponse(
            status="success",
            results=results
        )
    
    except Exception as e:
        logger.error(f"Error classifying files: {e}")
        return ClassifyResponse(status="error", results=[])
