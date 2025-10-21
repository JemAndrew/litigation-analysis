#!/usr/bin/env python3
"""
Document Selector - Smart Document Selection for Bible Building

FIXED: Regex syntax error on line 87 (missing closing quote and comma)

Selects master documents and skips drafts/duplicates.
Handles Excel files intelligently (critical indices vs drafts).

CRITICAL: Only extracts TOP-LEVEL files from pleadings folders,
          skips exhibit subfolders (C-1, C-2, FA-1, etc.)

YOUR EXACT BIBLE STRATEGY:
- 5 Categories: Procedural, Pleadings, Trial Witnesses, Indices, Disclosure
- ~40-44 documents total
- Specific folders: 4, 5, 6, 8, 25, 29, 35, 51, 52, 55, 57, 61, 69
- Skip exhibit subfolders completely
- Only Trial Witness Statements subfolder from folder 61
- Only indices from Late Disclosure (not 1,350 files)

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
    # CRITICAL: Individual exhibit file patterns (SKIP THESE)
    # FIXED: All patterns now properly closed with $', syntax
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
        r'\bcopy\b',
        r'\bworking\b',
        r'\barchive',
        r'\bold\b',
        r'\bbackup',
        r'_\d{8}',  # Date suffix like _20241015
    ]
    
    # Always skip patterns
    SKIP_PATTERNS = [
        r'\.tmp$',
        r'~\$',  # MS Office temp files
        r'\.log$',
        r'\.bak$',
        r'thumbs\.db',
        r'desktop\.ini',
    ]
    
    def __init__(self):
        """Initialise document selector"""
        pass
    
    def _is_exhibit_subfolder(self, doc_path: Path, folder_root: Path) -> bool:
        """
        Check if document is inside an exhibit subfolder
        
        Args:
            doc_path: Path to document
            folder_root: Root folder being processed
        
        Returns:
            True if inside exhibit subfolder (should skip)
        """
        
        # Get relative path from folder root
        try:
            rel_path = doc_path.relative_to(folder_root)
        except ValueError:
            return False
        
        # Check each parent folder in path
        for parent in rel_path.parents:
            parent_name = parent.name.lower()
            
            for pattern in self.EXHIBIT_SUBFOLDER_PATTERNS:
                if re.search(pattern, parent_name):
                    return True
        
        return False
    
    def _is_individual_exhibit(self, filename: str) -> bool:
        """
        Check if file is an individual exhibit (C-1.pdf, FA-1.pdf, etc.)
        
        Args:
            filename: Filename to check
        
        Returns:
            True if individual exhibit (should skip)
        """
        
        for pattern in self.INDIVIDUAL_EXHIBIT_PATTERNS:
            if re.match(pattern, filename):
                return True
        
        return False
    
    def _is_critical_excel(self, filename: str) -> bool:
        """
        Check if Excel file is critical (never skip)
        
        Args:
            filename: Filename to check
        
        Returns:
            True if critical Excel file
        """
        
        name_lower = filename.lower()
        
        for pattern in self.CRITICAL_EXCEL_PATTERNS:
            if re.search(pattern, name_lower):
                return True
        
        return False
    
    def _should_skip(self, filename: str, is_excel: bool = False) -> Tuple[bool, str]:
        """
        Determine if file should be skipped
        
        Args:
            filename: Filename to check
            is_excel: Whether file is Excel format
        
        Returns:
            (should_skip, reason)
        """
        
        name_lower = filename.lower()
        
        # Always skip temp files
        for pattern in self.SKIP_PATTERNS:
            if re.search(pattern, name_lower):
                return (True, "Temp/system file")
        
        # Skip individual exhibits
        if self._is_individual_exhibit(filename):
            return (True, "Individual exhibit (will be in vector store)")
        
        # Critical Excel files: NEVER skip
        if is_excel and self._is_critical_excel(filename):
            return (False, "Critical Excel file")
        
        # Other files: Check draft patterns
        for pattern in self.DRAFT_PATTERNS:
            if re.search(pattern, name_lower):
                return (True, "Draft/old version")
        
        return (False, "")
    
    def _get_extract_type(self, classification, doc_path: Path) -> str:
        """
        Determine extraction type for document
        
        Args:
            classification: FolderClassification object
            doc_path: Path to document
        
        Returns:
            'full', 'summary', or 'list'
        """
        
        filename = doc_path.name.lower()
        category = classification.category
        
        # Legal authorities: List only
        if category == 'legal_authorities':
            return 'list'
        
        # Indices: Always full extraction
        if category in ['index', 'indices']:
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
            if 'index' in filename or 'list' in filename or 'summary' in filename:
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
        if category in ['index', 'indices']:
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
            elif category in ['index', 'indices']:
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
            
            print(f"\n📂 {classification.name}")
            print(f"   Category: {category}")
            
            # ═══════════════════════════════════════════════════════════
            # CRITICAL FIX: Smart folder-specific scanning
            # ═══════════════════════════════════════════════════════════
            
            # FIX #1: Trial Witnesses - Only extract from "Trial Witness Statements" subfolder
            if category == 'trial_witnesses':
                trial_subfolder = folder_path / "Trial Witness Statements"
                if trial_subfolder.exists() and trial_subfolder.is_dir():
                    file_iterator = trial_subfolder.glob('*.pdf')
                    print(f"   [Scanning: Trial Witness Statements subfolder only]")
                else:
                    # Fallback: top-level only
                    file_iterator = folder_path.glob('*')
                    print(f"   [Scanning: Top-level files only]")
            
            # FIX #2: Late Disclosure - Only extract indices/summaries, not 1,350+ individual docs
            elif category == 'late_disclosure':
                file_iterator = folder_path.glob('*')
                print(f"   [Scanning: Indices/summaries only - NOT individual documents]")
            
            # FIX #3: Pleadings & Indices - Top-level only (skip exhibit subfolders)
            elif category in ['pleadings', 'bible_essential', 'index', 'indices']:
                file_iterator = folder_path.glob('*')
                print(f"   [Scanning: Top-level files only - skipping exhibit subfolders]")
            
            # Other categories: Recursive is fine
            else:
                file_iterator = folder_path.rglob('*')
                print(f"   [Scanning: All files recursively]")
            
            folder_selected = 0
            
            for doc_path in file_iterator:
                if not doc_path.is_file():
                    continue
                
                total_docs += 1
                filename = doc_path.name
                
                # Check if inside exhibit subfolder (should skip)
                if self._is_exhibit_subfolder(doc_path, folder_path):
                    skipped_exhibits += 1
                    continue
                
                # Check if individual exhibit file (C-1.pdf, FA-1.pdf, etc.)
                if self._is_individual_exhibit(filename):
                    skipped_individual_exhibits += 1
                    continue
                
                # Check file extension
                if doc_path.suffix not in self.EXTRACTABLE_EXTENSIONS:
                    continue
                
                # Check if should skip
                is_excel = doc_path.suffix.lower() in ['.xlsx', '.xls', '.xlsm']
                should_skip, skip_reason = self._should_skip(filename, is_excel)
                
                if should_skip:
                    skipped_docs += 1
                    continue
                
                # Get extract type and priority
                extract_type = self._get_extract_type(classification, doc_path)
                priority = self._get_priority(classification, doc_path)
                
                # Calculate size
                size_mb = doc_path.stat().st_size / (1024 * 1024)
                
                # Create Document
                doc = Document(
                    path=doc_path,
                    filename=filename,
                    folder_name=classification.name,
                    size_mb=size_mb,
                    extract_type=extract_type,
                    priority=priority,
                    reason=f"{category.upper()} - {extract_type}"
                )
                
                selected[target_key].append(doc)
                folder_selected += 1
            
            print(f"   ✅ Selected: {folder_selected} documents")
        
        # Summary
        print(f"\n{'='*70}")
        print("SELECTION SUMMARY")
        print(f"{'='*70}")
        
        for key, docs in selected.items():
            if docs:
                full_count = len([d for d in docs if d.extract_type == 'full'])
                list_count = len([d for d in docs if d.extract_type == 'list'])
                
                print(f"\n{key.upper()}: {len(docs)} documents")
                if full_count > 0:
                    print(f"  Full extraction: {full_count}")
                if list_count > 0:
                    print(f"  List only: {list_count}")
        
        total_selected = sum(len(docs) for docs in selected.values())
        total_full = sum(len([d for d in docs if d.extract_type == 'full']) 
                        for docs in selected.values())
        
        print(f"\n{'='*70}")
        print(f"✅ Total selected: {total_selected} documents")
        print(f"📄 Full extraction: {total_full} documents")
        print(f"⏭️  Skipped: {skipped_docs} (drafts/duplicates)")
        print(f"⏭️  Skipped: {skipped_exhibits} (exhibit subfolders)")
        print(f"⏭️  Skipped: {skipped_individual_exhibits} (individual exhibits like C-1.pdf)")
        print(f"\n💡 Individual exhibits will be searchable via vector store!")
        print(f"    (They're in the indices, so Claude can reference them)")
        print(f"{'='*70}\n")
        
        return selected


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