#!/usr/bin/env python3
"""
Enhanced RAG Vector Store - THE BRAIN
Includes: ChromaDB, Legal-BERT, Hybrid Search, LexNLP, Cohere Reranker, Email Metadata
British English throughout
"""


# Add src to path for imports
import sys
from pathlib import Path
src_dir = Path(__file__).parent.parent if "src" in str(Path(__file__).parent) else Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
    sys.path.insert(0, str(src_dir.parent))

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import hashlib
import json
from datetime import datetime
from tqdm import tqdm
import re
import email
from email import policy
from src.utils.document_loader import DocumentLoader

# ============================================================================
# OPTIONAL DEPENDENCIES - Handle gracefully if not installed
# ============================================================================

# BM25 keyword search (INSTALLED - you have this)
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    print("⚠️  rank-bm25 not installed. Hybrid search disabled.")

# LexNLP entity extraction (NOT AVAILABLE - compilation issues)


# Cohere reranking (INSTALLED - you have this)
try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False
    print("⚠️  Cohere not installed. Reranking disabled.")


class EnhancedVectorStore:
    """
    Advanced RAG engine with:
    - Legal-BERT embeddings (semantic search)
    - BM25 keyword search (exact matches)
    - Hybrid scoring (best of both)
    - LexNLP entity extraction
    - Cohere reranking (quality boost)
    - Email metadata extraction
    """
    
    def __init__(self, case_dir: Path, cohere_api_key: Optional[str] = None):
        """
        Initialise enhanced vector store
        
        Args:
            case_dir: Path to case directory (e.g., cases/lismore_v_ph/)
            cohere_api_key: Optional Cohere API key for reranking
        """
        self.case_dir = Path(case_dir)
        self.vector_store_dir = self.case_dir / "vector_store"
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialise ChromaDB (persistent storage)
        print("\n🔧 Initialising vector store...")
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.vector_store_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create/load collection
        try:
            self.collection = self.chroma_client.get_collection("documents")
            print(f"✅ Loaded existing collection ({self.collection.count()} chunks)")
        except:
            self.collection = self.chroma_client.create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
            print("✅ Created new collection")
        
        # Load Legal-BERT embedder
        print("🤖 Loading Legal-BERT embedder...")
        self.embedder = SentenceTransformer('nlpaueb/legal-bert-base-uncased')
        print("✅ Legal-BERT ready")
        
        # BM25 index (for hybrid search)
        self.bm25_index = None
        self.bm25_documents = []
        self.bm25_metadata = []
        self._load_bm25_index()
        
        # Cohere reranker (optional)
        self.cohere_client = None
        if cohere_api_key and COHERE_AVAILABLE:
            self.cohere_client = cohere.Client(cohere_api_key)
            print("✅ Cohere reranker enabled")
        elif not cohere_api_key and COHERE_AVAILABLE:
            print("⚠️  Cohere API key not provided. Reranking disabled.")
        
        # Statistics
        self.stats = {
            'total_documents': 0,
            'total_chunks': 0,
            'ingestion_date': None
        }
        self._load_stats()
    
    def _load_bm25_index(self):
        """Load BM25 index from disk (if exists)"""
        bm25_file = self.vector_store_dir / "bm25_index.json"
        
        if bm25_file.exists():
            print("📚 Loading BM25 index...")
            with open(bm25_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.bm25_documents = data['documents']
                self.bm25_metadata = data['metadata']
            
            # Tokenise documents for BM25
            tokenised_docs = [doc.lower().split() for doc in self.bm25_documents]
            self.bm25_index = BM25Okapi(tokenised_docs)
            print(f"✅ BM25 index loaded ({len(self.bm25_documents)} chunks)")
    
    def _save_bm25_index(self):
        """Save BM25 index to disk"""
        bm25_file = self.vector_store_dir / "bm25_index.json"
        
        with open(bm25_file, 'w', encoding='utf-8') as f:
            json.dump({
                'documents': self.bm25_documents,
                'metadata': self.bm25_metadata
            }, f)
    
    def _load_stats(self):
        """Load statistics"""
        stats_file = self.vector_store_dir / "stats.json"
        
        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                self.stats = json.load(f)
    
    def _save_stats(self):
        """Save statistics"""
        stats_file = self.vector_store_dir / "stats.json"
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2)
    
    def extract_legal_entities(self, text: str) -> Dict[str, List]:
        """
        Extract legal entities using simple regex patterns
        Good enough for litigation work without LexNLP/spaCy
        """
        import re
        
        entities = {
            'dates': [],
            'amounts': [],
            'money': []
        }
        
        # Extract dates (common legal formats)
        date_patterns = [
            # "15 March 2024", "15 March 2024", etc.
            r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\s+\d{4}',
            # "2024-03-15"
            r'\d{4}-\d{2}-\d{2}',
            # "15/03/2024" or "03/15/2024"
            r'\d{1,2}/\d{1,2}/\d{4}',
            # "March 2024"
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['dates'].extend(matches)
        
        # Extract money (£, $, EUR, USD, GBP)
        money_patterns = [
            # "£2.3M", "$500K", "€1.2B"
            r'[£$€]\s*\d+(?:,\d{3})*(?:\.\d+)?\s*(?:million|billion|thousand|M|B|K|m|b|k)?',
            # "2.3 million pounds", "500 thousand dollars"
            r'\d+(?:,\d{3})*(?:\.\d+)?\s+(?:million|billion|thousand)\s+(?:pounds|dollars|euros|GBP|USD|EUR)',
            # "GBP 2,300,000"
            r'(?:GBP|USD|EUR)\s+\d+(?:,\d{3})*(?:\.\d{2})?'
        ]
        
        for pattern in money_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['money'].extend(matches)
        
        # Extract standalone numbers (less useful but sometimes needed)
        number_pattern = r'\d+(?:,\d{3})*(?:\.\d+)?'
        entities['amounts'] = re.findall(number_pattern, text)[:10]  # Limit to first 10
        
        # Deduplicate
        entities['dates'] = list(set(entities['dates']))
        entities['money'] = list(set(entities['money']))
        
        return entities
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Intelligent text chunking with overlap
        
        Args:
            text: Full document text
            chunk_size: Words per chunk
            overlap: Overlap words between chunks
            
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        
        i = 0
        while i < len(words):
            # Get chunk
            chunk_words = words[i:i + chunk_size]
            chunk = ' '.join(chunk_words)
            chunks.append(chunk)
            
            # Move forward (with overlap)
            i += (chunk_size - overlap)
        
        return chunks if chunks else [text]
        
    def extract_email_metadata(self, file_path: Path) -> dict:
        """
        Extract email metadata from .msg or .eml files
        
        Args:
            file_path: Path to email file
            
        Returns:
            Dict with email metadata
        """
        if file_path.suffix.lower() not in ['.msg', '.eml']:
            return {}
        
        try:
            with open(file_path, 'rb') as f:
                msg = email.message_from_binary_file(f, policy=policy.default)
            
            return {
                'email_from': msg.get('From', ''),
                'email_to': msg.get('To', ''),
                'email_date': msg.get('Date', ''),
                'email_subject': msg.get('Subject', '')
            }
        except:
            return {}

    def ingest_document(self, file_path: Path, document_text: str) -> int:
        """
        Ingest single document with all enhancements
        
        Args:
            file_path: Path to document
            document_text: Extracted text content
            
        Returns:
            Number of chunks created
        """
        # Generate document ID
        doc_id = hashlib.md5(str(file_path).encode()).hexdigest()
        
        # Extract email metadata (if email)
        email_metadata = self.extract_email_metadata(file_path)
        
        # Extract legal entities with LexNLP
        entities = self.extract_legal_entities(document_text)
        
        # Chunk text
        chunks = self.chunk_text(document_text, chunk_size=1000, overlap=200)
        
        # Process each chunk
        chunk_count = 0
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            
            # Generate embedding with Legal-BERT
            embedding = self.embedder.encode(chunk).tolist()
            
            # Build metadata
            metadata = {
                'filename': file_path.name,
                'folder': file_path.parent.name,
                'doc_id': doc_id,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'file_extension': file_path.suffix.lower(),
                'ingestion_date': datetime.now().isoformat()
            }
            
            # Add email metadata if available
            if email_metadata:
                metadata.update(email_metadata)
            
            # Add LexNLP entities
            if entities['dates']:
                metadata['extracted_dates'] = entities['dates'][:5]  # Top 5
            if entities['amounts']:
                metadata['extracted_amounts'] = str(entities['amounts'][:5])
            
            # Add to ChromaDB
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[metadata]
            )
            
            # Add to BM25 index
            self.bm25_documents.append(chunk)
            self.bm25_metadata.append(metadata)
            
            chunk_count += 1
        
        return chunk_count
    
    def ingest_documents(self, documents_dir: Path) -> Dict:
        """
        Ingest all documents from directory
        
        Args:
            documents_dir: Path to documents directory
            
        Returns:
            Statistics dictionary
        """
        from src.utils.document_loader import DocumentLoader
        
        loader = DocumentLoader()
        
        print(f"\n📁 Ingesting documents from: {documents_dir}")
        print("This may take 10-30 minutes for 1,000 documents...\n")
        
        # Find all document files
        file_paths = []
        for ext in ['*.pdf', '*.docx', '*.doc', '*.txt', '*.msg', '*.eml']:
            file_paths.extend(documents_dir.rglob(ext))
        
        total_docs = 0
        total_chunks = 0
        
        # Process each file
        with tqdm(total=len(file_paths), desc="Ingesting") as pbar:
            for file_path in file_paths:
                try:
                    # Extract text
                    text = loader.extract_text(file_path)
                    
                    if not text or len(text) < 50:
                        pbar.update(1)
                        continue
                    
                    # Ingest with enhancements
                    chunks = self.ingest_document(file_path, text)
                    
                    total_docs += 1
                    total_chunks += chunks
                    
                    pbar.set_postfix({
                        'docs': total_docs,
                        'chunks': total_chunks
                    })
                    pbar.update(1)
                    
                except Exception as e:
                    print(f"\n⚠️  Error ingesting {file_path.name}: {e}")
                    pbar.update(1)
        
        # Rebuild BM25 index
        print("\n🔄 Building BM25 index...")
        tokenised_docs = [doc.lower().split() for doc in self.bm25_documents]
        self.bm25_index = BM25Okapi(tokenised_docs)
        
        # Save indexes and stats
        self._save_bm25_index()
        
        self.stats = {
            'total_documents': total_docs,
            'total_chunks': total_chunks,
            'ingestion_date': datetime.now().isoformat()
        }
        self._save_stats()
        
        print(f"\n✅ Ingestion complete!")
        print(f"   Documents: {total_docs:,}")
        print(f"   Chunks: {total_chunks:,}")
        
        return self.stats
    
    def semantic_search(self, query: str, n_results: int = 50) -> List[Dict]:
        """
        Semantic search using Legal-BERT embeddings
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of relevant chunks with metadata
        """
        # Generate query embedding
        query_embedding = self.embedder.encode(query).tolist()
        
        # Search ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, self.collection.count())
        )
        
        if not results['documents'][0]:
            return []
        
        # Format results
        formatted = []
        for doc, meta, dist in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ):
            formatted.append({
                'text': doc,
                'metadata': meta,
                'semantic_score': 1.0 - dist,  # Convert distance to similarity
                'source': 'semantic'
            })
        
        return formatted
    
    def keyword_search(self, query: str, n_results: int = 50) -> List[Dict]:
        """
        Keyword search using BM25
        
        Args:
            query: Search query
            n_results: Number of results
            
        Returns:
            List of relevant chunks
        """
        if not self.bm25_index:
            return []
        
        # Tokenise query
        query_tokens = query.lower().split()
        
        # Get BM25 scores
        scores = self.bm25_index.get_scores(query_tokens)
        
        # Get top N indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n_results]
        
        # Format results
        formatted = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include matches
                formatted.append({
                    'text': self.bm25_documents[idx],
                    'metadata': self.bm25_metadata[idx],
                    'keyword_score': float(scores[idx]),
                    'source': 'keyword'
                })
        
        return formatted
    
    def hybrid_search(self, query: str, n_results: int = 100, 
                     semantic_weight: float = 0.6) -> List[Dict]:
        """
        Hybrid search combining semantic + keyword
        
        Args:
            query: Search query
            n_results: Number of initial results to retrieve
            semantic_weight: Weight for semantic search (0-1)
            
        Returns:
            Merged and reranked results
        """
        keyword_weight = 1.0 - semantic_weight
        
        # Run both searches
        semantic_results = self.semantic_search(query, n_results)
        keyword_results = self.keyword_search(query, n_results)
        
        # Merge results by doc ID
        merged = {}
        
        # Add semantic results
        for result in semantic_results:
            doc_id = result['metadata'].get('doc_id', '') + '_' + str(result['metadata'].get('chunk_index', 0))
            merged[doc_id] = {
                **result,
                'semantic_score': result.get('semantic_score', 0),
                'keyword_score': 0
            }
        
        # Add keyword results
        for result in keyword_results:
            doc_id = result['metadata'].get('doc_id', '') + '_' + str(result['metadata'].get('chunk_index', 0))
            
            if doc_id in merged:
                # Update keyword score
                merged[doc_id]['keyword_score'] = result['keyword_score']
            else:
                # Add new result
                merged[doc_id] = {
                    **result,
                    'semantic_score': 0,
                    'keyword_score': result.get('keyword_score', 0)
                }
        
        # Calculate hybrid scores
        for doc_id, result in merged.items():
            # Normalise scores (0-1 range)
            sem_score = result.get('semantic_score', 0)
            key_score = result.get('keyword_score', 0)
            
            # Normalise keyword score (BM25 can be > 1)
            if key_score > 0:
                key_score = min(key_score / 10.0, 1.0)
            
            # Weighted combination
            result['hybrid_score'] = (semantic_weight * sem_score) + (keyword_weight * key_score)
        
        # Sort by hybrid score
        sorted_results = sorted(merged.values(), key=lambda x: x['hybrid_score'], reverse=True)
        
        return sorted_results[:n_results]
    
    def rerank_results(self, query: str, results: List[Dict], top_n: int = 15) -> List[Dict]:
        """
        Rerank results using Cohere
        
        Args:
            query: Original query
            results: Search results to rerank
            top_n: Number of top results to return
            
        Returns:
            Reranked results
        """
        if not self.cohere_client or not results:
            # Reranking not available, return top N by hybrid score
            return results[:top_n]
        
        try:
            # Prepare documents for reranking
            documents = [r['text'] for r in results]
            
            # Rerank with Cohere
            reranked = self.cohere_client.rerank(
                query=query,
                documents=documents,
                top_n=top_n,
                model="rerank-english-v3.0"
            )
            
            # Map back to original results
            reranked_results = []
            for result in reranked.results:
                original = results[result.index]
                original['rerank_score'] = result.relevance_score
                reranked_results.append(original)
            
            return reranked_results
            
        except Exception as e:
            print(f"⚠️  Reranking error: {e}")
            return results[:top_n]
    
    def search(self, query: str, n_results: int = 15, use_reranker: bool = True) -> List[Dict]:
        """
        Complete enhanced search pipeline
        
        Pipeline:
        1. Hybrid search (semantic + keyword) → 100 results
        2. Cohere reranking → top 15 results
        
        Args:
            query: Search query
            n_results: Final number of results
            use_reranker: Whether to use Cohere reranker
            
        Returns:
            Top N most relevant chunks
        """
        # Step 1: Hybrid search
        hybrid_results = self.hybrid_search(query, n_results=100)
        
        if not hybrid_results:
            return []
        
        # Step 2: Rerank (if enabled)
        if use_reranker and self.cohere_client:
            final_results = self.rerank_results(query, hybrid_results, top_n=n_results)
        else:
            final_results = hybrid_results[:n_results]
        
        return final_results
    
    def get_stats(self) -> Dict:
        """Get ingestion statistics"""
        return {
            **self.stats,
            'chroma_count': self.collection.count(),
            'bm25_count': len(self.bm25_documents)
        }