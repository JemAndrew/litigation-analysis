#!/usr/bin/env python3
"""
Review Folder 69 - Main Entry Point
Direct OneDrive access - no copying needed!
British English throughout
"""

import sys
from pathlib import Path
import os

# Load .env file FIRST
from dotenv import load_dotenv
load_dotenv()

# Add src directory to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'src'))

from src.intelligence.reviewer import Folder69Reviewer


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║           FOLDER 69 LATE DISCLOSURE REVIEW                           ║
╚══════════════════════════════════════════════════════════════════════╝

Analyses documents with detailed scoring and explanations.
    """)
    
    # Check API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not api_key:
        print("\n❌ ERROR: ANTHROPIC_API_KEY not found!")
        print("\n📄 Check your .env file")
        return
    
    print(f"✅ API key loaded: {api_key[:20]}...")
    
    # Paths
    case_dir = project_root / "cases" / "lismore_v_ph"
    
    # DIRECT PATH TO YOUR ONEDRIVE LOCATION (no copying needed!)
    folder_69_path = Path(r"C:\Users\JemAndrew\Velitor\Communication site - Documents\LIS1.1\69. PHL's disclosure (15 September 2025)")
    
    # Check if matched Excel exists
    excel_dir = case_dir / "analysis" / "folder_69_review"
    matched_excel = None
    
    if excel_dir.exists():
        excel_files = list(excel_dir.glob('Matched_Documents_*.xlsx'))
        if excel_files:
            matched_excel = sorted(excel_files)[-1]
            print(f"✅ Found metadata Excel: {matched_excel.name}")
    else:
        print("⚠️  No metadata Excel found (will use filenames)")
    
    # Check folder exists
    if not folder_69_path.exists():
        print(f"\n❌ Folder not found: {folder_69_path}")
        print(f"\n💡 Update the path in review_folder_69.py (line 38)")
        return
    
    # Count documents (directly from OneDrive)
    print(f"\n📂 Reading from OneDrive: {folder_69_path.name}")
    
    pdf_files = list(folder_69_path.rglob('*.pdf'))
    docx_files = list(folder_69_path.rglob('*.docx'))
    doc_count = len(pdf_files) + len(docx_files)
    
    if doc_count == 0:
        print(f"\n⚠️  No documents found in: {folder_69_path}")
        return
    
    print(f"\n📊 Found {doc_count} documents:")
    print(f"   PDFs: {len(pdf_files)}")
    print(f"   DOCXs: {len(docx_files)}")
    print(f"\n💡 Files will be read directly from OneDrive (on-demand)")
    
    # Initialize reviewer
    print("\n" + "="*70)
    print("INITIALISING REVIEWER")
    print("="*70 + "\n")
    
    try:
        reviewer = Folder69Reviewer(
            case_dir=case_dir,
            folder_69_path=folder_69_path,  # Direct OneDrive path
            matched_excel_path=matched_excel,
            claimant="Lismore Limited",
            respondent="Process Holdings plc"
        )
    except Exception as e:
        print(f"\n❌ Initialisation error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Menu
    print("\n" + "="*70)
    print("OPTIONS")
    print("="*70)
    print("\n1. 🚀 Full review (ingest + analyse all + export)")
    print("2. 🧪 Sample review (10 documents for testing)")
    print("3. 📥 Ingest documents only")
    print("4. 🔍 Analyse documents only (must ingest first)")
    print("5. 📊 Export results to Excel")
    print("6. 📝 Generate executive summary")
    print("7. 🚪 Exit")
    
    try:
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == '1':
            print("\n🚀 FULL REVIEW - ALL DOCUMENTS")
            print("="*70)
            print(f"\n📊 Statistics:")
            print(f"   Documents to analyse: {doc_count}")
            print(f"   Estimated time: {doc_count * 1.5 / 60:.0f}-{doc_count * 2 / 60:.0f} minutes")
            print(f"   Estimated cost: £{doc_count * 0.35:.2f}")
            print(f"\n📁 Reading directly from OneDrive (files download on-demand)")
            
            confirm = input("\n⚠️  Proceed with full analysis? (y/n): ")
            if confirm.lower() == 'y':
                reviewer.run_complete_review()
            else:
                print("\n❌ Cancelled.")
        
        elif choice == '2':
            print("\n🧪 SAMPLE REVIEW - 10 DOCUMENTS")
            print("="*70)
            print(f"\n📊 Statistics:")
            print(f"   Documents to analyse: 10")
            print(f"   Estimated time: 10-15 minutes")
            print(f"   Estimated cost: £3-5")
            print(f"\n📁 Reading directly from OneDrive")
            
            confirm = input("\n✅ Proceed with sample? (y/n): ")
            if confirm.lower() == 'y':
                reviewer.run_complete_review(sample_size=10)
            else:
                print("\n❌ Cancelled.")
        
        elif choice == '3':
            print("\n📥 INGESTING DOCUMENTS")
            print("="*70)
            print(f"📁 Reading from OneDrive (files download on-demand)")
            reviewer.ingest_documents()
        
        elif choice == '4':
            stats = reviewer.vector_store.get_stats()
            if stats.get('total_documents', 0) == 0:
                print("\n❌ No documents ingested yet!")
                print("💡 Run Option 3 first to ingest documents.")
            else:
                print(f"\n✅ Vector store has {stats['total_documents']} documents")
                print("\n🔍 ANALYSING ALL DOCUMENTS")
                print("="*70)
                
                confirm = input(f"\n⚠️  Analyse {doc_count} documents? (y/n): ")
                if confirm.lower() == 'y':
                    reviewer.analyse_all_documents()
                    reviewer.export_detailed_excel()
                    reviewer.generate_executive_summary()
        
        elif choice == '5':
            if reviewer.document_scores:
                print("\n📊 EXPORTING TO EXCEL")
                print("="*70)
                reviewer.export_detailed_excel()
            else:
                print("\n❌ No scores to export!")
                print("💡 Run analysis first (Option 1, 2, or 4).")
        
        elif choice == '6':
            if reviewer.document_scores:
                print("\n📝 GENERATING EXECUTIVE SUMMARY")
                print("="*70)
                reviewer.generate_executive_summary()
            else:
                print("\n❌ No scores for summary!")
                print("💡 Run analysis first (Option 1, 2, or 4).")
        
        elif choice == '7':
            print("\n👋 Goodbye!")
        
        else:
            print("\n❌ Invalid choice. Select 1-7.")
    
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during operation: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()