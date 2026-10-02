"""
Test script for metadata extraction
Demonstrates how filenames are mapped to folder names
"""
from app.ml.metadata_extractor import MetadataExtractor


def test_metadata_extraction():
    """Test various filename patterns"""
    test_files = [
        "screenshot_1234.png",
        "screenshot_2024_01_15.jpg",
        "photo_vacation_2024.jpg",
        "document_final_v2.pdf",
        "invoice_2024_001.xlsx",
        "receipt_amazon_2024.pdf",
        "report_quarterly_Q1.docx",
        "contract_agreement_2024.pdf",
        "video_recording_001.mp4",
        "music_favorite_song.mp3",
        "project_presentation.pptx",
        "assignment_homework.pdf",
        "backup_database_20240115.zip",
        "scan_document_page1.pdf",
        "export_data_2024.csv",
        "download_archive.zip",
    ]
    
    print("=" * 80)
    print("METADATA EXTRACTION TEST")
    print("=" * 80)
    print()
    
    for filename in test_files:
        folder_name, confidence = MetadataExtractor.extract_folder_name(filename)
        
        status = "✓" if confidence > 0.7 else "?"
        print(f"{status} {filename:40} -> {folder_name:20} (confidence: {confidence:.2f})")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    test_metadata_extraction()
