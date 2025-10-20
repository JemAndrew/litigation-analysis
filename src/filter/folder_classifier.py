#!/usr/bin/env python3
"""
Folder Classifier - Intelligent Document Organisation

Analyses folder structure and classifies folders by importance.
Used for:
1. Case Bible building (which folders to read)
2. Vector store ingestion (which documents to index)

Distinguishes between:
- Case-specific evidence (extract)
- Legal authorities (note but don't extract)
- Other proceedings (context only)

British English throughout.
"""

from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
import re


@dataclass
class FolderClassification:
    """Classification result for a folder"""
    path: Path
    name: str
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW, SKIP
    category: str  # pleading, disclosure, procedural, legal_authorities, etc.
    file_count: int
    reason: str  # Why this classification
    should_read_for_bible: bool
    should_ingest_to_vector: bool


class FolderClassifier:
    """
    Classifies litigation folders intelligently
    
    Strategy:
    - CRITICAL: Core pleadings (must read for Bible)
    - HIGH: Key evidence, witness statements (read for Bible)
    - MEDIUM: Procedural docs (summary only for Bible)
    - LOW: Legal authorities (note existence, don't extract)
    - SKIP: Duplicates, other proceedings, archives
    """
    
    # Pattern definitions for classification
    PLEADING_PATTERNS = [
        r'claim',
        r'statement of claim',
        r'defence',
        r'statement of defence',
        r'reply',
        r'rejoinder',
        r'counterclaim',
        r'amended.*claim',
        r'amended.*defence'
    ]
    
    DISCLOSURE_PATTERNS = [
        r'disclosure',
        r'production',
        r'document.*request',
        r'exhibit',
        r'stern.*schedule'
    ]
    
    WITNESS_PATTERNS = [
        r'witness.*statement',
        r'affidavit',
        r'expert.*report',
        r'expert.*opinion'
    ]
    
    PROCEDURAL_PATTERNS = [
        r'procedural.*order',
        r'tribunal.*ruling',
        r'tribunal.*decision',
        r'po\s*\d+',  # PO1, PO2, etc.
        r'order.*no\.*\s*\d+'
    ]
    
    INDEX_PATTERNS = [
        r'index',
        r'consolidated.*index',
        r'hyperlinked.*index',
        r'trial.*bundle.*ind'
    ]
    
    # Legal authorities patterns (note but don't extract)
    LEGAL_AUTHORITIES_PATTERNS = [
        r'legal\s+authorit',
        r'case\s+authorit',
        r'bundle\s+z',
        r'authorities\s+bundle',
        r'law\s+report',
        r'precedent',
        r'statutory\s+material',
        r'legislation',
    ]
    
    # Other proceedings patterns (context only - different cases)
    OTHER_PROCEEDINGS_PATTERNS = [
        r'p&id\s+v\s+nigeria',
        r'pid\s+v\s+nigeria',
        r'nigeria.*arbitration',
        r'nigeria.*trial',
        r'tuna\s+bond',
        r'mozambique',
        r'beauregarde',
        r'other.*arbitration',
        r'separate.*proceeding',
    ]
    
    # Folders to SKIP entirely (duplicates/archives)
    SKIP_PATTERNS = [
        r'trial.*bundle(?!.*index)',  # Trial Bundle but NOT Index
        r'complete.*set',
        r'complete.*disclosure',
        r'hearing.*bundle(?!.*index)',
        r'cover.*spine',
        r'dramatis.*personae',
        r'chronology(?!.*email)',  # Standalone chronology docs
        r'reading.*list',
        r'transcription.*quote',
        r'historical.*version',
        r'do.*not.*use',
        r'archive',
        r'backup',
    ]
    
    # Draft/working folders (skip for Bible, maybe ingest selected docs)
    DRAFT_PATTERNS = [
        r'draft',
        r'historic',
        r'version',
        r'working',
        r'wip'
    ]
    
    def __init__(self, root_path: Path):
        """
        Initialise classifier
        
        Args:
            root_path: Root directory containing case folders
        """
        self.root_path = Path(root_path)
        
    def classify_all_folders(self) -> List[FolderClassification]:
        """
        Classify all top-level folders
        
        Returns:
            List of FolderClassification objects
        """
        
        if not self.root_path.exists():
            raise ValueError(f"Path does not exist: {self.root_path}")
        
        folders = [f for f in self.root_path.iterdir() if f.is_dir()]
        
        print(f"\n{'='*70}")
        print(f"FOLDER CLASSIFICATION - {len(folders)} FOLDERS")
        print(f"{'='*70}\n")
        
        classifications = []
        
        for folder in sorted(folders):
            classification = self._classify_folder(folder)
            classifications.append(classification)
            
            # Print classification
            emoji = self._get_priority_emoji(classification.priority)
            print(f"{emoji} {classification.name[:50]:50s} [{classification.priority:8s}]")
            print(f"   Category: {classification.category}")
            print(f"   Files: {classification.file_count}")
            print(f"   For Bible: {'✅ YES' if classification.should_read_for_bible else '❌ NO'}")
            print(f"   Reason: {classification.reason}")
            print()
        
        # Summary
        self._print_summary(classifications)
        
        return classifications
    
    def _classify_folder(self, folder: Path) -> FolderClassification:
        """
        Classify a single folder
        
        Args:
            folder: Folder path to classify
            
        Returns:
            FolderClassification object
        """
        
        name = folder.name.lower()
        file_count = sum(1 for _ in folder.rglob('*') if _.is_file())
        
        # Check OTHER PROCEEDINGS first (separate cases - skip entirely)
        for pattern in self.OTHER_PROCEEDINGS_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                return FolderClassification(
                    path=folder,
                    name=folder.name,
                    priority='SKIP',
                    category='other_proceedings',
                    file_count=file_count,
                    reason=f'Separate case/proceeding - not relevant to Lismore v PH',
                    should_read_for_bible=False,
                    should_ingest_to_vector=False
                )
        
        # Check SKIP patterns (duplicates/archives)
        for pattern in self.SKIP_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                return FolderClassification(
                    path=folder,
                    name=folder.name,
                    priority='SKIP',
                    category='duplicate_archive',
                    file_count=file_count,
                    reason=f'Matches skip pattern: {pattern}',
                    should_read_for_bible=False,
                    should_ingest_to_vector=False
                )
        
        # Check LEGAL AUTHORITIES (note existence, don't extract)
        for pattern in self.LEGAL_AUTHORITIES_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                return FolderClassification(
                    path=folder,
                    name=folder.name,
                    priority='LOW',
                    category='legal_authorities',
                    file_count=file_count,
                    reason='Legal authorities - case law/statutes (note but don\'t extract)',
                    should_read_for_bible=False,  # Don't extract full text
                    should_ingest_to_vector=False  # Don't need in vector store
                )
        
        # Check INDICES (HIGH priority - before pleadings)
        for pattern in self.INDEX_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                return FolderClassification(
                    path=folder,
                    name=folder.name,
                    priority='HIGH',
                    category='index',
                    file_count=file_count,
                    reason='Exhibit index - critical for mapping documents',
                    should_read_for_bible=True,
                    should_ingest_to_vector=False
                )
        
        # Check CORE PLEADINGS ONLY (CRITICAL priority)
        # Very specific patterns to avoid catching procedural responses
        core_pleading_patterns = [
            r'\bstatement\s+of\s+claim\b',
            r'\bstatement\s+of\s+defence\b',
            r'\breply\s+and\s+rejoinder\b',
        ]
        
        for pattern in core_pleading_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                # Exclude if it's a "response to" something (procedural, not core pleading)
                if re.search(r'\bresponse\s+to\b', name, re.IGNORECASE):
                    continue
                
                # Exclude if it's "shared with counsel" (likely duplicate)
                if 'shared with counsel' in name:
                    return FolderClassification(
                        path=folder,
                        name=folder.name,
                        priority='MEDIUM',
                        category='duplicate_pleading',
                        file_count=file_count,
                        reason='Duplicate - "Shared with Counsel" version',
                        should_read_for_bible=False,
                        should_ingest_to_vector=False
                    )
                
                # Exclude drafts
                if any(re.search(p, name, re.IGNORECASE) for p in self.DRAFT_PATTERNS):
                    return FolderClassification(
                        path=folder,
                        name=folder.name,
                        priority='SKIP',
                        category='draft_pleading',
                        file_count=file_count,
                        reason='Draft/historical version',
                        should_read_for_bible=False,
                        should_ingest_to_vector=False
                    )
                
                # Determine which core pleading it is
                if 'statement of claim' in name:
                    description = 'Statement of Claim'
                elif 'statement of defence' in name:
                    description = 'Statement of Defence'
                elif 'reply' in name and 'rejoinder' in name:
                    description = 'Reply and Rejoinder'
                else:
                    description = 'Core Pleading'
                
                return FolderClassification(
                    path=folder,
                    name=folder.name,
                    priority='CRITICAL',
                    category='pleading',
                    file_count=file_count,
                    reason=f'Core pleading: {description}',
                    should_read_for_bible=True,
                    should_ingest_to_vector=True
                )
        
        # Procedural responses/objections (MEDIUM, not CRITICAL)
        procedural_response_patterns = [
            r'response\s+to.*stay',
            r'response\s+to.*security',
            r'objections?\s+to',
            r'stern\s+schedule',
            r'responses?\s+to.*disclosure',
            r'responses?\s+to.*production',
            r'list\s+of.*docs',
            r'exhibits?\s+from.*response',
        ]
        
        for pattern in procedural_response_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return FolderClassification(
                    path=folder,
                    name=folder.name,
                    priority='MEDIUM',
                    category='procedural_response',
                    file_count=file_count,
                    reason=f'Procedural response/objection (not core pleading)',
                    should_read_for_bible=False,
                    should_ingest_to_vector=True
                )
        
        # Check WITNESS STATEMENTS (HIGH priority)
        for pattern in self.WITNESS_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                return FolderClassification(
                    path=folder,
                    name=folder.name,
                    priority='HIGH',
                    category='witness',
                    file_count=file_count,
                    reason='Witness/expert evidence',
                    should_read_for_bible=True,
                    should_ingest_to_vector=True
                )
        
        # Check LATE DISCLOSURE (HIGH priority - smoking guns!)
        if re.search(r'(69|late.*disclosure|15.*september.*2025)', name, re.IGNORECASE):
            return FolderClassification(
                path=folder,
                name=folder.name,
                priority='HIGH',
                category='late_disclosure',
                file_count=file_count,
                reason='⚠️  Late disclosure - likely smoking guns!',
                should_read_for_bible=True,
                should_ingest_to_vector=True
            )
        
        # Check PROCEDURAL (MEDIUM priority)
        for pattern in self.PROCEDURAL_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                return FolderClassification(
                    path=folder,
                    name=folder.name,
                    priority='MEDIUM',
                    category='procedural',
                    file_count=file_count,
                    reason='Tribunal ruling/procedural order',
                    should_read_for_bible=True,
                    should_ingest_to_vector=True
                )
        
        # Check DISCLOSURE (MEDIUM priority - lots of docs)
        for pattern in self.DISCLOSURE_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                return FolderClassification(
                    path=folder,
                    name=folder.name,
                    priority='MEDIUM',
                    category='disclosure',
                    file_count=file_count,
                    reason='General disclosure documents',
                    should_read_for_bible=False,
                    should_ingest_to_vector=True
                )
        
        # Default: LOW priority
        return FolderClassification(
            path=folder,
            name=folder.name,
            priority='LOW',
            category='other',
            file_count=file_count,
            reason='Miscellaneous/correspondence',
            should_read_for_bible=False,
            should_ingest_to_vector=True
        )
    
    def get_folders_for_bible(self) -> Dict[str, List[FolderClassification]]:
        """
        Get folders organised by what to read for Case Bible
        
        Returns:
            Dict with keys: 'critical', 'high', 'medium', 'legal_authorities', 'skip'
        """
        
        all_classifications = self.classify_all_folders()
        
        organised = {
            'critical': [],           # MUST read in full
            'high': [],               # SHOULD read (full or sample)
            'medium': [],             # Summary only
            'legal_authorities': [],  # Note existence only
            'skip': []                # Don't read
        }
        
        for classification in all_classifications:
            if classification.priority == 'CRITICAL':
                organised['critical'].append(classification)
            elif classification.priority == 'HIGH':
                organised['high'].append(classification)
            elif classification.priority == 'MEDIUM':
                organised['medium'].append(classification)
            elif classification.category == 'legal_authorities':
                organised['legal_authorities'].append(classification)
            else:
                organised['skip'].append(classification)
        
        return organised
    
    def _get_priority_emoji(self, priority: str) -> str:
        """Get emoji for priority level"""
        emojis = {
            'CRITICAL': '🔥',
            'HIGH': '⭐',
            'MEDIUM': '📋',
            'LOW': '📚',  # Legal authorities
            'SKIP': '❌'
        }
        return emojis.get(priority, '📁')
    
    def _print_summary(self, classifications: List[FolderClassification]):
        """Print classification summary"""
        
        print(f"{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}\n")
        
        # Count by priority
        by_priority = {}
        by_category = {}
        
        for c in classifications:
            by_priority[c.priority] = by_priority.get(c.priority, 0) + 1
            by_category[c.category] = by_category.get(c.category, 0) + 1
        
        print("BY PRIORITY:")
        for priority in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'SKIP']:
            count = by_priority.get(priority, 0)
            emoji = self._get_priority_emoji(priority)
            print(f"   {emoji} {priority:10s}: {count:2d} folders")
        
        print("\nBY CATEGORY:")
        for category, count in sorted(by_category.items()):
            print(f"   • {category:25s}: {count:2d} folders")
        
        # Bible reading summary
        bible_folders = [c for c in classifications if c.should_read_for_bible]
        vector_folders = [c for c in classifications if c.should_ingest_to_vector]
        legal_auth = [c for c in classifications if c.category == 'legal_authorities']
        other_proc = [c for c in classifications if c.category == 'other_proceedings']
        
        print(f"\nFOR CASE BIBLE:")
        print(f"   ✅ Will extract: {len(bible_folders)} folders")
        print(f"   📚 Note existence: {len(legal_auth)} folders (legal authorities)")
        print(f"   ❌ Will skip: {len(classifications) - len(bible_folders) - len(legal_auth)} folders")
        
        print(f"\nFOR VECTOR STORE:")
        print(f"   ✅ Will ingest: {len(vector_folders)} folders")
        print(f"   ❌ Will skip: {len(classifications) - len(vector_folders)} folders")
        
        # File count estimates
        total_files = sum(c.file_count for c in classifications)
        bible_files = sum(c.file_count for c in bible_folders)
        other_proc_files = sum(c.file_count for c in other_proc)
        legal_auth_files = sum(c.file_count for c in legal_auth)
        
        print(f"\nFILE COUNT ESTIMATES:")
        print(f"   Total files: {total_files:,}")
        print(f"   For Bible: {bible_files:,} ({bible_files/total_files*100:.1f}%)")
        print(f"   Legal authorities (note only): {legal_auth_files:,}")
        print(f"   Other proceedings (skip): {other_proc_files:,}")
        print(f"   Saved by filtering: {total_files - bible_files:,} files\n")
        
        print(f"{'='*70}\n")


