#!/usr/bin/env python3
"""
Test script to verify duplicate detection fix for identical images
"""
import requests
import json
import os
from pathlib import Path

# Test with Desktop folder (where you have the 2 dog images)
test_folder = "/Users/pranil/Desktop"

print("=" * 60)
print("DUPLICATE DETECTION TEST")
print("=" * 60)
print(f"\nScanning folder: {test_folder}")

# Step 1: Scan the folder
print("\n[1/2] Scanning folder for files...")
scan_response = requests.post(
    "http://localhost:8000/api/scan-folder/",
    json={"folder_path": test_folder}
)

if scan_response.status_code != 200:
    print(f"❌ Scan failed: {scan_response.text}")
    exit(1)

scan_data = scan_response.json()
files = scan_data.get("files", [])
print(f"✓ Found {len(files)} files")

# Show files
print("\nFiles found:")
for i, f in enumerate(files[:10]):  # Show first 10
    print(f"  {i+1}. {f['name']} (hash: {f.get('hash', 'N/A')[:8]}...)")
if len(files) > 10:
    print(f"  ... and {len(files) - 10} more")

# Step 2: Run duplicate detection
print(f"\n[2/2] Running duplicate detection on {len(files)} files...")
dup_response = requests.post(
    "http://localhost:8000/api/detect-duplicates/",
    json={"files": files}
)

if dup_response.status_code != 200:
    print(f"❌ Duplicate detection failed: {dup_response.text}")
    exit(1)

dup_data = dup_response.json()
groups = dup_data.get("duplicate_groups", [])

print(f"\n✓ Duplicate detection complete\n")
print("=" * 60)

if not groups:
    print("✓ No duplicates found (this is expected for unique files)")
else:
    print(f"🔍 Found {len(groups)} duplicate group(s)\n")
    
    for i, group in enumerate(groups, 1):
        print(f"Group {i}:")
        print(f"  Detection method: {group.get('detection_method', 'Unknown')}")
        print(f"  Similarity score: {group['similarity_score']:.2f}")
        print(f"  Files ({len(group['files'])}):")
        for filename in group['files']:
            print(f"    - {filename}")
        print()

# Show stats
total_dups = dup_data.get("total_duplicates", 0)
print("=" * 60)
print(f"Total duplicate files: {total_dups}")
print(f"Total groups: {len(groups)}")
print("=" * 60)

# Test specifically for dog images
print("\n" + "=" * 60)
print("LOOKING FOR DOG IMAGE DUPLICATES...")
print("=" * 60)

dog_files = [f for f in files if 'dog' in f['name'].lower()]
print(f"\nFound {len(dog_files)} file(s) with 'dog' in name:")
for f in dog_files:
    print(f"  - {f['name']}")
    print(f"    Path: {f['path']}")
    print(f"    Hash: {f.get('hash', 'N/A')[:16]}...")

if len(dog_files) >= 2:
    # Check if they have same hash
    hash1 = dog_files[0].get('hash', '')
    hash2 = dog_files[1].get('hash', '')
    
    if hash1 and hash2:
        if hash1 == hash2:
            print(f"\n✓ DUPLICATE DOG IMAGES DETECTED!")
            print(f"  Both have hash: {hash1[:16]}...")
        else:
            print(f"\n❌ Dog images have DIFFERENT hashes:")
            print(f"  File 1: {hash1[:16]}...")
            print(f"  File 2: {hash2[:16]}...")
    else:
        print("\n⚠ One or both dog images don't have hash (hashing might have failed)")

print("\n" + "=" * 60)
