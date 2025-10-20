#!/usr/bin/env python3
"""
Build Case Bible - Entry Point

Simple script to build the Case Bible.
Run this ONCE per case (or when case significantly changes).

Usage:
    python build_bible.py

British English throughout.
"""

from pathlib import Path
from src.core.bible_builder import BibleBuilder


def main():
    """Build Case Bible"""
    
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                     CASE BIBLE BUILDER                            ║
║                                                                   ║
║  This will analyse your case documents and build a comprehensive ║
║  Case Bible that will be cached for all future queries.          ║
║                                                                   ║
║  ONE-TIME COST: £1-2 (with accurate token counting!)             ║
║  Time required: 10-15 minutes                                     ║
║  Future query cost: £0.30 (95% savings with caching!)            ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    # Configuration
    CASE_ROOT = Path(r"C:\Users\JemAndrew\Velitor\Communication site - Documents\LIS1.1")
    CASE_ID = "lismore_v_ph"
    CASE_NAME = "Lismore Capital Limited v Process Holdings Limited"
    CLAIMANT = "Lismore Capital Limited"
    RESPONDENT = "Process Holdings Limited (PH)"
    TRIBUNAL = "LCIA"
    
    # Confirm
    print(f"\nCase: {CASE_NAME}")
    print(f"Root: {CASE_ROOT}")
    print(f"\n📋 WHAT THIS WILL DO:")
    print(f"  1. Classify 74 folders intelligently")
    print(f"  2. Select ~40-44 Bible-critical documents")
    print(f"  3. Extract text from selected documents")
    print(f"  4. Generate comprehensive Case Bible with Claude")
    print(f"  5. Save Bible to cases/{CASE_ID}/")
    print(f"\n💰 COST BREAKDOWN:")
    print(f"  • Input: ~90-120K tokens = £0.27-0.36")
    print(f"  • Output: ~60-80K tokens = £0.90-1.20")
    print(f"  • Extended thinking: ~20K tokens = £0.06")
    print(f"  • TOTAL: £1.00-1.30")
    print(f"\n⏱️  TIME: 10-15 minutes (mostly Claude thinking)")
    
    confirm = input("\n✅ Proceed with Bible generation? (y/n): ")
    if confirm.lower() != 'y':
        print("\n❌ Cancelled")
        return
    
    # Verify case root exists
    if not CASE_ROOT.exists():
        print(f"\n❌ ERROR: Case root not found at {CASE_ROOT}")
        print(f"\nPlease verify the path in build_bible.py")
        return
    
    # Build Bible
    try:
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
        print("✅ CASE BIBLE BUILD COMPLETE!")
        print("="*70)
        print(f"\n📄 Bible saved to: {bible_path}")
        print(f"\n🚀 NEXT STEPS:")
        print(f"  1. Review the Case Bible at: {bible_path}")
        print(f"  2. Use chat.py to ask questions (Bible will be cached)")
        print(f"  3. Each query will cost ~£0.30 instead of £2-5!")
        print(f"\n💡 The Bible is the foundation - everything builds on it!")
        
    except Exception as e:
        print(f"\n❌ ERROR during Bible generation:")
        print(f"   {e}")
        print(f"\n💡 Common issues:")
        print(f"   • ANTHROPIC_API_KEY not set in .env")
        print(f"   • Missing dependencies (pip install PyPDF2 python-docx)")
        print(f"   • Case root path incorrect")
        return


if __name__ == '__main__':
    main()