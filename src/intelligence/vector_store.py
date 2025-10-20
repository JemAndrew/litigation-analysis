#!/usr/bin/env python3
"""
Enhanced RAG Vector Store with Smart Ingestion Detection

KEY FEATURES:
1. Content-based hashing - Detects actual document changes, not just renames
2. Ingestion manifest - Tracks what's been successfully processed
3. Incremental ingestion - Only process new/modified documents
4. Crash recovery - Resume from failures without re-processing successes
5. Comprehensive validation - Detect corrupted/unreadable files early

British English throughout.
"""

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
from typing import List, Dict, Optional, Tuple, Set
import hashlib
import json
from datetime import datetime
from tqdm import tqdm
import re
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

# BM25 keyword search
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

# Cohere reranking
try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False


@dataclass
class DocumentManifestEntry:
    """
    Tracks successfully ingested document with content fingerprint
    
    This enables intelligent incremental ingestion - we only re-process
    documents if their content actually changed.
    """
    file_path: str              # Relative path from documents root
    content_hash: str           # SHA256 of extracted text content
    file_size: int              # File size in bytes
    file_mtime: float           # Last modification time
    ingestion_date: str         # When successfully ingested
    chunk_count: int            # Number of chunks created
    extraction_success: bool    # Whether text extraction worked
    validation_status: str      # VALID, CORRUPTED, EMPTY, FAILED


