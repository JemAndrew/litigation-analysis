#!/usr/bin/env python3
"""
Document Selector - Smart Document Selection for Bible Building

Selects master documents and skips drafts/duplicates.
Handles Excel files intelligently (critical indices vs drafts).

CRITICAL FIX: Only extracts TOP-LEVEL files from pleadings folders,
              skips exhibit subfolders (C-1, C-2, FA-1, etc.)

FIXED: Regex patterns now properly closed with quotes and commas

British English throughout.
"""

from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
import re


@dataclass
class Document:
    """Document selection result"""
    path: Path
    filename: str
    folder_name: str
    size_mb: float
    extract_type: str  # 'full', 'summary', 'list'
    priority: int  # 1-10 (10 = highest)
    reason: str  # Why selected/skipped


class DocumentSelector:
    """
    Selects documents intelligently for Bible building
    
    Strategy:
    - Full extraction: Core pleadings, indices, key witness statements
    - Summary only: Procedural orders, large disclosure sets
    - List only: Legal authorities (note existence, don't extract)
    - Skip: Drafts, duplicates, archives, EXHIBIT SUBFOLDERS
    """
    
    # File extensions
    PDF_EXTENSIONS = ['.pdf', '.PDF']
    WORD_EXTENSIONS = ['.doc', '.docx', '.DOC', '.DOCX']
    EXCEL_EXTENSIONS = ['.xlsx', '.xls', '.xlsm', '.XLSX', '.XLS', '.XLSM']
    EXTRACTABLE_EXTENSIONS = PDF_EXTENSIONS + WORD_EXTENSIONS + EXCEL_EXTENSIONS
    
    # ═══════════════════════════════════════════════════════════════
    # CRITICAL: Exhibit subfolder patterns (SKIP THESE)
    # ═══════════════════════════════════════════════════════════════
    EXHIBIT_SUBFOLDER_PATTERNS = [
        r'claimant.*factual.*exhibit',
        r'claimant.*exhibit',
        r'respondent.*exhibit',
        r'factual.*exhibit',
        r'expert.*exhibit',
        r'legal.*authorit.*exhibit',
        r'exhibit.*bundle',
        r'^exhibits?$',  # Folder literally named "Exhibits"
    ]
    
    # ═══════════════════════════════════════════════════════════════
    # CRITICAL EXCEL FILES (Never Skip Even if Named "Draft")
    # ═══════════════════════════════════════════════════════════════
    CRITICAL_EXCEL_PATTERNS = [
        r'trial.*bundle.*index',
        r'list.*documents.*received',
        r'consolidated.*index',
        r'hyperlinked.*index',
        r'exhibit.*index',
        r'document.*index',
    ]
    
    # Draft patterns (usually skip these)
    DRAFT_PATTERNS = [
        r'\bdraft\b',
        r'\bv\d+\b',  # v1, v2, etc.
        r'\bversion\s+\d+\b',
        r'\bworking\b',
        r'\bwip\b',
        r'^\d{2}\.\d{2}\.\d{2}',  # Date prefix like "01.02.24 Draft.pdf"
    ]
    
    # ═══════════════════════════════════════════════════════════════
    # FIXED: Individual exhibit file patterns (skip these)
    # ═══════════════════════════════════════════════════════════════
    INDIVIDUAL_EXHIBIT_PATTERNS = [
        r'^C-\d+\.pdf$',         # C-1.pdf, C-45.pdf, C-100.pdf
        r'^C-\d+\.PDF$',         # C-45.PDF (uppercase variant)
        r'^FA-\d+\.pdf$',        # FA-1.pdf, FA-10.pdf (expert exhibits)
        r'^FA-\d+\.PDF$',        # FA-1.PDF
        r'^CLA-\d+\.pdf$',       # CLA-1.pdf, CLA-05.pdf (legal authorities)
        r'^CLA-\d+\.PDF$',       # CLA-1.PDF
        r'^R-\d+\.pdf$',         # R-1.pdf (respondent exhibits)
        r'^R-\d+\.PDF$',         # R-1.PDF
        r'^R\d-\d+\.pdf$',       # R1-1.pdf (respondent exhibits variant)
        r'^R\d-\d+\.PDF$',       # R1-1.PDF
    ]
    
    # Skip patterns (always skip)
    SKIP_PATTERNS = [
        r'cover.*spine',
        r'do.*not.*use',
        r'delete',
        r'archive',
        r'backup',
        r'~\$',  # Temp Word files
    ]
    
    def __init__(self):
        """Initialise document selector"""
        pass
    
    def _is_exhibit_subfolder(self, path: Path, parent_folder: Path) -> bool:
        """
        Check if path is inside an exhibit subfolder
        
        Args:
            path: File path to check
            parent_folder: Parent folder path
            
        Returns:
            True if file is inside an exhibit subfolder
        """
        # Get relative path from parent
        try:
            rel_path = path.relative_to(parent_folder)
        except ValueError:
            return False
        
        # Check if any part of the path matches exhibit patterns
        for part in rel_path.parts[:-1]:  # Exclude filename itself
            for pattern in self.EXHIBIT_SUBFOLDER_PATTERNS:
                if re.search(pattern, part, re.IGNORECASE):
                    return True
        
        return False
    
    def _is_critical_excel(self, filename: str) -> bool:
        """
        Check if Excel file is critical for Bible
        
        Args:
            filename: Name of file to check
            
        Returns:
            True if Excel file is critical (never skip)
        """
        # Check if it's an Excel file
        if not any(filename.lower().endswith(ext.lower()) for ext in self.EXCEL_EXTENSIONS):
            return False
        
        # Check if matches critical patterns
        for pattern in self.CRITICAL_EXCEL_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                return True
        
        return False
    
    def _should_skip_document(self, doc_path: Path) -> Tuple[bool, str]:
        """
        Determine if document should be skipped
        
        Args:
            doc_path: Path to document
            
        Returns:
            (should_skip, reason)
        """
        
        filename = doc_path.name
        
        # NEVER skip critical Excel files
        if self._is_critical_excel(filename):
            return False, "Critical Excel index file"
        
        # Check INDIVIDUAL EXHIBIT patterns (C-1.pdf, CLA-05.pdf, etc.)
        for pattern in self.INDIVIDUAL_EXHIBIT_PATTERNS:
            if re.match(pattern, filename, re.IGNORECASE):
                return True, f"Individual exhibit file: {filename}"
        
        # Check SKIP patterns
        for pattern in self.SKIP_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                return True, f"Skip pattern matched: {pattern}"
        
        # Check DRAFT patterns
        for pattern in self.DRAFT_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                # Check if there's a non-draft version
                parent = doc_path.parent
                base_name = re.sub(r'(draft|v\d+|version\s+\d+)', '', filename, flags=re.IGNORECASE)
                base_name = re.sub(r'\s+', ' ', base_name).strip()
                
                # Look for potential master version
                for sibling in parent.glob('*'):
                    if sibling == doc_path:
                        continue
                    if base_name.lower() in sibling.name.lower():
                        if not any(re.search(p, sibling.name, re.IGNORECASE) for p in self.DRAFT_PATTERNS):
                            return True, f"Draft version - master exists: {sibling.name}"
                
                # No master found, but still probably a draft
                return True, "Draft version (no master found, but marked as draft)"
        
        # Check file extension
        if not any(filename.lower().endswith(ext.lower()) for ext in self.EXTRACTABLE_EXTENSIONS):
            return True, f"Unsupported file type: {doc_path.suffix}"
        
        return False, "Selected"
    
    def _get_extraction_type(self, classification, doc_path: Path) -> str:
        """
        Determine extraction type based on folder classification and document
        
        Args:
            classification: FolderClassification object
            doc_path: Path to document
            
        Returns:
            'full', 'summary', or 'list'
        """
        
        filename = doc_path.name
        category = classification.category
        
        # Legal authorities: List only
        if category == 'legal_authorities':
            return 'list'
        
        # Indices: Always full extraction
        if category == 'index':
            return 'full'
        
        # Core pleadings: Always full extraction
        if category in ['pleadings', 'bible_essential']:
            return 'full'
        
        # Trial witnesses: Always full extraction
        if category == 'trial_witnesses':
            return 'full'
        
        # Late disclosure: Full extraction for indices/summaries only
        if category == 'late_disclosure':
            # Check if it's an index/summary or actual document
            if 'index' in filename.lower() or 'list' in filename.lower() or 'summary' in filename.lower():
                return 'full'
            # Individual late disclosure docs go to vector store, not Bible
            return 'list'
        
        # Procedural orders: Full extraction (usually short)
        if category == 'procedural':
            return 'full'
        
        # Everything else: List only (will be in vector store)
        return 'list'
    
    def _get_priority(self, classification, doc_path: Path) -> int:
        """
        Get priority score (1-10) for document
        
        Args:
            classification: FolderClassification object
            doc_path: Path to document
            
        Returns:
            Priority score (10 = highest)
        """
        
        filename = doc_path.name.lower()
        category = classification.category
        
        # Critical documents
        if category in ['pleadings', 'bible_essential']:
            return 10
        
        # Indices
        if category == 'index':
            return 9
        
        # Trial witnesses
        if category == 'trial_witnesses':
            return 9
        
        # Late disclosure summaries
        if category == 'late_disclosure':
            if 'index' in filename or 'list' in filename or 'summary' in filename:
                return 8
            return 5
        
        # Procedural orders
        if category == 'procedural':
            return 7
        
        # Everything else
        return 5
    
    def select_for_bible_building(
        self,
        folder_classifications: List
    ) -> Dict[str, List[Document]]:
        """
        Select documents from classified folders
        
        Args:
            folder_classifications: List of FolderClassification objects
            
        Returns:
            Dict of documents by category
        """
        
        print(f"\n{'='*70}")
        print("DOCUMENT SELECTION FOR BIBLE BUILDING")
        print(f"{'='*70}\n")
        
        selected = {
            'pleadings': [],
            'indices': [],
            'trial_witnesses': [],
            'late_disclosure': [],
            'procedural': [],
            'legal_authorities': [],
            'other': []
        }
        
        total_docs = 0
        skipped_docs = 0
        skipped_exhibits = 0
        skipped_individual_exhibits = 0
        
        for classification in folder_classifications:
            if not classification.should_read_for_bible:
                continue
            
            folder_path = classification.path
            category = classification.category
            
            # Map category to selection dict key
            if category in ['pleadings', 'bible_essential']:
                target_key = 'pleadings'
            elif category == 'index':
                target_key = 'indices'
            elif category == 'trial_witnesses':
                target_key = 'trial_witnesses'
            elif category == 'late_disclosure':
                target_key = 'late_disclosure'
            elif category == 'procedural':
                target_key = 'procedural'
            elif category == 'legal_authorities':
                target_key = 'legal_authorities'
            else:
                target_key = 'other'
            
            # ═══════════════════════════════════════════════════════════
            # CRITICAL FIX: Smart folder-specific scanning
            # ═══════════════════════════════════════════════════════════
            
            # FIX #1: Trial Witnesses - Only extract from "Trial Witness Statements" subfolder
            if category == 'trial_witnesses':
                trial_subfolder = folder_path / "Trial Witness Statements"
                if trial_subfolder.exists() and trial_subfolder.is_dir():
                    file_iterator = trial_subfolder.glob('*.pdf')
                    print(f"   [Trial witnesses only: {classification.name}/Trial Witness Statements]")
                else:
                    # Fallback: top-level only
                    file_iterator = folder_path.glob('*.pdf')
                    print(f"   [Scanning top-level only: {classification.name}]")
            
            # FIX #2: Late Disclosure - Only extract indices/summaries, not 1,350+ individual docs
            elif category == 'late_disclosure':
                file_iterator = folder_path.glob('*')
                print(f"   [Late disclosure indices only: {classification.name}]")
            
            # FIX #3: Pleadings & Indices - Top-level only (skip exhibit subfolders)
            elif category in ['pleadings', 'bible_essential', 'index', 'indices']:
                file_iterator = folder_path.glob('*')
                print(f"   [Scanning top-level only: {classification.name}]")
            
            # Other categories: Recursive is fine
            else:
                file_iterator = folder_path.rglob('*')
            
            for doc_path in file_iterator:
                if not doc_path.is_file():
                    continue
                
                total_docs += 1
                
                # Check if inside exhibit subfolder
                if self._is_exhibit_subfolder(doc_path, folder_path):
                    skipped_exhibits += 1
                    continue
                
                # Check if should skip
                should_skip, reason = self._should_skip_document(doc_path)
                
                if should_skip:
                    # Track individual exhibits separately
                    if "Individual exhibit file" in reason:
                        skipped_individual_exhibits += 1
                    else:
                        skipped_docs += 1
                    continue
                
                # Get extraction type and priority
                extract_type = self._get_extraction_type(classification, doc_path)
                priority = self._get_priority(classification, doc_path)
                
                # Calculate size
                size_mb = doc_path.stat().st_size / (1024 * 1024)
                
                # Create Document object
                doc = Document(
                    path=doc_path,
                    filename=doc_path.name,
                    folder_name=classification.name,
                    size_mb=size_mb,
                    extract_type=extract_type,
                    priority=priority,
                    reason=f"Selected from {category}"
                )
                
                selected[target_key].append(doc)
        
        # Sort each category by priority
        for key in selected:
            selected[key].sort(key=lambda x: x.priority, reverse=True)
        
        # Print summary
        self._print_selection_summary(
            selected, 
            total_docs, 
            skipped_docs, 
            skipped_exhibits,
            skipped_individual_exhibits
        )
        
        return selected
    
    def _print_selection_summary(
        self,
        selected: Dict[str, List[Document]],
        total_docs: int,
        skipped_docs: int,
        skipped_exhibits: int,
        skipped_individual_exhibits: int
    ) -> None:
        """Print selection summary"""
        
        print(f"\n{'='*70}")
        print("DOCUMENT SELECTION SUMMARY")
        print(f"{'='*70}\n")
        
        total = 0
        total_to_extract = 0
        total_size = 0.0
        
        for category, docs in selected.items():
            if not docs:
                continue
            
            count = len(docs)
            to_extract = len([d for d in docs if d.extract_type == 'full'])
            size = sum(d.size_mb for d in docs)
            
            total += count
            total_to_extract += to_extract
            total_size += size
            
            print(f"{category.upper().replace('_', ' ')}:")
            print(f"   Documents: {count}")
            print(f"   To extract: {to_extract} (full text)")
            print(f"   To list: {count - to_extract} (reference only)")
            print(f"   Size: {size:.1f} MB")
            
            if docs and category != 'legal_authorities':
                print(f"   Files:")
                for doc in docs[:5]:
                    print(f"      • {doc.filename[:60]}")
                if len(docs) > 5:
                    print(f"      ... and {len(docs)-5} more")
            
            elif docs and category == 'legal_authorities':
                print(f"   Sample files (not extracting):")
                for doc in docs[:3]:
                    print(f"      • {doc.filename[:60]}")
                if len(docs) > 3:
                    print(f"      ... and {len(docs)-3} more")
            
            print()
        
        print(f"{'='*70}")
        print(f"TOTAL DOCUMENTS: {total}")
        print(f"   Total found: {total_docs}")
        print(f"   Skipped (drafts/duplicates): {skipped_docs}")
        print(f"   Skipped (exhibit subfolders): {skipped_exhibits}")
        print(f"   Skipped (individual exhibits): {skipped_individual_exhibits}")
        print(f"   Selected: {total}")
        print(f"   To extract (full text): {total_to_extract} ({total_size:.1f} MB)")
        print(f"   To list (reference): {total - total_to_extract}")
        print(f"\n💡 Individual exhibits (C-XX, CLA-XX, FA-XX) belong in vector store,")
        print(f"   not the Bible. They'll be searchable via the indices!")
        print(f"{'='*70}\n")


def main():
    """Test document selector"""
    
    from folder_classifier import FolderClassifier
    
    # Test on your case
    root_path = Path(r"C:\Users\JemAndrew\Velitor\Communication site - Documents\LIS1.1")
    
    # First classify folders
    classifier = FolderClassifier(root_path)
    organised = classifier.get_folders_for_bible()
    
    # Get all classifications
    to_process = (organised['critical'] + organised['high'] + 
                  organised['medium'] + organised['legal_authorities'])
    
    # Select documents
    selector = DocumentSelector()
    selected = selector.select_for_bible_building(to_process)
    
    # Show what we'll extract vs list
    print("\n" + "="*70)
    print("READY FOR BIBLE BUILDING")
    print("="*70)
    
    extract_count = sum(len([d for d in docs if d.extract_type == 'full']) 
                       for docs in selected.values())
    list_count = sum(len([d for d in docs if d.extract_type == 'list']) 
                    for docs in selected.values())
    
    print(f"\n✅ {extract_count} documents will be extracted (full text)")
    print(f"📚 {list_count} documents will be listed (reference only)")
    print(f"\nThis saves extracting hundreds of exhibits while still noting their existence!")


if __name__ == '__main__':
    main()