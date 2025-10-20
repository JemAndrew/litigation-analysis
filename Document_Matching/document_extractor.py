#!/usr/bin/env python3
"""
PHASE 1: Clean Metadata Extraction
Multi-page sampling to create unique document fingerprints

Extracts:
- Text from first, middle, and last pages
- Creates composite description (unique fingerprint)
- Extracts dates from content and filenames
- Calculates file size and page count

British English throughout.
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import logging

import pandas as pd
import PyPDF2
import pdfplumber
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# TEXT EXTRACTION - MULTI-PAGE SAMPLING
# ============================================================================

def extract_multipage_text(pdf_path: Path) -> Dict:
    """
    Extract text from multiple pages throughout document.
    
    Strategy:
    1. First page (0-1000 chars) - Title, header, parties
    2. Middle pages (sample 2-3 pages) - Body content
    3. Last page (0-500 chars) - Signatures, dates
    4. Composite: Concatenate all samples into unique fingerprint
    
    This prevents first-page duplicate false positives.
    """
    
    if not pdf_path.exists():
        return {
            'composite_description': 'FILE NOT FOUND',
            'page_count': 0,
            'extraction_method': 'FAILED',
            'text_length': 0
        }
    
    # Try pdfplumber first (better quality)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            text_samples = []
            
            # First page
            if total_pages >= 1:
                first_text = pdf.pages[0].extract_text() or ''
                first_clean = clean_text(first_text)[:1000]
                if first_clean:
                    text_samples.append(f"[P1] {first_clean}")
            
            # Middle pages (sample 2-3 from different sections)
            if total_pages >= 5:
                # Quarter point
                quarter_idx = total_pages // 4
                quarter_text = pdf.pages[quarter_idx].extract_text() or ''
                quarter_clean = clean_text(quarter_text)[:800]
                if quarter_clean:
                    text_samples.append(f"[P{quarter_idx+1}] {quarter_clean}")
                
                # Middle point
                middle_idx = total_pages // 2
                middle_text = pdf.pages[middle_idx].extract_text() or ''
                middle_clean = clean_text(middle_text)[:800]
                if middle_clean:
                    text_samples.append(f"[P{middle_idx+1}] {middle_clean}")
            
            elif total_pages >= 3:
                # Just middle for shorter docs
                middle_idx = total_pages // 2
                middle_text = pdf.pages[middle_idx].extract_text() or ''
                middle_clean = clean_text(middle_text)[:800]
                if middle_clean:
                    text_samples.append(f"[P{middle_idx+1}] {middle_clean}")
            
            # Last page
            if total_pages >= 2:
                last_text = pdf.pages[-1].extract_text() or ''
                last_clean = clean_text(last_text)[:500]
                if last_clean:
                    text_samples.append(f"[P{total_pages}] {last_clean}")
            
            # Create composite fingerprint
            composite = ' '.join(text_samples)
            
            # Limit total length
            if len(composite) > 3000:
                composite = composite[:3000]
            
            return {
                'composite_description': composite if composite else 'NO TEXT EXTRACTED',
                'page_count': total_pages,
                'extraction_method': 'pdfplumber',
                'text_length': len(composite)
            }
    
    except Exception as e:
        logger.warning(f"pdfplumber failed for {pdf_path.name}: {e}")
        
        # Fallback to PyPDF2
        try:
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                total_pages = len(pdf_reader.pages)
                text_samples = []
                
                # First page
                if total_pages >= 1:
                    first_text = pdf_reader.pages[0].extract_text() or ''
                    first_clean = clean_text(first_text)[:1000]
                    if first_clean:
                        text_samples.append(f"[P1] {first_clean}")
                
                # Middle
                if total_pages >= 3:
                    middle_idx = total_pages // 2
                    middle_text = pdf_reader.pages[middle_idx].extract_text() or ''
                    middle_clean = clean_text(middle_text)[:800]
                    if middle_clean:
                        text_samples.append(f"[P{middle_idx+1}] {middle_clean}")
                
                # Last page
                if total_pages >= 2:
                    last_text = pdf_reader.pages[-1].extract_text() or ''
                    last_clean = clean_text(last_text)[:500]
                    if last_clean:
                        text_samples.append(f"[P{total_pages}] {last_clean}")
                
                composite = ' '.join(text_samples)
                
                if len(composite) > 3000:
                    composite = composite[:3000]
                
                return {
                    'composite_description': composite if composite else 'NO TEXT EXTRACTED',
                    'page_count': total_pages,
                    'extraction_method': 'PyPDF2',
                    'text_length': len(composite)
                }
        
        except Exception as e2:
            logger.error(f"All extraction failed for {pdf_path.name}: {e2}")
            return {
                'composite_description': 'EXTRACTION FAILED',
                'page_count': 0,
                'extraction_method': 'FAILED',
                'text_length': 0
            }


def clean_text(text: str) -> str:
    """Clean and normalise extracted text"""
    if not text:
        return ''
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove PDF artifacts
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    return text.strip()


# ============================================================================
# DATE EXTRACTION
# ============================================================================

def extract_dates(pdf_path: Path, text_content: str) -> str:
    """
    Extract date from:
    1. Filename patterns
    2. Document content (common date formats)
    3. PDF metadata
    
    Returns: YYYY-MM-DD or 'NO DATE FOUND'
    """
    
    # Try filename first
    filename_date = extract_date_from_filename(pdf_path.name)
    if filename_date != 'NO DATE FOUND':
        return filename_date
    
    # Try content
    content_date = extract_date_from_content(text_content)
    if content_date != 'NO DATE FOUND':
        return content_date
    
    return 'NO DATE FOUND'


def extract_date_from_filename(filename: str) -> str:
    """Extract date from filename patterns"""
    
    patterns = [
        r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
        r'(\d{2}-\d{2}-\d{4})',  # DD-MM-YYYY
        r'(\d{8})',              # YYYYMMDD
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            date_str = match.group(1)
            try:
                if len(date_str) == 8:
                    date_obj = datetime.strptime(date_str, '%Y%m%d')
                elif '-' in date_str:
                    parts = date_str.split('-')
                    if len(parts[0]) == 4:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    else:
                        date_obj = datetime.strptime(date_str, '%d-%m-%Y')
                
                return date_obj.strftime('%Y-%m-%d')
            except:
                pass
    
    return 'NO DATE FOUND'


def extract_date_from_content(text: str) -> str:
    """Extract date from document content"""
    
    if not text:
        return 'NO DATE FOUND'
    
    # Common legal document date patterns
    patterns = [
        r'dated?\s+(\d{1,2}\s+\w+\s+\d{4})',  # "dated 28 March 2024"
        r'(\d{1,2}\s+\w+\s+\d{4})',           # "28 March 2024"
        r'(\d{1,2}/\d{1,2}/\d{4})',           # "28/03/2024"
        r'(\d{4}-\d{2}-\d{2})',               # "2024-03-28"
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text[:2000])  # Search first 2000 chars
        if matches:
            date_str = matches[0]
            try:
                # Try parsing
                if '/' in date_str:
                    date_obj = datetime.strptime(date_str, '%d/%m/%Y')
                elif '-' in date_str:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                else:
                    # Try month name format
                    date_obj = datetime.strptime(date_str, '%d %B %Y')
                
                return date_obj.strftime('%Y-%m-%d')
            except:
                try:
                    date_obj = datetime.strptime(date_str, '%d %b %Y')
                    return date_obj.strftime('%Y-%m-%d')
                except:
                    pass
    
    return 'NO DATE FOUND'


# ============================================================================
# METADATA GENERATION
# ============================================================================

def generate_metadata(source_dir: Path, folder_name: str) -> pd.DataFrame:
    """Generate enhanced metadata for all PDFs in directory"""
    
    print(f"\n{'='*80}")
    print(f"EXTRACTING: {folder_name}")
    print(f"{'='*80}")
    print(f"Source: {source_dir}")
    
    # Find all PDFs (recursively)
    pdf_files = list(source_dir.rglob('*.pdf'))
    
    if not pdf_files:
        print(f"❌ No PDF files found!")
        return pd.DataFrame()
    
    print(f"Found {len(pdf_files)} PDF files")
    
    results = []
    
    for pdf_path in tqdm(pdf_files, desc=f"Extracting {folder_name}"):
        # Extract reference from filename
        reference = pdf_path.stem
        
        # Get file size
        file_size_bytes = pdf_path.stat().st_size
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
        
        # Extract multi-page text
        extraction = extract_multipage_text(pdf_path)
        
        # Extract date
        date = extract_dates(pdf_path, extraction['composite_description'])
        
        # Build record
        record = {
            'Reference': reference,
            'Date': date,
            'Description': extraction['composite_description'],
            'Source Folder': folder_name,
            'File Name': pdf_path.name,
            'File Path': str(pdf_path),
            'Extraction Method': extraction['extraction_method'],
            'Text Length': extraction['text_length'],
            'Page Count': extraction['page_count'],
            'File Size (MB)': file_size_mb,
        }
        
        results.append(record)
    
    df = pd.DataFrame(results)
    
    # Summary
    print(f"\n📊 Extraction Summary:")
    print(f"   Total: {len(df)}")
    
    successful = df[df['Extraction Method'] != 'FAILED']
    failed = df[df['Extraction Method'] == 'FAILED']
    
    print(f"   ✅ Success: {len(successful)} ({len(successful)/len(df)*100:.1f}%)")
    print(f"   ❌ Failed: {len(failed)} ({len(failed)/len(df)*100:.1f}%)")
    
    has_date = df[df['Date'] != 'NO DATE FOUND']
    print(f"   📅 With dates: {len(has_date)} ({len(has_date)/len(df)*100:.1f}%)")
    
    return df


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    PHASE 1: Extract metadata for Folders 01, 02, and 03
    """
    
    print("="*80)
    print("PHASE 1: CLEAN METADATA EXTRACTION")
    print("Multi-Page Sampling for Unique Document Fingerprints")
    print("="*80)
    
    # Paths
    base_dir = Path(r"C:\Users\JemAndrew\Velitor\Communication site - Documents\LIS1.1\73. Review of PHL Disclosures")
    output_dir = Path(r"C:\Users\JemAndrew\OneDrive - Velitor\Claude\litigation_analysis\cases\lismore_v_ph\analysis")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # STEP 1: Extract Folder 01
    print(f"\n{'='*80}")
    print("STEP 1: FOLDER 01 (C- Exhibits)")
    print(f"{'='*80}")
    
    folder_01_dir = base_dir / "01. Claimant's Factual Exhibits"
    
    if not folder_01_dir.exists():
        print(f"❌ Folder not found: {folder_01_dir}")
        return
    
    df_01 = generate_metadata(folder_01_dir, "Folder 01")
    
    if len(df_01) == 0:
        print("❌ No documents extracted from Folder 01")
        return
    
    output_01 = output_dir / f"Folder_01_Enhanced_{timestamp}.xlsx"
    df_01.to_excel(output_01, index=False)
    print(f"✅ Saved: {output_01.name}")
    
    # STEP 2: Extract Folder 02
    print(f"\n{'='*80}")
    print("STEP 2: FOLDER 02 (PHL Disclosure)")
    print(f"{'='*80}")
    
    folder_02_dir = base_dir / "02. PHL Disclosure prior to 23 June"
    
    if not folder_02_dir.exists():
        print(f"❌ Folder not found: {folder_02_dir}")
        return
    
    df_02 = generate_metadata(folder_02_dir, "Folder 02")
    
    if len(df_02) == 0:
        print("❌ No documents extracted from Folder 02")
        return
    
    output_02 = output_dir / f"Folder_02_Enhanced_{timestamp}.xlsx"
    df_02.to_excel(output_02, index=False)
    print(f"✅ Saved: {output_02.name}")
    
    # STEP 3: Combine Folders 01 & 02
    print(f"\n{'='*80}")
    print("STEP 3: COMBINE FOLDERS 01 & 02")
    print(f"{'='*80}")
    
    df_01_02 = pd.concat([df_01, df_02], ignore_index=True)
    
    output_01_02 = output_dir / f"Folders_01_02_Enhanced_{timestamp}.xlsx"
    df_01_02.to_excel(output_01_02, index=False)
    
    print(f"\n📊 Combined Statistics:")
    print(f"   Folder 01: {len(df_01)} documents")
    print(f"   Folder 02: {len(df_02)} documents")
    print(f"   Total: {len(df_01_02)} documents")
    print(f"\n✅ Saved: {output_01_02.name}")
    
    # STEP 4: Extract Folder 03
    print(f"\n{'='*80}")
    print("STEP 4: FOLDER 03 (Restricted Disclosure)")
    print(f"{'='*80}")
    
    folder_03_dir = base_dir / "03. Erroneously restricted documents"
    
    if not folder_03_dir.exists():
        print(f"❌ Folder not found: {folder_03_dir}")
        return
    
    df_03 = generate_metadata(folder_03_dir, "Folder 03")
    
    if len(df_03) == 0:
        print("❌ No documents extracted from Folder 03")
        return
    
    output_03 = output_dir / f"Folder_03_Enhanced_{timestamp}.xlsx"
    df_03.to_excel(output_03, index=False)
    print(f"✅ Saved: {output_03.name}")
    
    # FINAL SUMMARY
    print(f"\n{'='*80}")
    print("✅ PHASE 1 COMPLETE: METADATA EXTRACTION")
    print(f"{'='*80}")
    
    print(f"\n📂 Output Files Created:")
    print(f"   1. {output_01.name}")
    print(f"   2. {output_02.name}")
    print(f"   3. {output_01_02.name}  ← Use this for matching")
    print(f"   4. {output_03.name}")
    
    print(f"\n📊 Document Counts:")
    print(f"   Source (01+02): {len(df_01_02)}")
    print(f"   Target (03): {len(df_03)}")
    
    print(f"\n💡 Key Improvements:")
    print(f"   ✅ Multi-page text sampling (not just first page)")
    print(f"   ✅ Unique document fingerprints")
    print(f"   ✅ Prevents first-page duplicate false positives")
    print(f"   ✅ Better date extraction from content")
    
    print(f"\n🚀 NEXT STEP: Run Phase 2 (Bidirectional Matching)")
    print(f"   python enhanced_bidirectional_matcher.py")
    
    print(f"\n{'='*80}\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()