class IntelligentVectorStore:
    """
    Vector store with smart document change detection
    
    INNOVATION: Only re-ingests documents that actually changed
    
    How it works:
    1. Calculate content hash (SHA256) of extracted text
    2. Compare against ingestion manifest
    3. If hash unchanged → Skip (already processed)
    4. If hash changed → Re-ingest (document modified)
    5. If not in manifest → Ingest (new document)
    
    This saves massive time and cost on repeated runs!
    """
    
    def __init__(self, case_dir: Path, cohere_api_key: Optional[str] = None):
        """
        Initialise intelligent vector store
        
        Args:
            case_dir: Path to case directory
            cohere_api_key: Optional Cohere API key for reranking
        """
        self.case_dir = Path(case_dir)
        self.vector_store_dir = self.case_dir / "vector_store"
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
        
        # Manifest file tracks what's been successfully ingested
        self.manifest_file = self.vector_store_dir / "ingestion_manifest.json"
        self.manifest: Dict[str, DocumentManifestEntry] = {}
        self._load_manifest()
        
        # Checkpoint for crash recovery (separate from manifest)
        self.checkpoint_file = self.vector_store_dir / "crash_recovery_checkpoint.json"
        
        print("\n🔧 Initialising intelligent vector store...")
        
        # ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.vector_store_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        try:
            self.collection = self.chroma_client.get_collection("documents")
            print(f"✅ Loaded collection ({self.collection.count()} chunks)")
        except:
            self.collection = self.chroma_client.create_collection(
                name="documents",
                metadata={"hnsw:space": "cosine"}
            )
            print("✅ Created new collection")
        
        # Legal-BERT
        print("🤖 Loading Legal-BERT embedder...")
        self.embedder = SentenceTransformer('nlpaueb/legal-bert-base-uncased')
        print("✅ Legal-BERT ready")
        
        # BM25 index
        self.bm25_index = None
        self.bm25_documents = []
        self.bm25_metadata = []
        self._load_bm25_index()
        
        # Cohere reranker
        self.cohere_client = None
        if cohere_api_key and COHERE_AVAILABLE:
            self.cohere_client = cohere.Client(cohere_api_key)
            print("✅ Cohere reranker enabled")
        
        # Statistics
        self.stats = {
            'total_documents': 0,
            'total_chunks': 0,
            'ingestion_date': None
        }
        self._load_stats()
        
        print(f"📊 Manifest: {len(self.manifest)} documents previously ingested")
    
    def _load_manifest(self):
        """Load ingestion manifest from disk"""
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert dict entries back to dataclass instances
                    self.manifest = {
                        path: DocumentManifestEntry(**entry)
                        for path, entry in data.items()
                    }
                logger.info(f"Loaded manifest: {len(self.manifest)} entries")
            except Exception as e:
                logger.error(f"Failed to load manifest: {e}")
                self.manifest = {}
        else:
            self.manifest = {}
    
    def _save_manifest(self):
        """Save ingestion manifest to disk"""
        try:
            # Convert dataclass instances to dicts for JSON serialisation
            data = {
                path: asdict(entry)
                for path, entry in self.manifest.items()
            }
            with open(self.manifest_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved manifest: {len(self.manifest)} entries")
        except Exception as e:
            logger.error(f"Failed to save manifest: {e}")
    
    def _calculate_content_hash(self, text: str) -> str:
        """
        Calculate SHA256 hash of document content
        
        This is the KEY to intelligent incremental ingestion.
        Same content → Same hash → Skip re-ingestion
        
        Args:
            text: Extracted document text
            
        Returns:
            SHA256 hash (hex string)
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate hash of file on disk (for quick detection)
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA256 hash of file bytes
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Cannot hash file {file_path}: {e}")
            return ""
    
    def scan_for_changes(self, documents_dir: Path) -> Dict[str, List[Path]]:
        """
        🎯 SMART INGESTION: Scan directory and categorise documents
        
        Categorises documents into:
        - NEW: Not in manifest (never seen before)
        - MODIFIED: Content hash changed (document edited)
        - UNCHANGED: Content hash matches (already processed)
        - FAILED_PREVIOUS: Previous ingestion failed (retry)
        
        This is the BRAIN of incremental ingestion!
        
        Args:
            documents_dir: Directory to scan
            
        Returns:
            Dictionary of categorised file paths
        """
        print(f"\n🔍 Scanning for document changes in: {documents_dir}")
        print("   Comparing against ingestion manifest...\n")
        
        categories = {
            'new': [],
            'modified': [],
            'unchanged': [],
            'failed_previous': []
        }
        
        # Find all document files
        all_files = []
        for ext in ['*.pdf', '*.docx', '*.doc', '*.txt', '*.msg', '*.eml']:
            all_files.extend(documents_dir.rglob(ext))
        
        print(f"📂 Found {len(all_files)} files on disk")
        print("   Analysing changes...\n")
        
        from src.utils.document_loader import DocumentLoader
        loader = DocumentLoader()
        
        for file_path in tqdm(all_files, desc="Scanning"):
            # Get relative path for manifest key
            try:
                rel_path = str(file_path.relative_to(documents_dir))
            except ValueError:
                rel_path = str(file_path)
            
            # Get file metadata
            try:
                file_size = file_path.stat().st_size
                file_mtime = file_path.stat().st_mtime
            except:
                logger.warning(f"Cannot access file: {file_path}")
                continue
            
            # Check manifest
            if rel_path in self.manifest:
                entry = self.manifest[rel_path]
                
                # Check if previous ingestion failed
                if not entry.extraction_success or entry.validation_status == 'FAILED':
                    categories['failed_previous'].append(file_path)
                    continue
                
                # Quick check: file size or mtime changed?
                if file_size != entry.file_size or file_mtime != entry.file_mtime:
                    # File changed on disk - need to check content
                    # Extract text and calculate new hash
                    try:
                        text = loader.extract_text(file_path)
                        if text and len(text) >= 50:
                            new_hash = self._calculate_content_hash(text)
                            
                            if new_hash != entry.content_hash:
                                # Content actually changed
                                categories['modified'].append(file_path)
                            else:
                                # False alarm - metadata changed but content same
                                categories['unchanged'].append(file_path)
                        else:
                            # Cannot extract text - treat as modified
                            categories['modified'].append(file_path)
                    except:
                        # Extraction failed - treat as modified
                        categories['modified'].append(file_path)
                else:
                    # File unchanged (size and mtime match)
                    categories['unchanged'].append(file_path)
            else:
                # Not in manifest - new document
                categories['new'].append(file_path)
        
        # Print summary
        print(f"\n📊 Change Detection Results:")
        print(f"   🆕 New documents: {len(categories['new'])}")
        print(f"   ✏️  Modified documents: {len(categories['modified'])}")
        print(f"   ✅ Unchanged documents: {len(categories['unchanged'])}")
        print(f"   🔄 Previously failed: {len(categories['failed_previous'])}")
        
        total_to_process = len(categories['new']) + len(categories['modified']) + len(categories['failed_previous'])
        print(f"\n   → {total_to_process} documents need processing")
        print(f"   → {len(categories['unchanged'])} documents can be skipped\n")
        
        return categories
    
    def comprehensive_validation(self, file_path: Path) -> Tuple[bool, str, Optional[str]]:
        """
        🔬 COMPREHENSIVE DOCUMENT VALIDATION
        
        Validates document BEFORE ingestion to catch issues early:
        1. File exists and readable
        2. File size reasonable (not empty, not huge)
        3. Text extraction works
        4. Minimum content length met
        5. Not just OCR gibberish
        
        Args:
            file_path: Path to document
            
        Returns:
            Tuple of (is_valid, status_message, extracted_text)
        """
        # Check file exists
        if not file_path.exists():
            return False, "FILE_NOT_FOUND", None
        
        # Check file size
        try:
            file_size = file_path.stat().st_size
        except:
            return False, "CANNOT_ACCESS", None
        
        if file_size == 0:
            return False, "EMPTY_FILE", None
        
        if file_size > 100 * 1024 * 1024:  # 100MB
            return False, "TOO_LARGE", None
        
        # Try to extract text
        from src.utils.document_loader import DocumentLoader
        loader = DocumentLoader()
        
        try:
            text = loader.extract_text(file_path)
        except Exception as e:
            return False, f"EXTRACTION_FAILED: {str(e)[:50]}", None
        
        # Check text extraction succeeded
        if not text:
            return False, "NO_TEXT_EXTRACTED", None
        
        if len(text) < 50:
            return False, "INSUFFICIENT_CONTENT", None
        
        # Check for OCR gibberish (lots of � or unprintable characters)
        gibberish_chars = text.count('�') + text.count('\x00')
        if gibberish_chars > len(text) * 0.1:  # >10% gibberish
            return False, "OCR_GIBBERISH", None
        
        # Check it's not just whitespace
        if len(text.strip()) < 50:
            return False, "ONLY_WHITESPACE", None
        
        # All checks passed
        return True, "VALID", text
    
    def ingest_with_intelligence(
        self,
        documents_dir: Path,
        force_reprocess: bool = False,
        skip_unchanged: bool = True
    ) -> Dict:
        """
        🚀 INTELLIGENT INCREMENTAL INGESTION
        
        This is the MAIN ingestion method with smart change detection.
        
        Process:
        1. Scan directory for changes (new/modified/unchanged)
        2. Skip unchanged documents (unless force_reprocess=True)
        3. Validate documents before processing
        4. Extract text and calculate content hash
        5. Ingest with embeddings
        6. Update manifest on success
        7. Checkpoint for crash recovery
        
        Args:
            documents_dir: Directory containing documents
            force_reprocess: If True, re-process everything (ignore manifest)
            skip_unchanged: If True, skip unchanged documents
            
        Returns:
            Statistics dictionary
        """
        from src.utils.document_loader import DocumentLoader
        loader = DocumentLoader()
        
        print(f"\n{'='*70}")
        print("INTELLIGENT DOCUMENT INGESTION")
        print(f"{'='*70}\n")
        
        # Scan for changes
        if force_reprocess:
            print("⚠️  FORCE REPROCESS MODE - Ignoring manifest\n")
            # Get all files
            all_files = []
            for ext in ['*.pdf', '*.docx', '*.doc', '*.txt']:
                all_files.extend(documents_dir.rglob(ext))
            
            categories = {
                'new': all_files,
                'modified': [],
                'unchanged': [],
                'failed_previous': []
            }
        else:
            categories = self.scan_for_changes(documents_dir)
        
        # Determine what to process
        files_to_process = []
        
        if skip_unchanged:
            files_to_process = (
                categories['new'] + 
                categories['modified'] + 
                categories['failed_previous']
            )
            print(f"✅ Skipping {len(categories['unchanged'])} unchanged documents")
        else:
            # Process everything (including unchanged)
            files_to_process = (
                categories['new'] + 
                categories['modified'] + 
                categories['unchanged'] + 
                categories['failed_previous']
            )
        
        if not files_to_process:
            print("\n✅ All documents are up to date! Nothing to process.\n")
            return self.stats
        
        print(f"\n📋 Processing {len(files_to_process)} documents\n")
        
        # Estimate time and cost
        estimated_time_mins = (len(files_to_process) * 1.5) / 60
        print(f"⏱️  Estimated time: {estimated_time_mins:.1f} minutes")
        print(f"💰 Estimated cost: £0 (embeddings are local)")
        
        proceed = input("\nProceed with ingestion? (y/n): ")
        if proceed.lower() != 'y':
            print("Cancelled.")
            return self.stats
        
        # Load checkpoint
        processed_this_run = self._load_checkpoint()
        
        # Process documents
        total_docs = 0
        total_chunks = 0
        failed_files = []
        skipped_files = []
        
        print(f"\n{'='*70}")
        print("PROCESSING DOCUMENTS")
        print(f"{'='*70}\n")
        
        with tqdm(total=len(files_to_process), desc="Ingesting") as pbar:
            for file_path in files_to_process:
                # Get relative path for manifest
                try:
                    rel_path = str(file_path.relative_to(documents_dir))
                except ValueError:
                    rel_path = str(file_path)
                
                # Skip if already processed in this run (crash recovery)
                if rel_path in processed_this_run:
                    pbar.update(1)
                    continue
                
                # Validate document
                is_valid, status, extracted_text = self.comprehensive_validation(file_path)
                
                if not is_valid:
                    logger.warning(f"Validation failed for {file_path.name}: {status}")
                    failed_files.append((file_path.name, status))
                    
                    # Update manifest with failure
                    self.manifest[rel_path] = DocumentManifestEntry(
                        file_path=rel_path,
                        content_hash="",
                        file_size=file_path.stat().st_size if file_path.exists() else 0,
                        file_mtime=file_path.stat().st_mtime if file_path.exists() else 0,
                        ingestion_date=datetime.now().isoformat(),
                        chunk_count=0,
                        extraction_success=False,
                        validation_status=status
                    )
                    
                    pbar.update(1)
                    continue
                
                # Calculate content hash
                content_hash = self._calculate_content_hash(extracted_text)
                
                # Check if content hash already exists in manifest (duplicate content)
                duplicate_found = False
                for existing_path, existing_entry in self.manifest.items():
                    if existing_path != rel_path and existing_entry.content_hash == content_hash:
                        logger.info(f"Duplicate content: {file_path.name} matches {existing_path}")
                        skipped_files.append((file_path.name, f"Duplicate of {existing_path}"))
                        duplicate_found = True
                        break
                
                if duplicate_found:
                    pbar.update(1)
                    continue
                
                # Ingest document
                try:
                    chunk_count = self._ingest_single_document(
                        file_path=file_path,
                        document_text=extracted_text,
                        content_hash=content_hash
                    )
                    
                    # Update manifest with success
                    self.manifest[rel_path] = DocumentManifestEntry(
                        file_path=rel_path,
                        content_hash=content_hash,
                        file_size=file_path.stat().st_size,
                        file_mtime=file_path.stat().st_mtime,
                        ingestion_date=datetime.now().isoformat(),
                        chunk_count=chunk_count,
                        extraction_success=True,
                        validation_status="VALID"
                    )
                    
                    total_docs += 1
                    total_chunks += chunk_count
                    
                    # Add to processed set
                    processed_this_run.add(rel_path)
                    
                    # Save checkpoint every 10 documents
                    if len(processed_this_run) % 10 == 0:
                        self._save_checkpoint(processed_this_run)
                        self._save_manifest()
                    
                    pbar.set_postfix({
                        'docs': total_docs,
                        'chunks': total_chunks,
                        'failed': len(failed_files)
                    })
                    
                except Exception as e:
                    logger.error(f"Ingestion failed for {file_path.name}: {e}")
                    failed_files.append((file_path.name, str(e)[:50]))
                    
                    # Update manifest with failure
                    self.manifest[rel_path] = DocumentManifestEntry(
                        file_path=rel_path,
                        content_hash=content_hash,
                        file_size=file_path.stat().st_size,
                        file_mtime=file_path.stat().st_mtime,
                        ingestion_date=datetime.now().isoformat(),
                        chunk_count=0,
                        extraction_success=False,
                        validation_status=f"INGESTION_FAILED: {str(e)[:30]}"
                    )
                
                pbar.update(1)
        
        # Rebuild BM25 index
        if BM25_AVAILABLE and self.bm25_documents:
            print("\n🔄 Rebuilding BM25 index...")
            tokenised_docs = [doc.lower().split() for doc in self.bm25_documents]
            self.bm25_index = BM25Okapi(tokenised_docs)
        
        # Save final state
        self._save_bm25_index()
        self._save_manifest()
        self._clear_checkpoint()
        
        # Update stats
        self.stats = {
            'total_documents': total_docs,
            'total_chunks': total_chunks,
            'ingestion_date': datetime.now().isoformat(),
            'manifest_entries': len(self.manifest),
            'failed_files': len(failed_files),
            'skipped_duplicates': len(skipped_files)
        }
        self._save_stats()
        
        # Print summary
        print(f"\n{'='*70}")
        print("INGESTION COMPLETE")
        print(f"{'='*70}")
        print(f"\n✅ Successfully ingested:")
        print(f"   Documents: {total_docs:,}")
        print(f"   Chunks: {total_chunks:,}")
        
        if skipped_files:
            print(f"\n⏭️  Skipped (duplicates): {len(skipped_files)}")
        
        if failed_files:
            print(f"\n⚠️  Failed: {len(failed_files)}")
            print(f"   See: {self.vector_store_dir}/ingestion_errors.log")
            
            # Save error log
            error_log = self.vector_store_dir / "ingestion_errors.log"
            with open(error_log, 'w', encoding='utf-8') as f:
                for filename, error in failed_files:
                    f.write(f"{filename}: {error}\n")
        
        print()
        
        return self.stats
    
    def _ingest_single_document(
        self,
        file_path: Path,
        document_text: str,
        content_hash: str
    ) -> int:
        """
        Ingest single document (internal method)
        
        Args:
            file_path: Path to document
            document_text: Extracted text
            content_hash: SHA256 hash of content
            
        Returns:
            Number of chunks created
        """
        # Chunk text
        chunks = self._chunk_text(document_text, chunk_size=1000, overlap=200)
        
        chunk_count = 0
        for i, chunk in enumerate(chunks):
            chunk_id = f"{content_hash}_{i}"
            
            # Generate Legal-BERT embedding
            embedding = self.embedder.encode(chunk).tolist()
            
            # Build metadata
            metadata = {
                'filename': file_path.name,
                'folder': file_path.parent.name,
                'content_hash': content_hash,
                'chunk_index': i,
                'total_chunks': len(chunks),
                'file_extension': file_path.suffix.lower(),
                'ingestion_date': datetime.now().isoformat()
            }
            
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
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Intelligent text chunking with overlap"""
        words = text.split()
        chunks = []
        
        i = 0
        while i < len(words):
            chunk_words = words[i:i + chunk_size]
            chunk = ' '.join(chunk_words)
            chunks.append(chunk)
            i += (chunk_size - overlap)
        
        return chunks if chunks else [text]
    
    def _load_checkpoint(self) -> Set[str]:
        """Load crash recovery checkpoint"""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        return set()
    
    def _save_checkpoint(self, processed: Set[str]):
        """Save crash recovery checkpoint"""
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(list(processed), f)
    
    def _clear_checkpoint(self):
        """Clear checkpoint after successful completion"""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
    
    def _load_bm25_index(self):
        """Load BM25 index from disk"""
        bm25_file = self.vector_store_dir / "bm25_index.json"
        if bm25_file.exists():
            with open(bm25_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.bm25_documents = data['documents']
                self.bm25_metadata = data['metadata']
            if BM25_AVAILABLE and self.bm25_documents:
                tokenised = [doc.lower().split() for doc in self.bm25_documents]
                self.bm25_index = BM25Okapi(tokenised)
    
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
    
    # Search methods remain the same as before...
    def search(self, query: str, n_results: int = 15, use_reranker: bool = True) -> List[Dict]:
        """Complete search pipeline (same as before)"""
        # Implementation same as your current vector_store.py
        pass
    
    def get_stats(self) -> Dict:
        """Get statistics including manifest info"""
        return {
            **self.stats,
            'chroma_count': self.collection.count(),
            'bm25_count': len(self.bm25_documents),
            'manifest_entries': len(self.manifest),
            'valid_documents': len([e for e in self.manifest.values() if e.extraction_success]),
            'failed_documents': len([e for e in self.manifest.values() if not e.extraction_success])
        }