#!/usr/bin/env python3
"""
Transfer logs from action_history.json to MongoDB
Imports all historical file movements into MongoDB Compass
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.mongo_client import get_file_movements_collection

def load_action_history():
    """Load action history from JSON file"""
    history_file = "backend/app/logs/action_history.json"
    
    if not os.path.exists(history_file):
        print(f"ERROR: {history_file} not found")
        return []
    
    try:
        with open(history_file, 'r') as f:
            actions = json.load(f)
        print(f"Loaded {len(actions)} actions from {history_file}")
        return actions
    except Exception as e:
        print(f"ERROR reading {history_file}: {e}")
        return []

def transfer_to_mongodb(actions):
    """Transfer actions to MongoDB"""
    collection = get_file_movements_collection()
    
    if not collection:
        print("ERROR: Could not connect to MongoDB")
        print("Make sure MongoDB is running:")
        print("  brew services start mongodb-community")
        return False
    
    # Check if collection already has data
    existing_count = collection.count_documents({})
    if existing_count > 0:
        print(f"WARNING: Collection already has {existing_count} documents")
        response = input("Overwrite? (y/n): ")
        if response.lower() == 'y':
            collection.delete_many({})
            print("Cleared existing documents")
        else:
            print("Aborting transfer")
            return False
    
    # Convert and insert
    inserted = 0
    failed = 0
    
    for action in actions:
        try:
            # Convert timestamp string to datetime
            timestamp_str = action.get("timestamp", "")
            try:
                # Handle ISO format timestamps
                if 'T' in timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    timestamp = datetime.now()
            except:
                timestamp = datetime.now()
            
            # Prepare document for MongoDB
            doc = {
                "_id": action.get("id"),
                "id": action.get("id"),
                "type": action.get("type", "move"),
                "filename": action.get("filename", ""),
                "from_path": action.get("from_path", ""),
                "to_path": action.get("to_path", ""),
                "category": action.get("category", ""),
                "confidence": action.get("confidence", 0.0),
                "folder_source": action.get("folder_source", "category"),
                "timestamp": timestamp
            }
            
            collection.insert_one(doc)
            inserted += 1
            
            # Print progress every 100 documents
            if inserted % 100 == 0:
                print(f"  Transferred {inserted} documents...")
        
        except Exception as e:
            failed += 1
            if failed <= 5:  # Show first 5 errors
                print(f"  WARNING: Failed to insert action {action.get('id')}: {e}")
    
    print(f"\nTransfer complete:")
    print(f"  Successfully inserted: {inserted}")
    print(f"  Failed: {failed}")
    
    # Show summary stats
    try:
        total = collection.count_documents({})
        print(f"  Total in MongoDB: {total}")
        
        # Category breakdown
        categories = collection.aggregate([
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ])
        
        print(f"\nBreakdown by category:")
        for cat in categories:
            print(f"  {cat['_id']}: {cat['count']}")
    
    except Exception as e:
        print(f"Could not fetch stats: {e}")
    
    return inserted > 0

def main():
    print("=" * 60)
    print("Transfer Action History to MongoDB")
    print("=" * 60)
    print()
    
    # Load from JSON
    print("Step 1: Loading action history from JSON...")
    actions = load_action_history()
    
    if not actions:
        print("No actions to transfer")
        return
    
    print()
    print("Step 2: Transferring to MongoDB...")
    print()
    
    success = transfer_to_mongodb(actions)
    
    print()
    print("=" * 60)
    if success:
        print("SUCCESS: Data transferred to MongoDB")
        print()
        print("View in MongoDB Compass:")
        print("  Database: smart_file_organizer")
        print("  Collection: file_movements")
    else:
        print("FAILED: Could not transfer data")
    print("=" * 60)

if __name__ == "__main__":
    main()
