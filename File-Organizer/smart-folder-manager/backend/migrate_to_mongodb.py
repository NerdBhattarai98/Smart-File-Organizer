"""
Migration script to move action history from JSON to MongoDB
This script transfers all file movement records from action_history.json to MongoDB
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "smart_file_organizer"
COLLECTION_NAME = "file_movements"

# File paths
JSON_HISTORY_PATH = Path(__file__).parent / "app" / "logs" / "action_history.json"

def migrate_to_mongodb():
    """Migrate action history from JSON to MongoDB"""
    
    print("=" * 60)
    print("FILE MOVEMENT HISTORY MIGRATION")
    print("=" * 60)
    
    # Connect to MongoDB
    try:
        print("\n1. Connecting to MongoDB...")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        print("   ✅ Connected to MongoDB successfully")
    except ServerSelectionTimeoutError as e:
        print(f"   ❌ Failed to connect to MongoDB: {e}")
        print("   Make sure MongoDB is running on localhost:27017")
        return False
    
    try:
        # Get database and collection
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Read JSON history
        print(f"\n2. Reading action history from {JSON_HISTORY_PATH}...")
        if not JSON_HISTORY_PATH.exists():
            print(f"    File not found: {JSON_HISTORY_PATH}")
            return False
        
        with open(JSON_HISTORY_PATH, 'r') as f:
            actions = json.load(f)
        
        print(f"    Found {len(actions)} action records")
        
        # Prepare documents for insertion
        print("\n3. Preparing documents for migration...")
        documents = []
        
        for action in actions:
            # Only include file movement records (exclude undo records)
            if action.get("type") != "undo":
                doc = {
                    "id": action.get("id"),
                    "type": action.get("type", "move"),
                    "filename": action.get("filename"),
                    "from_path": action.get("from_path"),
                    "to_path": action.get("to_path"),
                    "category": action.get("category"),
                    "confidence": action.get("confidence"),
                    "folder_source": action.get("folder_source", "classifier"),
                    "timestamp": action.get("timestamp"),
                    "migrated_at": datetime.now()
                }
                documents.append(doc)
        
        print(f"   ✅ Prepared {len(documents)} documents for migration")
        print(f"      (Excluded {len(actions) - len(documents)} undo records)")
        
        # Clear existing collection (optional - comment out to keep existing data)
        print("\n4. Clearing existing collection...")
        existing_count = collection.count_documents({})
        if existing_count > 0:
            collection.delete_many({"type": {"$ne": "undo"}})
            print(f"   ✅ Cleared {existing_count} existing records")
        else:
            print("   ✅ Collection is empty")
        
        # Insert documents
        print("\n5. Inserting documents into MongoDB...")
        if documents:
            result = collection.insert_many(documents)
            print(f"   ✅ Successfully inserted {len(result.inserted_ids)} documents")
        else:
            print("   ⚠️  No documents to insert")
        
        # Create indexes for better query performance
        print("\n6. Creating indexes...")
        collection.create_index("timestamp")
        collection.create_index("filename")
        collection.create_index("category")
        collection.create_index("from_path")
        collection.create_index("to_path")
        print("   ✅ Indexes created successfully")
        
        # Verify migration
        print("\n7. Verifying migration...")
        total_docs = collection.count_documents({})
        move_docs = collection.count_documents({"type": "move"})
        print(f"   ✅ Total documents in MongoDB: {total_docs}")
        print(f"   ✅ File movement records: {move_docs}")
        
        # Show sample record
        sample = collection.find_one({"type": "move"})
        if sample:
            print(f"\n   Sample record:")
            print(f"   - Filename: {sample.get('filename')}")
            print(f"   - From: {sample.get('from_path')}")
            print(f"   - To: {sample.get('to_path')}")
            print(f"   - Category: {sample.get('category')}")
            print(f"   - Timestamp: {sample.get('timestamp')}")
        
        print("\n" + "=" * 60)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nYou can now view your file movements in MongoDB Compass:")
        print(f"Database: {DATABASE_NAME}")
        print(f"Collection: {COLLECTION_NAME}")
        print("\nNote: Your JSON history file is still available at:")
        print(f"{JSON_HISTORY_PATH}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        client.close()
        print("\nClosed MongoDB connection")

if __name__ == "__main__":
    success = migrate_to_mongodb()
    sys.exit(0 if success else 1)
