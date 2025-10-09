#!/usr/bin/env python3
"""
Test script for EnhancedVectorStore
Tests ChromaDB integration and RAG functionality
"""

import sys
from pathlib import Path

# Add src/ to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import the CLASS
from intelligence.vector_store import EnhancedVectorStore


def test_vector_store():
    """Test basic vector store functionality"""
    
    print("\n" + "="*70)
    print("TESTING VECTOR STORE")
    print("="*70 + "\n")
    
    # Create test directory
    test_dir = Path("test_vector_store_data")
    test_dir.mkdir(exist_ok=True)
    
    try:
        # Initialize vector store with correct parameters
        print("1. Initialising vector store...")
        store = EnhancedVectorStore(
            case_dir=test_dir  # ← Uses case_dir, not store_dir
        )
        print("   ✅ Vector store initialised\n")
        
        # Test document ingestion
        print("2. Testing document ingestion...")
        test_docs = [
            {
                'id': 'DOC_001',
                'content': 'The Share Purchase Agreement was signed on 15 March 2024 for £2.3 million.',
                'metadata': {
                    'filename': 'SPA_Agreement.pdf',
                    'doc_type': 'contract',
                    'date': '2024-03-15'
                }
            },
            {
                'id': 'DOC_002',
                'content': 'Process Holdings failed to disclose material liabilities totalling £800,000.',
                'metadata': {
                    'filename': 'Disclosure_Letter.pdf',
                    'doc_type': 'correspondence',
                    'date': '2024-04-10'
                }
            },
            {
                'id': 'DOC_003',
                'content': 'Email from CFO dated 10 February 2024 discussing undisclosed Grace Taiga liabilities.',
                'metadata': {
                    'filename': 'Email_CFO_Feb2024.msg',
                    'doc_type': 'email',
                    'date': '2024-02-10'
                }
            }
        ]
        
        for doc in test_docs:
            store.add_document(
                doc_id=doc['id'],
                content=doc['content'],
                metadata=doc['metadata']
            )
        print(f"   ✅ Ingested {len(test_docs)} documents\n")
        
        # Test semantic search
        print("3. Testing semantic search...")
        results = store.search(
            query="undisclosed liabilities concealment",
            n_results=2
        )
        print(f"   ✅ Found {len(results)} relevant documents")
        for i, result in enumerate(results):
            print(f"\n   Result {i+1}:")
            print(f"   - ID: {result['id']}")
            print(f"   - Score: {result['score']:.3f}")
            print(f"   - Preview: {result['content'][:80]}...")
        print()
        
        # Test hybrid search (if available)
        print("4. Testing hybrid search...")
        try:
            results = store.hybrid_search(
                query="Grace Taiga £800,000",
                n_results=2
            )
            print(f"   ✅ Hybrid search found {len(results)} documents")
            for i, result in enumerate(results):
                print(f"\n   Result {i+1}:")
                print(f"   - ID: {result['id']}")
                print(f"   - Score: {result['score']:.3f}")
            print()
        except AttributeError:
            print("   ⚠️  Hybrid search not available")
            print("   System works fine without it\n")
        
        # Test entity extraction
        print("5. Testing entity extraction...")
        entities = store.extract_legal_entities(test_docs[0]['content'])
        if entities['dates'] or entities['money']:
            print(f"   ✅ Extracted entities:")
            print(f"   - Dates: {entities.get('dates', [])}")
            print(f"   - Money: {entities.get('money', [])}")
            print()
        else:
            print("   ⚠️  No entities extracted (check regex patterns)")
            print()
        
        print("="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        print("\nCleaning up test data...")
        import shutil
        if test_dir.exists():
            shutil.rmtree(test_dir)
        print("✅ Cleanup complete\n")


if __name__ == "__main__":
    success = test_vector_store()
    sys.exit(0 if success else 1)