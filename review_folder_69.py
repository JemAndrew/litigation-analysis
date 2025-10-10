#!/usr/bin/env python3
"""
Review Folder 69 - Main Entry Point
British English throughout
"""

import sys
from pathlib import Path
import os

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from intelligence.reviewer import EnhancedFolder69Reviewer


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║           FOLDER 69 LATE DISCLOSURE REVIEW                           ║
╚══════════════════════════════════════════════════════════════════════╝

Analyses documents with detailed scoring and explanations.
    """)
    
    # Check API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("\n❌ ERROR: ANTHROPIC_API_KEY not set!")
        print("\nWindows: $env:ANTHROPIC_API_KEY = 'your-key'")
        print("Linux/Mac: export ANTHROPIC_API_KEY='your-key'")
        return
    
    # Paths
    case_dir = project_root / "cases" / "lismore_v_ph"
    folder_69_path = case_dir / "documents" / "69. Late Disclosure"
    matched_excel = None
    
    # Check folders exist
    if not folder_69_path.exists():
        print(f"\n❌ Folder not found: {folder_69_path}")
        print(f"\nCreate directory and add documents")
        return
    
    # Count documents
    doc_count = len(list(folder_69_path.rglob('*.pdf'))) + len(list(folder_69_path.rglob('*.docx')))
    
    if doc_count == 0:
        print(f"\n⚠️  No documents in: {folder_69_path}")
        return
    
    print(f"\n📂 Found {doc_count} documents")
    
    # Initialize
    print("\n" + "="*70)
    print("INITIALIZING REVIEWER")
    print("="*70 + "\n")
    
    try:
        reviewer = EnhancedFolder69Reviewer(
            case_dir=case_dir,
            folder_69_path=folder_69_path,
            matched_excel_path=matched_excel,
            claimant="Lismore Limited",
            respondent="Process Holdings plc"
        )
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Menu
    print("\n" + "="*70)
    print("OPTIONS")
    print("="*70)
    print("\n1. Full review (ingest + analyse all + export)")
    print("2. Sample review (10 documents)")
    print("3. Ingest only")
    print("4. Analyse only")
    print("5. Export results")
    print("6. Executive summary")
    print("7. Exit")
    
    try:
        choice = input("\nSelect (1-7): ").strip()
        
        if choice == '1':
            print("\n🚀 FULL REVIEW")
            print("⏱️  30-90 minutes")
            print("💰 £200-400")
            if input("\nProceed? (y/n): ").lower() == 'y':
                reviewer.run_complete_review()
        
        elif choice == '2':
            print("\n🧪 SAMPLE (10 docs)")
            print("⏱️  10-15 minutes")
            print("💰 £3-5")
            if input("\nProceed? (y/n): ").lower() == 'y':
                reviewer.run_complete_review(sample_size=10)
        
        elif choice == '3':
            reviewer.ingest_documents()
        
        elif choice == '4':
            if input("\nDocuments ingested? (y/n): ").lower() == 'y':
                reviewer.analyse_all_documents()
                reviewer.export_detailed_excel()
                reviewer.generate_executive_summary()
        
        elif choice == '5':
            if reviewer.document_scores:
                reviewer.export_detailed_excel()
            else:
                print("❌ No scores. Run analysis first.")
        
        elif choice == '6':
            if reviewer.document_scores:
                reviewer.generate_executive_summary()
            else:
                print("❌ No scores. Run analysis first.")
        
        elif choice == '7':
            print("\n👋 Goodbye!")
        
        else:
            print("\n❌ Invalid choice")
    
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()