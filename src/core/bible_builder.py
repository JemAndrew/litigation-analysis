#!/usr/bin/env python3
"""
Case Bible Builder - Main Orchestrator

Orchestrates the complete Case Bible building process:
1. Classifies folders (what to read)
2. Selects master documents (skip drafts)
3. Extracts text from documents
4. Builds comprehensive Bible prompt
5. Calls Claude with extended thinking
6. Saves Case Bible with metadata

This is run ONCE per case (or when case significantly changes).

British English throughout.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from filter.folder_classifier import FolderClassifier
from filter.document_selector import DocumentSelector
from prompts.bible_prompts import BiblePrompts
from api.claude_client import ClaudeClient

# Document extraction libraries
try:
    import PyPDF2
    from docx import Document as DocxDocument
except ImportError:
    print("⚠️  Missing dependencies. Install with:")
    print("   pip install PyPDF2 python-docx")
    sys.exit(1)


@dataclass
class BibleMetadata:
    """Metadata about the Case Bible build"""
    case_id: str
    case_name: str
    build_date: str
    folders_analysed: int
    documents_extracted: int
    legal_authorities_noted: int
    total_cost_gbp: float
    bible_length_chars: int
    bible_length_tokens_est: int
    folders_by_priority: Dict[str, int]
    build_duration_seconds: float


class BibleBuilder:
    """
    Orchestrates Case Bible building process
    
    This is the main class that coordinates:
    - Folder classification
    - Document selection
    - Text extraction
    - Bible generation via Claude
    - Saving results
    """
    
    def __init__(
        self,
        case_root: Path,
        case_id: str,
        case_name: str,
        claimant: str,
        respondent: str,
        tribunal: str = "LCIA"
    ):
        """
        Initialise Bible Builder
        
        Args:
            case_root: Root directory of case (contains 74 folders)
            case_id: Case identifier (e.g., 'lismore_v_ph')
            case_name: Display name
            claimant: Claimant name
            respondent: Respondent name
            tribunal: Tribunal name
        """
        
        self.case_root = Path(case_root)
        self.case_id = case_id
        self.case_name = case_name
        self.claimant = claimant
        self.respondent = respondent
        self.tribunal = tribunal
        
        # Output directory (where Bible will be saved)
        self.output_dir = Path(f"cases/{case_id}")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.classifier = FolderClassifier(self.case_root)
        self.selector = DocumentSelector()
        self.prompts = BiblePrompts()
        self.claude = ClaudeClient()
        
        # Tracking
        self.start_time = None
        self.extracted_texts = {}
        self.legal_authorities_list = []
    
    def build_bible(self, use_extended_thinking: bool = True) -> Path:
        """
        Build the complete Case Bible
        
        Args:
            use_extended_thinking: Use Claude's extended thinking (recommended)
        
        Returns:
            Path to saved Case Bible file
        """
        
        print("\n" + "="*70)
        print("🏗️  CASE BIBLE BUILDER")
        print("="*70)
        print(f"\nCase: {self.case_name}")
        print(f"Claimant: {self.claimant}")
        print(f"Respondent: {self.respondent}")
        print(f"Tribunal: {self.tribunal}")
        print(f"Root: {self.case_root}")
        print()
        
        self.start_time = datetime.now()
        
        # Step 1: Classify folders
        print("="*70)
        print("STEP 1: CLASSIFY FOLDERS")
        print("="*70)
        
        organised = self.classifier.get_folders_for_bible()
        
        # Step 2: Select master documents
        print("\n" + "="*70)
        print("STEP 2: SELECT MASTER DOCUMENTS")
        print("="*70)
        
        to_process = (organised['critical'] + organised['high'] + 
                     organised['medium'] + organised['legal_authorities'])
        
        selected = self.selector.select_for_bible_building(to_process)
        
        # Step 3: Extract text from documents
        print("\n" + "="*70)
        print("STEP 3: EXTRACT TEXT FROM DOCUMENTS")
        print("="*70)
        
        self._extract_all_documents(selected)
        
        # Step 4: Build Bible prompt
        print("\n" + "="*70)
        print("STEP 4: BUILD BIBLE PROMPT")
        print("="*70)
        
        bible_prompt = self._build_bible_prompt()
        
        # Step 5: Call Claude to generate Bible
        print("\n" + "="*70)
        print("STEP 5: GENERATE CASE BIBLE WITH CLAUDE")
        print("="*70)
        
        bible_text = self._generate_bible(bible_prompt, use_extended_thinking)
        
        # Step 6: Save Bible and metadata
        print("\n" + "="*70)
        print("STEP 6: SAVE CASE BIBLE")
        print("="*70)
        
        bible_path = self._save_bible(bible_text, organised, selected)
        
        # Summary
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print("\n" + "="*70)
        print("✅ CASE BIBLE BUILD COMPLETE!")
        print("="*70)
        print(f"\n📄 Bible saved to: {bible_path}")
        print(f"📊 Length: {len(bible_text):,} characters")
        print(f"⏱️  Time: {elapsed/60:.1f} minutes")
        print(f"💰 Cost: £{self.claude.total_cost_gbp:.2f}")
        print()
        
        return bible_path
    
    def _extract_all_documents(self, selected: Dict[str, List]) -> None:
        """
        Extract text from all selected documents
        
        Args:
            selected: Dict from DocumentSelector
        """
        
        total_to_extract = sum(
            len([d for d in docs if d.extract_type == 'full'])
            for docs in selected.values()
        )
        
        print(f"\n📄 Extracting text from {total_to_extract} documents...\n")
        
        extracted_count = 0
        
        for category, documents in selected.items():
            if not documents:
                continue
            
            print(f"\n{category.upper().replace('_', ' ')}:")
            
            for doc in documents:
                if doc.extract_type == 'list':
                    # For legal authorities, just note the filename
                    self.legal_authorities_list.append({
                        'filename': doc.filename,
                        'folder': doc.folder_name,
                        'size_mb': doc.size_mb
                    })
                    continue
                
                # Extract full text
                try:
                    print(f"   📖 {doc.filename[:60]}...")
                    
                    text = self._extract_text_from_file(doc.path)
                    
                    if text:
                        self.extracted_texts[doc.filename] = {
                            'text': text,
                            'category': category,
                            'folder': doc.folder_name,
                            'path': str(doc.path)
                        }
                        extracted_count += 1
                        print(f"      ✅ Extracted ({len(text):,} chars)")
                    else:
                        print(f"      ⚠️  No text extracted")
                
                except Exception as e:
                    print(f"      ❌ Error: {e}")
        
        print(f"\n✅ Extracted {extracted_count} documents")
        print(f"📚 Noted {len(self.legal_authorities_list)} legal authorities")
    
    def _extract_text_from_file(self, file_path: Path) -> str:
        """
        Extract text from a file (PDF or DOCX)
        
        Args:
            file_path: Path to file
        
        Returns:
            Extracted text
        """
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        suffix = file_path.suffix.lower()
        
        if suffix == '.pdf':
            return self._extract_from_pdf(file_path)
        elif suffix in ['.docx', '.doc']:
            return self._extract_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
    
    def _extract_from_pdf(self, file_path: Path) -> str:
        """Extract text from PDF"""
        
        try:
            text = ""
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            
            return text.strip()
        
        except Exception as e:
            raise Exception(f"PDF extraction failed: {e}")
    
    def _extract_from_docx(self, file_path: Path) -> str:
        """Extract text from DOCX"""
        
        try:
            doc = DocxDocument(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        
        except Exception as e:
            raise Exception(f"DOCX extraction failed: {e}")
    
    def _build_bible_prompt(self) -> str:
        """
        Build the complete Bible generation prompt
        
        Returns:
            Complete prompt for Claude
        """
        
        print("\n🔨 Building comprehensive prompt...")
        
        # Organize extracted texts by category
        pleadings = {}
        indices = {}
        late_disclosure_context = ""
        tribunal_rulings = ""
        
        for filename, data in self.extracted_texts.items():
            category = data['category']
            text = data['text']
            
            if category == 'pleadings':
                # Determine which pleading this is
                name_lower = filename.lower()
                if 'statement of claim' in name_lower and 'response' not in name_lower:
                    pleadings['claim'] = text
                elif 'defence' in name_lower and 'response' not in name_lower:
                    pleadings['defence'] = text
                elif 'reply' in name_lower or 'rejoinder' in name_lower:
                    if 'reply' not in pleadings:
                        pleadings['reply'] = text
                    else:
                        pleadings['rejoinder'] = text
            
            elif category == 'indices':
                # Determine which index
                if 'claimant' in filename.lower():
                    indices['claimant'] = text
                elif 'respondent' in filename.lower() or 'first respondent' in filename.lower():
                    indices['respondent'] = text
                else:
                    indices['other'] = text
            
            elif category == 'late_disclosure':
                # Sample of late disclosure
                if not late_disclosure_context:
                    late_disclosure_context = f"Sample documents from Folder 69 (15 Sep 2025 late disclosure):\n\n"
                
                late_disclosure_context += f"[{filename}]\n{text[:2000]}...\n\n"
            
            elif category == 'procedural':
                # Tribunal rulings
                tribunal_rulings += f"\n[{filename}]\n{text[:1500]}...\n\n"
        
        # Add legal authorities summary
        if self.legal_authorities_list:
            legal_auth_summary = "\n\nLEGAL AUTHORITIES REFERENCED:\n"
            legal_auth_summary += f"Total: {len(self.legal_authorities_list)} documents\n\n"
            
            # Group by folder
            by_folder = {}
            for auth in self.legal_authorities_list:
                folder = auth['folder']
                if folder not in by_folder:
                    by_folder[folder] = []
                by_folder[folder].append(auth['filename'])
            
            for folder, files in by_folder.items():
                legal_auth_summary += f"\n{folder}:\n"
                for file in files[:20]:  # Show first 20
                    legal_auth_summary += f"• {file}\n"
                if len(files) > 20:
                    legal_auth_summary += f"... and {len(files)-20} more\n"
            
            late_disclosure_context += "\n" + legal_auth_summary
        
        # Generate prompt using BiblePrompts
        prompt = self.prompts.generate_bible_prompt(
            pleadings=pleadings,
            indices=indices,
            late_disclosure_context=late_disclosure_context or "No late disclosure sampled.",
            tribunal_rulings=tribunal_rulings or "No tribunal rulings extracted."
        )
        
        print(f"   ✅ Prompt built ({len(prompt):,} characters)")
        
        return prompt
    
    def _generate_bible(self, prompt: str, use_extended_thinking: bool) -> str:
        """
        Call Claude to generate the Case Bible
        
        Args:
            prompt: Complete prompt
            use_extended_thinking: Use extended thinking
        
        Returns:
            Generated Case Bible text
        """
        
        print(f"\n🤖 Calling Claude to generate Case Bible...")
        print(f"   This is a LARGE job - will take 5-10 minutes")
        print(f"   Extended thinking: {'✅ YES' if use_extended_thinking else '❌ NO'}")
        
        # Estimate cost with accurate token counting
        print(f"\n📊 Counting tokens...")
        estimate = self.claude.estimate_cost_with_token_count(
            text=prompt,
            output_tokens=32000,
            model='claude-sonnet-4-5-20250929'
        )
        
        print(f"   Input tokens: {estimate['input_tokens']:,}")
        print(f"   Expected output tokens: {estimate['output_tokens']:,}")
        print(f"   💰 Estimated cost: £{estimate['gbp']:.2f}")
        
        # Confirm
        confirm = input("\n   Proceed with Bible generation? (y/n): ")
        if confirm.lower() != 'y':
            print("   ❌ Cancelled by user")
            sys.exit(0)
        
        print("\n   🔄 Generating... (this will take several minutes)")
        
        # Build system prompt
        system_prompt = self.prompts.get_system_prompt()
        
        # PREFILLING: Force Claude to start with exact format
        prefill_text = "═══════════════════════════════════════════════════════════════════════\n1. CASE OVERVIEW\n═══════════════════════════════════════════════════════════════════════\n\n"
        
        # Build messages with prefilling
        messages = [
            {
                'role': 'user',
                'content': prompt
            },
            {
                'role': 'assistant',
                'content': prefill_text  # ← Prefill forces exact format
            }
        ]
        
        # Call Claude with optimized settings
        thinking_config = None
        if use_extended_thinking:
            thinking_config = {
                'type': 'enabled',
                'budget_tokens': 20000  # Allow deep thinking
            }
        
        response = self.claude.create_message(
            messages=messages,
            system=[{
                'type': 'text',
                'text': system_prompt,
                'cache_control': {'type': 'ephemeral'}  # Cache system prompt
            }],
            max_tokens=32000,
            temperature=0.0,  # ← DETERMINISTIC for factual extraction!
            thinking=thinking_config
        )
        
        # Combine prefill + generated content
        bible_text = prefill_text + response['content']
        
        print(f"\n   ✅ Bible generated!")
        print(f"   Length: {len(bible_text):,} characters")
        print(f"   Actual cost: £{response['usage'].total_cost_gbp:.2f}")
        
        return bible_text
    
    def _save_bible(
        self,
        bible_text: str,
        organised: Dict,
        selected: Dict
    ) -> Path:
        """
        Save Case Bible (both formats) and metadata
        
        Args:
            bible_text: Generated Bible
            organised: Organised folders from classifier
            selected: Selected documents
        
        Returns:
            Path to saved Bible file
        """
        
        # Save plain text Bible
        bible_file = self.output_dir / "case_bible.txt"
        bible_file.write_text(bible_text, encoding='utf-8')
        
        print(f"\n✅ Plain text Bible saved: {bible_file}")
        
        # Parse and save structured Bible
        try:
            from utils.bible_parser import BibleParser
            
            print("\n📊 Generating structured Bible...")
            parser = BibleParser()
            structured = parser.parse_bible(bible_text)
            
            structured_file = self.output_dir / "case_bible_structured.json"
            with open(structured_file, 'w', encoding='utf-8') as f:
                json.dump(structured, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Structured Bible saved: {structured_file}")
            
        except Exception as e:
            print(f"⚠️  Could not generate structured Bible: {e}")
            print("   Plain text Bible is still available for queries.")
        
        # Create metadata
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        folders_by_priority = {
            'critical': len(organised['critical']),
            'high': len(organised['high']),
            'medium': len(organised['medium']),
            'legal_authorities': len(organised['legal_authorities']),
            'skip': len(organised['skip'])
        }
        
        docs_extracted = len(self.extracted_texts)
        
        metadata = BibleMetadata(
            case_id=self.case_id,
            case_name=self.case_name,
            build_date=datetime.now().isoformat(),
            folders_analysed=sum(folders_by_priority.values()),
            documents_extracted=docs_extracted,
            legal_authorities_noted=len(self.legal_authorities_list),
            total_cost_gbp=self.claude.total_cost_gbp,
            bible_length_chars=len(bible_text),
            bible_length_tokens_est=len(bible_text) // 4,
            folders_by_priority=folders_by_priority,
            build_duration_seconds=elapsed
        )
        
        # Save metadata
        metadata_file = self.output_dir / "case_bible_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(metadata), f, indent=2)
        
        print(f"✅ Metadata saved: {metadata_file}")
        
        # Save document list
        doc_list_file = self.output_dir / "extracted_documents.json"
        with open(doc_list_file, 'w', encoding='utf-8') as f:
            json.dump({
                'extracted': [
                    {
                        'filename': filename,
                        'category': data['category'],
                        'folder': data['folder'],
                        'length_chars': len(data['text'])
                    }
                    for filename, data in self.extracted_texts.items()
                ],
                'legal_authorities': self.legal_authorities_list
            }, f, indent=2)
        
        print(f"✅ Document list saved: {doc_list_file}")
        
        return bible_file


def main():
    """Test the Bible Builder"""
    
    # Configuration
    CASE_ROOT = Path(r"C:\Users\JemAndrew\Velitor\Communication site - Documents\LIS1.1")
    CASE_ID = "lismore_v_ph"
    CASE_NAME = "Lismore Capital Limited v Process Holdings Limited"
    CLAIMANT = "Lismore Capital Limited"
    RESPONDENT = "Process Holdings Limited (PH)"
    TRIBUNAL = "LCIA"
    
    # Build Bible
    builder = BibleBuilder(
        case_root=CASE_ROOT,
        case_id=CASE_ID,
        case_name=CASE_NAME,
        claimant=CLAIMANT,
        respondent=RESPONDENT,
        tribunal=TRIBUNAL
    )
    
    bible_path = builder.build_bible(use_extended_thinking=True)
    
    print("\n" + "="*70)
    print("🎉 DONE!")
    print("="*70)
    print(f"\nYour Case Bible is ready at:")
    print(f"   {bible_path}")
    print(f"\nThis will now be cached for all future queries,")
    print(f"saving 90% on costs for every question you ask!")


if __name__ == '__main__':
    main()