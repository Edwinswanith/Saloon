"""
Clone MongoDB database structure (collections, indexes) and all data.

Usage:
    python clone_structure.py
"""

import os
from pymongo import MongoClient

# MongoDB Configuration
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
SOURCE_DB = "Saloon"
TARGET_DB = "Saloon_prod"

def build_connection_uri(base_uri, db_name):
    """Build connection URI with database name."""
    # If URI contains a database path, remove it
    if '@' in base_uri:
        parts = base_uri.split('@')
        if len(parts) == 2:
            credentials = parts[0]
            host_and_params = parts[1]
            
            # Remove database name from host part if present
            if '/' in host_and_params:
                host = host_and_params.split('/')[0]
                # Keep query parameters if they exist
                if '?' in host_and_params:
                    params = '?' + host_and_params.split('?', 1)[1]
                else:
                    params = ''
                base_uri = f"{credentials}@{host}{params}"
    
    # Add database name to URI if not present
    if f'/{db_name}' not in base_uri:
        if '?' in base_uri:
            base_uri = base_uri.replace('?', f'/{db_name}?')
        else:
            base_uri = f"{base_uri}/{db_name}"
    
    # Add retry parameters if not present
    if 'retryWrites' not in base_uri:
        separator = '&' if '?' in base_uri else '?'
        base_uri = f"{base_uri}{separator}retryWrites=true&w=majority"
    
    return base_uri

def clone_database_structure():
    """Clone database structure (collections, indexes) and all data."""
    print("="*60)
    print("MONGODB DATABASE CLONING (STRUCTURE + DATA)")
    print("="*60)
    print(f"\nSource Database: {SOURCE_DB}")
    print(f"Target Database: {TARGET_DB}")
    
    # Build connection URI (connect to admin database first)
    base_uri = MONGODB_URI
    if '@' in base_uri:
        parts = base_uri.split('@')
        if len(parts) == 2:
            credentials = parts[0]
            host_and_params = parts[1]
            if '/' in host_and_params:
                host = host_and_params.split('/')[0]
                if '?' in host_and_params:
                    params = '?' + host_and_params.split('?', 1)[1]
                else:
                    params = ''
                base_uri = f"{credentials}@{host}{params}"
    
    # Connect to MongoDB (without specifying database to access multiple databases)
    if '?' in base_uri:
        connection_uri = base_uri
    else:
        connection_uri = f"{base_uri}?retryWrites=true&w=majority"
    
    print(f"\nConnecting to MongoDB...")
    try:
        client = MongoClient(connection_uri, serverSelectionTimeoutMS=30000)
        # Test connection
        client.admin.command('ping')
        print("Connected successfully!")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        return False
    
    # Get source and target databases
    src_db = client[SOURCE_DB]
    tgt_db = client[TARGET_DB]
    
    # Get all collections from source database
    collections = src_db.list_collection_names()
    print(f"\nFound {len(collections)} collections in source database")
    
    # Clone each collection structure
    for coll_name in collections:
        print(f"\nProcessing collection: {coll_name}")
        
        src_coll = src_db[coll_name]
        tgt_coll = tgt_db[coll_name]
        
        # Get collection info
        try:
            coll_info = src_db.list_collection_names(filter={'name': coll_name})
            # Get collection options
            coll_options = {}
            # Note: pymongo doesn't directly expose collection options like mongosh
            # We'll create the collection without options (MongoDB will use defaults)
        except Exception as e:
            print(f"  Error getting collection info: {e}")
            continue
        
        # Create collection in target database
        try:
            # Check if collection already exists
            if coll_name in tgt_db.list_collection_names():
                print(f"  Collection already exists: {coll_name}")
            else:
                # Create empty collection
                tgt_db.create_collection(coll_name)
                print(f"  Created collection: {coll_name}")
        except Exception as e:
            error_code = getattr(e, 'code', None)
            if error_code == 48:  # Collection already exists
                print(f"  Collection already exists: {coll_name}")
            else:
                print(f"  Collection creation failed ({coll_name}): {e}")
                continue
        
        # Clone indexes
        try:
            indexes = src_coll.list_indexes()
            index_count = 0
            for idx in indexes:
                idx_name = idx.get('name', '')
                if idx_name == '_id_':
                    continue  # Skip _id index (auto-created)
                
                idx_key = idx.get('key', {})
                idx_options = {k: v for k, v in idx.items() 
                              if k not in ['key', 'ns', 'v', 'name']}
                
                try:
                    # Create index with same options
                    tgt_coll.create_index(
                        list(idx_key.items()) if isinstance(idx_key, dict) else idx_key,
                        **idx_options
                    )
                    print(f"    Created index: {coll_name}.{idx_name}")
                    index_count += 1
                except Exception as e:
                    error_code = getattr(e, 'code', None)
                    if error_code == 85:  # Index already exists
                        print(f"    Index already exists: {coll_name}.{idx_name}")
                    else:
                        print(f"    Index creation failed ({coll_name}.{idx_name}): {e}")
        except Exception as e:
            print(f"  Error getting indexes for {coll_name}: {e}")
        
        # Clone data
        try:
            doc_count = src_coll.count_documents({})
            if doc_count > 0:
                print(f"  Copying {doc_count} documents...")
                
                # Use bulk operations for efficiency
                batch_size = 1000
                inserted_count = 0
                
                # Check if target collection already has data
                existing_count = tgt_coll.count_documents({})
                if existing_count > 0:
                    print(f"  Warning: Target collection already has {existing_count} documents")
                    response = input(f"  Do you want to continue and add more documents? (y/n): ")
                    if response.lower() != 'y':
                        print(f"  Skipping data copy for {coll_name}")
                        continue
                
                # Copy documents in batches
                cursor = src_coll.find({})
                batch = []
                
                for doc in cursor:
                    batch.append(doc)
                    if len(batch) >= batch_size:
                        tgt_coll.insert_many(batch, ordered=False)
                        inserted_count += len(batch)
                        print(f"    Copied {inserted_count}/{doc_count} documents...", end='\r')
                        batch = []
                
                # Insert remaining documents
                if batch:
                    tgt_coll.insert_many(batch, ordered=False)
                    inserted_count += len(batch)
                
                print(f"    Copied {inserted_count} documents successfully")
            else:
                print(f"  Collection is empty, no data to copy")
        except Exception as e:
            print(f"  Error copying data for {coll_name}: {e}")
    
    print("\n" + "="*60)
    print("CLONING COMPLETE!")
    print("="*60)
    print(f"\nAll collections, indexes, and data from '{SOURCE_DB}' have been cloned to '{TARGET_DB}'")
    
    client.close()
    return True

if __name__ == '__main__':
    try:
        clone_database_structure()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()

