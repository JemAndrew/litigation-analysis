#!/usr/bin/env python3
"""
Discover the actual methods available in EnhancedVectorStore
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from intelligence.vector_store import EnhancedVectorStore

print("\n" + "="*70)
print("ENHANCED VECTOR STORE - AVAILABLE METHODS")
print("="*70 + "\n")

# Get all public methods
methods = [method for method in dir(EnhancedVectorStore) 
           if not method.startswith('_') and callable(getattr(EnhancedVectorStore, method))]

print("Public methods:\n")
for method in sorted(methods):
    # Get method signature
    import inspect
    try:
        sig = inspect.signature(getattr(EnhancedVectorStore, method))
        print(f"  ✅ {method}{sig}")
    except:
        print(f"  ✅ {method}(...)")

print("\n" + "="*70)
print("LIKELY METHODS FOR TESTING:")
print("="*70 + "\n")

# Highlight key methods
key_patterns = {
    'add': 'Adding documents',
    'ingest': 'Ingesting documents', 
    'index': 'Indexing documents',
    'search': 'Searching',
    'hybrid': 'Hybrid search',
    'extract': 'Entity extraction'
}

for pattern, description in key_patterns.items():
    matching = [m for m in methods if pattern in m.lower()]
    if matching:
        print(f"{description}:")
        for m in matching:
            print(f"  • {m}()")
        print()