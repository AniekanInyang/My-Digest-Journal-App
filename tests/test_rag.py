"""
Test script for RAG service functionality.
Run this to verify the RAG implementation is working correctly.
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables
load_dotenv()

print("=" * 60)
print("RAG Service Test")
print("=" * 60)

# Test 1: Import rag_service
print("\n1. Testing imports...")
try:
    from services.rag_service import (
        initialize_collection,
        add_entry_to_vector_db,
        search_entries,
        chat_with_journal,
        get_collection_stats,
        delete_entry_from_vector_db
    )
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    exit(1)

# Test 2: Check Azure OpenAI configuration
print("\n2. Checking Azure OpenAI configuration...")
required_vars = ['AZURE_OPENAI_KEY', 'AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_MODEL_NAME']
missing = [var for var in required_vars if not os.environ.get(var)]
if missing:
    print(f"✗ Missing environment variables: {', '.join(missing)}")
    print("   Please configure these in your .env file")
    exit(1)
else:
    print("✓ Azure OpenAI configuration found")

# Test 3: Initialize collection
print("\n3. Initializing ChromaDB collection...")
try:
    collection = initialize_collection()
    print(f"✓ Collection initialized: {collection.name}")
except Exception as e:
    print(f"✗ Collection initialization failed: {e}")
    exit(1)

# Test 4: Get collection stats
print("\n4. Getting collection statistics...")
try:
    stats = get_collection_stats()
    print(f"✓ Collection stats: {stats['total_entries']} entries")
except Exception as e:
    print(f"✗ Failed to get stats: {e}")

# Test 5: Add a test entry
print("\n5. Adding test entry to vector database...")
test_entry_id = "test_001"
test_content = "Today I felt really happy about finishing my project. I'm excited about the new features."
test_date = "2026-03-22T00:00:00Z"

try:
    result = add_entry_to_vector_db(
        entry_id=test_entry_id,
        content=test_content,
        date=test_date
    )
    if result:
        print("✓ Test entry added successfully")
    else:
        print("✗ Failed to add test entry")
except Exception as e:
    print(f"✗ Error adding entry: {e}")
    # Continue anyway to test other features

# Test 6: Search for the entry
print("\n6. Testing semantic search...")
try:
    results = search_entries("happy about project", n_results=3)
    print(f"✓ Search completed: Found {len(results)} results")
    if results:
        print(f"   Top result: {results[0]['content'][:50]}...")
except Exception as e:
    print(f"✗ Search failed: {e}")

# Test 7: Test chat functionality (if entries exist)
print("\n7. Testing chat functionality...")
try:
    if results:
        response = chat_with_journal(
            "What made me happy recently?",
            results[:2]
        )
        print(f"✓ Chat response generated ({len(response)} characters)")
        print(f"   Preview: {response[:100]}...")
    else:
        print("⚠ Skipping chat test (no entries found)")
except Exception as e:
    print(f"✗ Chat failed: {e}")

# Test 8: Delete test entry
print("\n8. Cleaning up test entry...")
try:
    result = delete_entry_from_vector_db(test_entry_id)
    if result:
        print("✓ Test entry deleted successfully")
    else:
        print("⚠ Could not delete test entry (may not exist)")
except Exception as e:
    print(f"✗ Deletion failed: {e}")

# Final stats
print("\n9. Final collection statistics...")
try:
    final_stats = get_collection_stats()
    print(f"✓ Final count: {final_stats['total_entries']} entries")
except Exception as e:
    print(f"✗ Failed to get final stats: {e}")

print("\n" + "=" * 60)
print("RAG Service Test Complete!")
print("=" * 60)
print("\nNext steps:")
print("1. Run 'python app.py' to start the application")
print("2. Navigate to /chat to test the chat interface")
print("3. Navigate to /migrate to migrate existing entries")
print("\nFor more information, see PHASE1_README.md")
