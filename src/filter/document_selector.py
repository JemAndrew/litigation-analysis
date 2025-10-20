#!/usr/bin/env python3
"""
Document Selector - Master Document Detection

Intelligently selects master documents within folders.
Skips drafts, historical versions, and duplicates.

Handles:
- Case-specific evidence (extract full text)
- Legal authorities (list only, don't extract)
- Other proceedings (note only)

Strategy:
1. Look for "As Filed" / "Final" subfolders first
2. Skip "Draft" / "Historical" / "Archive" subfolders
3. Find master version by filename patterns
4. Return only critical documents to extract

British English throughout.
"""

from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
import re


@dataclass
class SelectedDocument:
    """A selected master document"""
    path: Path
    filename: str
    folder_name: str
    category: str  # pleading, index, witness, legal_authority, etc.
    reason: str  # Why this was selected
    size_mb: float
    extract_type: str  # 'full', 'list', 'skip'


class DocumentSelector:
    """
    Selects master documents within folders
    
    Filters out:
    - Draft versions
    - Historical versions
    - Archive copies
    - Duplicate documents
    
    Treats differently:
    - Case evidence (extract full text)
    - Legal authorities (list only)
    - Other proceedings (note only)
    
    Returns only the final, filed versions.
    """
    
    # Subfolders to prioritise (master versions)
    PRIORITY_SUBFOLDERS = [
        r'as\s+filed',
        r'final',
        r'signed',
        r'executed',
        r'filed',
    ]
    
    # Subfolders to skip (not master versions)
    SKIP_SUBFOLDERS = [
        r'draft',
        r'historical',
        r'historic',
        r'archive',
        r'version',
        r'working',
        r'wip',
        r'do\s+not\s+use',
        r'old',
        r'backup',
        r'temp',
    ]
    
    # Filename patterns to prioritise
    PRIORITY_FILENAMES = [
        r'final',
        r'signed',
        r'as\s+filed',
        r'filed',
    ]
    
    # Filename patterns to skip
    SKIP_FILENAMES = [
        r'draft',
        r'redline',
        r'track.*change',
        r'version\s+\d+',
        r'v\d+',
        r'copy\s+of',
        r'backup',
        r'\(conflicted\)',
        r'\~\$',  # Word temp files
    ]
    
    # File extensions to include
    VALID_EXTENSIONS = {
        '.pdf', '.docx', '.doc', '.xlsx', '.xls'
    }
    
    def __init__(self):
        """Initialise document selector"""
        pass
    
    def select_documents_from_folder(
        self, 
        folder: Path, 
        category: str,
        max_documents: int = 10,
        extract_type: str = 'full'
    ) -> List[SelectedDocument]:
        """
        Select master documents from a folder
        
        Args:
            folder: Folder to scan
            category: Category (pleading, index, witness, legal_authority, etc.)
            max_documents: Maximum documents to return
            extract_type: 'full' (extract text), 'list' (list only), 'skip'
        
        Returns:
            List of SelectedDocument objects
        """
        
        print(f"\n📂 Scanning: {folder.name}")
        
        if not folder.exists():
            print(f"   ❌ Folder does not exist")
            return []
        
        # For legal authorities, just list the files (don't extract)
        if category == 'legal_authorities':
            print(f"   📚 Legal authorities - listing only (not extracting)")
            return self._list_legal_authorities(folder, max_documents)
        
        # Strategy 1: Look for "As Filed" or "Final" subfolder
        priority_subfolder = self._find_priority_subfolder(folder)
        
        if priority_subfolder:
            print(f"   ✅ Found priority subfolder: {priority_subfolder.name}")
            return self._select_from_subfolder(
                priority_subfolder, 
                folder.name,
                category,
                max_documents,
                extract_type
            )
        
        # Strategy 2: Scan all files, skip draft subfolders
        print(f"   🔍 No priority subfolder - scanning all files")
        return self._select_from_all_files(
            folder,
            category,
            max_documents,
            extract_type
        )
    
    def _list_legal_authorities(
        self,
        folder: Path,
        max_documents: int
    ) -> List[SelectedDocument]:
        """
        List legal authority documents without extracting
        
        Args:
            folder: Folder containing legal authorities
            max_documents: Max to list
        
        Returns:
            List of SelectedDocument with extract_type='list'
        """
        
        files = []
        
        for file_path in folder.rglob('*'):
            if not file_path.is_file():
                continue
            
            if file_path.suffix.lower() not in self.VALID_EXTENSIONS:
                continue
            
            files.append(file_path)
        
        # Sort alphabetically
        files = sorted(files, key=lambda f: f.name)
        
        # Convert to SelectedDocument
        selected = []
        for file_path in files[:max_documents]:
            selected.append(SelectedDocument(
                path=file_path,
                filename=file_path.name,
                folder_name=folder.name,
                category='legal_authorities',
                reason='Legal authority - list only, no extraction',
                size_mb=file_path.stat().st_size / (1024 * 1024),
                extract_type='list'  # Don't extract, just note
            ))
        
        print(f"   📚 Listed {len(selected)} legal authorities (not extracting)")
        
        return selected
    
    def _find_priority_subfolder(self, folder: Path) -> Optional[Path]:
        """
        Find "As Filed" / "Final" subfolder
        
        Args:
            folder: Parent folder
        
        Returns:
            Path to priority subfolder, or None
        """
        
        subfolders = [f for f in folder.iterdir() if f.is_dir()]
        
        for subfolder in subfolders:
            name = subfolder.name.lower()
            
            for pattern in self.PRIORITY_SUBFOLDERS:
                if re.search(pattern, name, re.IGNORECASE):
                    return subfolder
        
        return None
    
    def _select_from_subfolder(
        self,
        subfolder: Path,
        parent_folder_name: str,
        category: str,
        max_documents: int,
        extract_type: str
    ) -> List[SelectedDocument]:
        """
        Select documents from a priority subfolder
        
        Args:
            subfolder: Subfolder to scan
            parent_folder_name: Name of parent folder
            category: Document category
            max_documents: Max to return
            extract_type: 'full', 'list', 'skip'
        
        Returns:
            List of SelectedDocument objects
        """
        
        files = []
        
        for file_path in subfolder.rglob('*'):
            if not file_path.is_file():
                continue
            
            if file_path.suffix.lower() not in self.VALID_EXTENSIONS:
                continue
            
            # Check if in a skip subfolder
            if self._is_in_skip_subfolder(file_path, subfolder):
                continue
            
            # Check filename
            if self._should_skip_filename(file_path.name):
                continue
            
            files.append(file_path)
        
        # Sort by priority
        files = self._sort_by_priority(files)
        
        # Convert to SelectedDocument
        selected = []
        for file_path in files[:max_documents]:
            selected.append(SelectedDocument(
                path=file_path,
                filename=file_path.name,
                folder_name=parent_folder_name,
                category=category,
                reason=f'From priority subfolder: {subfolder.name}',
                size_mb=file_path.stat().st_size / (1024 * 1024),
                extract_type=extract_type
            ))
        
        print(f"   📄 Selected {len(selected)} documents from {subfolder.name}")
        
        return selected
    
    def _select_from_all_files(
        self,
        folder: Path,
        category: str,
        max_documents: int,
        extract_type: str
    ) -> List[SelectedDocument]:
        """
        Select documents from entire folder (no priority subfolder found)
        
        Args:
            folder: Folder to scan
            category: Document category
            max_documents: Max to return
            extract_type: 'full', 'list', 'skip'
        
        Returns:
            List of SelectedDocument objects
        """
        
        files = []
        
        for file_path in folder.rglob('*'):
            if not file_path.is_file():
                continue
            
            if file_path.suffix.lower() not in self.VALID_EXTENSIONS:
                continue
            
            # Check if in a skip subfolder
            if self._is_in_skip_subfolder(file_path, folder):
                continue
            
            # Check filename
            if self._should_skip_filename(file_path.name):
                continue
            
            files.append(file_path)
        
        # Sort by priority
        files = self._sort_by_priority(files)
        
        # Convert to SelectedDocument
        selected = []
        for file_path in files[:max_documents]:
            selected.append(SelectedDocument(
                path=file_path,
                filename=file_path.name,
                folder_name=folder.name,
                category=category,
                reason='Master version (no drafts in path)',
                size_mb=file_path.stat().st_size / (1024 * 1024),
                extract_type=extract_type
            ))
        
        print(f"   📄 Selected {len(selected)} documents")
        
        return selected
    
    def _is_in_skip_subfolder(self, file_path: Path, root: Path) -> bool:
        """
        Check if file is inside a skip subfolder
        
        Args:
            file_path: File to check
            root: Root folder (don't check above this)
        
        Returns:
            True if in skip subfolder
        """
        
        # Get all parent folders between file and root
        relative = file_path.relative_to(root)
        parts = relative.parts[:-1]  # Exclude filename
        
        for part in parts:
            part_lower = part.lower()
            
            for pattern in self.SKIP_SUBFOLDERS:
                if re.search(pattern, part_lower, re.IGNORECASE):
                    return True
        
        return False
    
    def _should_skip_filename(self, filename: str) -> bool:
        """
        Check if filename should be skipped
        
        Args:
            filename: Filename to check
        
        Returns:
            True if should skip
        """
        
        filename_lower = filename.lower()
        
        for pattern in self.SKIP_FILENAMES:
            if re.search(pattern, filename_lower, re.IGNORECASE):
                return True
        
        return False
    
    def _sort_by_priority(self, files: List[Path]) -> List[Path]:
        """
        Sort files by priority (priority filenames first)
        
        Args:
            files: List of file paths
        
        Returns:
            Sorted list
        """
        
        def priority_score(file_path: Path) -> int:
            """Calculate priority score (higher = better)"""
            score = 0
            name_lower = file_path.name.lower()
            
            # Check priority patterns
            for pattern in self.PRIORITY_FILENAMES:
                if re.search(pattern, name_lower, re.IGNORECASE):
                    score += 10
            
            # Prefer PDF over DOCX
            if file_path.suffix.lower() == '.pdf':
                score += 5
            
            # Prefer shorter filenames (often the main document)
            if len(file_path.name) < 50:
                score += 2
            
            return score
        
        return sorted(files, key=priority_score, reverse=True)
    
    def select_for_bible_building(
        self,
        folder_classifications: List
    ) -> Dict[str, List[SelectedDocument]]:
        """
        Select all documents needed for Case Bible building
        
        Args:
            folder_classifications: List from FolderClassifier
        
        Returns:
            Dict organized by category
        """
        
        print("\n" + "="*70)
        print("DOCUMENT SELECTION FOR CASE BIBLE")
        print("="*70)
        
        selected = {
            'pleadings': [],
            'indices': [],
            'witness_statements': [],
            'late_disclosure': [],
            'procedural': [],
            'legal_authorities': []  # Listed, not extracted
        }
        
        for classification in folder_classifications:
            if not classification.should_read_for_bible and classification.category != 'legal_authorities':
                continue
            
            # Determine category and max documents
            if classification.category == 'pleading':
                category_key = 'pleadings'
                max_docs = 5
                extract_type = 'full'
            
            elif classification.category == 'index':
                category_key = 'indices'
                max_docs = 3
                extract_type = 'full'
            
            elif classification.category == 'witness':
                category_key = 'witness_statements'
                max_docs = 20
                extract_type = 'full'
            
            elif classification.category == 'late_disclosure':
                category_key = 'late_disclosure'
                max_docs = 20
                extract_type = 'full'
            
            elif classification.category == 'procedural':
                category_key = 'procedural'
                max_docs = 2
                extract_type = 'full'
            
            elif classification.category == 'legal_authorities':
                category_key = 'legal_authorities'
                max_docs = 50  # List more since not extracting
                extract_type = 'list'  # Don't extract, just list
            
            else:
                continue
            
            # Select documents
            docs = self.select_documents_from_folder(
                classification.path,
                classification.category,
                max_docs,
                extract_type
            )
            
            selected[category_key].extend(docs)
        
        # Summary
        print("\n" + "="*70)
        print("SELECTION SUMMARY")
        print("="*70)
        
        total = 0
        total_size = 0
        total_to_extract = 0
        
        for category, docs in selected.items():
            count = len(docs)
            size = sum(d.size_mb for d in docs)
            to_extract = len([d for d in docs if d.extract_type == 'full'])
            total += count
            total_size += size
            total_to_extract += to_extract
            
            print(f"\n{category.upper().replace('_', ' ')}:")
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
        
        print(f"\n{'='*70}")
        print(f"TOTAL DOCUMENTS: {total}")
        print(f"   To extract (full text): {total_to_extract} ({total_size:.1f} MB)")
        print(f"   To list (reference): {total - total_to_extract}")
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
    print(f"\nThis saves extracting legal authorities while still noting their existence!")


if __name__ == '__main__':
    main()