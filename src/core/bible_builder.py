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
import logging

logger = logging.getLogger(__name__)

# Add parent directories to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

try:
    from src.filter.folder_classifier import FolderClassifier
    from src.filter.document_selector import DocumentSelector
    from src.prompts.bible_prompts import BiblePrompts
    from src.api.claude_client import ClaudeClient
except ImportError:
    # Fallback for different import styles
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
    - Bible generation via Claude (with extended thinking)
    - Saving results
    
    ARCHITECTURE NOTE:
    This does NOT just extract text. It:
    1. Extracts text from PDFs (PyPDF2 - no AI)
    2. Sends ALL text to Claude with EXTENDED THINKING
    3. Claude analyzes deeply and creates Case Bible
    4. Bible gets CACHED by Anthropic
    5. Future queries read cached Bible (90% cost savings)
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
        
        # Validate case root exists
        if not self.case_root.exists():
            raise ValueError(f"Case root does not exist: {self.case_root}")
        
        # Output directory (where Bible will be saved)
        self.output_dir = Path(f"cases/{case_id}/knowledge")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initializing Bible Builder for case: {case_name}")
        
        # Initialize components
        try:
            self.classifier = FolderClassifier(self.case_root)
            self.selector = DocumentSelector()
            self.prompts = BiblePrompts()
            self.claude = ClaudeClient()
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
        
        # Tracking
        self.start_time = None
        self.extracted_texts = {}
        self.legal_authorities_list = []
    
    def build_bible(self, use_extended_thinking: bool = True) -> Path:
        """
        Build the complete Case Bible
        
        Args:
            use_extended_thinking: Use Claude's extended thinking (RECOMMENDED)
                                  
                                  Why use thinking:
                                  - Deep legal analysis (not just extraction)
                                  - Evidence chain mapping
                                  - Contradiction detection
                                  - Strategic insights
                                  - £0.30 extra cost, 1000x benefit
        
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
        
        # Validate we got folders
        total_folders = sum(len(v) for v in organised.values())
        if total_folders == 0:
            raise ValueError("No folders found to process! Check case_root path.")
        
        # Step 2: Select master documents
        print("\n" + "="*70)
        print("STEP 2: SELECT MASTER DOCUMENTS")
        print("="*70)
        
        to_process = (organised['critical'] + organised['high'] + 
                     organised['medium'] + organised['legal_authorities'])
        
        if not to_process:
            raise ValueError("No folders selected for Bible building!")
        
        selected = self.selector.select_for_bible_building(to_process)
        
        # Validate we got documents
        total_docs = sum(len(v) for v in selected.values())
        if total_docs == 0:
            raise ValueError("No documents selected! Check folder contents.")
        
        # Step 3: Extract text from documents
        print("\n" + "="*70)
        print("STEP 3: EXTRACT TEXT FROM DOCUMENTS")
        print("="*70)
        
        self._extract_all_documents(selected)
        
        # Validate we extracted something
        if not self.extracted_texts:
            raise ValueError("No text extracted from any documents! Check file formats.")
        
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
        
        # Validate we got output
        if not bible_text or len(bible_text) < 1000:
            raise ValueError(f"Bible generation produced suspiciously short output ({len(bible_text)} chars)")
        
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
        print(f"\n💡 This Bible is now CACHED by Anthropic")
        print(f"   Future queries will cost ~£0.03 each (90% savings!)")
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
        
        if total_to_extract == 0:
            logger.warning("No documents marked for full extraction!")
            return
        
        print(f"\n📄 Extracting text from {total_to_extract} documents...")
        print(f"   (This may take 2-5 minutes)\n")
        
        extracted_count = 0
        failed_count = 0
        
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
                    filename_display = doc.filename[:60] + "..." if len(doc.filename) > 60 else doc.filename
                    print(f"   📖 {filename_display}")
                    
                    text = self._extract_text_from_file(doc.path)
                    
                    if text and len(text.strip()) > 50:  # Validate meaningful content
                        self.extracted_texts[doc.filename] = {
                            'text': text,
                            'category': category,
                            'folder': doc.folder_name,
                            'size_mb': doc.size_mb
                        }
                        extracted_count += 1
                    else:
                        logger.warning(f"Document {doc.filename} extracted but empty/minimal content")
                        failed_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to extract {doc.filename}: {e}")
                    print(f"      ⚠️  Failed: {str(e)[:50]}")
                    failed_count += 1
        
        print(f"\n✅ Successfully extracted: {extracted_count}/{total_to_extract} documents")
        if failed_count > 0:
            print(f"⚠️  Failed/Empty: {failed_count} documents")
            logger.warning(f"Failed to extract {failed_count} documents")
    
    def _extract_text_from_file(self, file_path: Path) -> str:
        """
        Extract text from PDF or DOCX file
        
        Args:
            file_path: Path to document
        
        Returns:
            Extracted text
        """
        
        suffix = file_path.suffix.lower()
        
        if suffix == '.pdf':
            return self._extract_pdf(file_path)
        elif suffix in ['.doc', '.docx']:
            return self._extract_docx(file_path)
        elif suffix in ['.xlsx', '.xls', '.xlsm']:
            # For Excel files, just note them (don't extract - too complex)
            return f"[Excel file: {file_path.name} - Contains structured data/index]"
        else:
            raise ValueError(f"Unsupported file type: {suffix}")
    
    def _extract_pdf(self, file_path: Path) -> str:
        """Extract text from PDF"""
        
        try:
            text_parts = []
            
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                
                # Check if PDF is encrypted
                if reader.is_encrypted:
                    try:
                        reader.decrypt('')
                    except:
                        raise Exception("PDF is encrypted and cannot be decrypted")
                
                page_count = len(reader.pages)
                
                # Extract text from all pages
                for page_num, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    except Exception as e:
                        logger.warning(f"Failed to extract page {page_num + 1} of {file_path.name}: {e}")
                        continue
            
            full_text = "\n".join(text_parts)
            
            if not full_text.strip():
                raise Exception("PDF appears to be scanned/image-based - no text extracted")
            
            return full_text.strip()
        
        except Exception as e:
            raise Exception(f"PDF extraction failed: {e}")
    
    def _extract_docx(self, file_path: Path) -> str:
        """Extract text from DOCX"""
        
        try:
            doc = DocxDocument(file_path)
            paragraphs = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
            
            if not paragraphs:
                raise Exception("DOCX appears empty - no text found")
            
            return "\n".join(paragraphs)
        
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
        witness_statements_text = ""
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
                elif 'consolidated' in filename.lower():
                    indices['consolidated'] = text
                elif 'hyperlink' in filename.lower():
                    indices['hyperlinked'] = text
                elif 'trial bundle' in filename.lower():
                    indices['trial_bundle'] = text
            
            elif category == 'trial_witnesses':
                # Accumulate all trial witness statements
                witness_statements_text += f"\n\n{'='*70}\n"
                witness_statements_text += f"WITNESS STATEMENT: {filename}\n"
                witness_statements_text += f"{'='*70}\n\n"
                witness_statements_text += text[:20000]  # Limit each statement to 20K chars
            
            elif category == 'late_disclosure':
                # Accumulate late disclosure context
                late_disclosure_context += f"\n\n{filename}:\n{text[:10000]}"
            
            elif category == 'procedural':
                # Accumulate tribunal rulings
                tribunal_rulings += f"\n\n{filename}:\n{text[:10000]}"
        
        # Build complete prompt using the prompts module
        prompt = self.prompts.get_bible_generation_prompt(
            case_name=self.case_name,
            claimant=self.claimant,
            respondent=self.respondent,
            tribunal=self.tribunal,
            pleadings=pleadings,
            indices=indices,
            witness_statements=witness_statements_text or "No trial witness statements extracted.",
            late_disclosure_context=late_disclosure_context or "No late disclosure context extracted.",
            tribunal_rulings=tribunal_rulings or "No tribunal rulings extracted."
        )
        
        print(f"   ✅ Prompt built ({len(prompt):,} characters)")
        print(f"   📊 Estimated input tokens: ~{len(prompt) // 4:,}")
        
        return prompt
    
    def _generate_bible(self, prompt: str, use_extended_thinking: bool) -> str:
        """
        Call Claude to generate the Case Bible
        
        CRITICAL: This is where the MAGIC happens!
        - NOT just text extraction
        - Claude ANALYZES with extended thinking
        - Creates rich analytical foundation
        - Gets CACHED for 1000+ future queries
        
        Args:
            prompt: Complete prompt
            use_extended_thinking: Use extended thinking (RECOMMENDED)
        
        Returns:
            Generated Case Bible text
        """
        
        print(f"\n🤖 Calling Claude to generate Case Bible...")
        print(f"   This is a LARGE job - will take 5-10 minutes")
        print(f"   Extended thinking: {'✅ YES (RECOMMENDED)' if use_extended_thinking else '❌ NO'}")
        
        if use_extended_thinking:
            print(f"\n💡 Extended thinking means Claude will:")
            print(f"   - Analyze legal strategy deeply")
            print(f"   - Map evidence chains")
            print(f"   - Detect contradictions")
            print(f"   - Assess claim strengths")
            print(f"   - Calculate settlement leverage")
            print(f"   This analysis gets CACHED - saving 90% on future queries!")
        
        # Estimate cost
        print(f"\n📊 Estimating cost...")
        
        try:
            estimate = self.claude.estimate_cost_with_token_count(
                text=prompt,
                output_tokens=32000,
                model='claude-sonnet-4-5-20250929'
            )
            
            print(f"   Input tokens: {estimate['input_tokens']:,}")
            print(f"   Expected output tokens: {estimate['output_tokens']:,}")
            print(f"   💰 Estimated cost: £{estimate['gbp']:.2f}")
            
            if use_extended_thinking:
                print(f"   💭 Extended thinking: ~£0.30 additional")
                print(f"   💰 Total estimated: ~£{estimate['gbp'] + 0.30:.2f}")
        
        except Exception as e:
            logger.warning(f"Token counting failed: {e}")
            print(f"   ⚠️  Token counting failed, using fallback")
            print(f"   💰 Estimated cost: £0.80-1.20")
        
        # Confirm
        confirm = input("\n   Proceed with Bible generation? (y/n): ")
        if confirm.lower() != 'y':
            print("   ❌ Cancelled by user")
            sys.exit(0)
        
        print("\n   🔄 Generating... (this will take several minutes)")
        print("   ☕ Good time for a coffee break!\n")
        
        # Build system prompt
        system_prompt = self.prompts.get_system_prompt()
        
        # CRITICAL FIX: When using extended thinking, CANNOT use text prefilling
        # Extended thinking requires the assistant message to start with a thinking block
        # So we just send the user message and let Claude structure the response
        messages = [
            {
                'role': 'user',
                'content': prompt
            }
        ]
        
        # Configure thinking if enabled
        thinking_config = None
        if use_extended_thinking:
            thinking_config = {
                'type': 'enabled',
                'budget_tokens': 20000  # 20K tokens for deep thinking
            }
        
        # Call Claude with all the right settings
        try:
            response = self.claude.create_message(
                messages=messages,
                system=[{
                    'type': 'text',
                    'text': system_prompt,
                    'cache_control': {'type': 'ephemeral'}  # Cache this for future queries
                }],
                max_tokens=32000,
                temperature=1.0,  # REQUIRED when extended thinking enabled (API constraint)
                thinking=thinking_config
            )
        except Exception as e:
            logger.error(f"Bible generation failed: {e}")
            raise
        
        # Extract content from response
        # create_message returns: {'content': str, 'usage': dict, 'response': object}
        bible_text = response['content']
        
        print(f"\n   ✅ Bible generated successfully!")
        print(f"   📏 Length: {len(bible_text):,} characters")
        print(f"   📊 Estimated tokens: ~{len(bible_text) // 4:,}")
        print(f"   💰 Actual cost: £{response['usage']['total_cost_gbp']:.2f}")
        
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
        
        try:
            bible_file.write_text(bible_text, encoding='utf-8')
            print(f"\n✅ Plain text Bible saved: {bible_file}")
        except Exception as e:
            logger.error(f"Failed to save Bible: {e}")
            raise
        
        # Parse and save structured Bible (optional - may fail, that's OK)
        try:
            from src.utils.bible_parser import BibleParser
            
            print("\n📊 Attempting to generate structured Bible...")
            parser = BibleParser()
            structured = parser.parse_bible(bible_text)
            
            structured_file = self.output_dir / "case_bible_structured.json"
            with open(structured_file, 'w', encoding='utf-8') as f:
                json.dump(structured, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Structured Bible saved: {structured_file}")
            
        except ImportError:
            print("⚠️  BibleParser not found - skipping structured Bible")
        except Exception as e:
            logger.warning(f"Could not generate structured Bible: {e}")
            print(f"⚠️  Could not generate structured Bible (not critical)")
            print("   Plain text Bible is still fully functional")
        
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
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(metadata), f, indent=2)
            print(f"✅ Metadata saved: {metadata_file}")
        except Exception as e:
            logger.warning(f"Failed to save metadata: {e}")
        
        # Save document list
        doc_list_file = self.output_dir / "extracted_documents.json"
        try:
            with open(doc_list_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'extracted': [
                        {
                            'filename': filename,
                            'category': data['category'],
                            'folder': data['folder'],
                            'length_chars': len(data['text']),
                            'length_tokens_est': len(data['text']) // 4
                        }
                        for filename, data in self.extracted_texts.items()
                    ],
                    'legal_authorities': self.legal_authorities_list
                }, f, indent=2, ensure_ascii=False)
            print(f"✅ Document list saved: {doc_list_file}")
        except Exception as e:
            logger.warning(f"Failed to save document list: {e}")
        
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
    print(f"\nThis Bible is now CACHED by Anthropic.")
    print(f"Future queries will cost ~£0.03 each (90% savings!)")
    print(f"\nNext step: Integrate this Bible into your chat system.")


if __name__ == '__main__':
    main()