def main():
    """Test the classifier"""
    
    # Your case path
    root_path = Path(r"C:\Users\JemAndrew\Velitor\Communication site - Documents\LIS1.1")
    
    classifier = FolderClassifier(root_path)
    
    # Get organised folders
    organised = classifier.get_folders_for_bible()
    
    print("\n" + "="*70)
    print("FOLDERS FOR CASE BIBLE BUILDING")
    print("="*70 + "\n")
    
    print("🔥 CRITICAL (Read in Full):")
    for folder in organised['critical']:
        print(f"   • {folder.name}")
    
    print("\n⭐ HIGH (Read Full or Sample):")
    for folder in organised['high']:
        print(f"   • {folder.name}")
    
    print("\n📋 MEDIUM (Summary Only):")
    for folder in organised['medium']:
        print(f"   • {folder.name}")
    
    print("\n📚 LEGAL AUTHORITIES (Note Existence Only):")
    for folder in organised['legal_authorities']:
        print(f"   • {folder.name}")
    
    print("\n❌ SKIP (Duplicates/Other Proceedings):")
    for folder in organised['skip'][:10]:
        print(f"   • {folder.name}")
    if len(organised['skip']) > 10:
        print(f"   ... and {len(organised['skip'])-10} more")


if __name__ == '__main__':
    main()