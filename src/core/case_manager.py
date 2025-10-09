#!/usr/bin/env python3
"""
Multi-Case Manager
Handles switching between different litigation cases

British English throughout
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class CaseMetadata:
    """Metadata for a litigation case"""
    case_id: str
    case_name: str
    claimant: str
    respondent: str
    tribunal: str
    allegations: str
    created_date: str
    last_accessed: str
    document_count: int
    ingestion_complete: bool


class CaseManager:
    """Manages multiple litigation cases"""
    
    def __init__(self, cases_root: Path):
        """
        Args:
            cases_root: Root directory containing all cases
        """
        self.cases_root = Path(cases_root)
        self.cases_root.mkdir(parents=True, exist_ok=True)
        
        self.cases_index_file = self.cases_root / "cases_index.json"
        self.cases_index = self._load_cases_index()
        
        self.active_case_id = None
    
    def _load_cases_index(self) -> Dict:
        """Load index of all cases"""
        if self.cases_index_file.exists():
            with open(self.cases_index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'cases': {}}
    
    def _save_cases_index(self):
        """Save cases index"""
        with open(self.cases_index_file, 'w', encoding='utf-8') as f:
            json.dump(self.cases_index, f, indent=2)
    
    def create_case(self, 
                   case_id: str,
                   case_name: str,
                   claimant: str,
                   respondent: str,
                   tribunal: str = "LCIA",
                   allegations: str = "") -> Path:
        """
        Create new case structure
        
        Returns:
            Path to case directory
        """
        case_dir = self.cases_root / case_id
        
        # Create directory structure
        (case_dir / "documents").mkdir(parents=True, exist_ok=True)
        (case_dir / "analysis").mkdir(parents=True, exist_ok=True)
        (case_dir / "vector_store").mkdir(parents=True, exist_ok=True)
        
        # Create metadata
        metadata = CaseMetadata(
            case_id=case_id,
            case_name=case_name,
            claimant=claimant,
            respondent=respondent,
            tribunal=tribunal,
            allegations=allegations,
            created_date=datetime.now().isoformat(),
            last_accessed=datetime.now().isoformat(),
            document_count=0,
            ingestion_complete=False
        )
        
        # Save metadata
        metadata_file = case_dir / "case_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(metadata), f, indent=2)
        
        # Add to index
        self.cases_index['cases'][case_id] = asdict(metadata)
        self._save_cases_index()
        
        print(f"✅ Created case: {case_name} ({case_id})")
        print(f"   Location: {case_dir}")
        print(f"\n📂 Add documents to: {case_dir / 'documents'}")
        
        return case_dir
    
    def list_cases(self) -> List[Dict]:
        """List all cases"""
        return list(self.cases_index['cases'].values())
    
    def get_case(self, case_id: str) -> Optional[Path]:
        """Get path to case directory"""
        if case_id in self.cases_index['cases']:
            case_dir = self.cases_root / case_id
            if case_dir.exists():
                # Update last accessed
                self.cases_index['cases'][case_id]['last_accessed'] = datetime.now().isoformat()
                self._save_cases_index()
                return case_dir
        return None
    
    def switch_case(self, case_id: str) -> bool:
        """Switch active case"""
        if case_id in self.cases_index['cases']:
            self.active_case_id = case_id
            print(f"✅ Switched to case: {self.cases_index['cases'][case_id]['case_name']}")
            return True
        return False
    
    def get_active_case(self) -> Optional[Path]:
        """Get currently active case directory"""
        if self.active_case_id:
            return self.get_case(self.active_case_id)
        return None
    
    def update_metadata(self, case_id: str, updates: Dict):
        """Update case metadata"""
        if case_id in self.cases_index['cases']:
            self.cases_index['cases'][case_id].update(updates)
            self._save_cases_index()
            
            # Also update file
            case_dir = self.cases_root / case_id
            metadata_file = case_dir / "case_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.cases_index['cases'][case_id], f, indent=2)