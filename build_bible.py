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
║  One-time cost: £60-80                                            ║
║  Time required: 30-60 minutes                                     ║
║  Future query cost: £0.15 (95% savings with caching!)            ║
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
    print(f"\nThis will:")
    print(f"  • Analyse 74 folders")
    print(f"  • Extract ~50-100 master documents")
    print(f"  • Generate comprehensive Case Bible")
    print(f"  • Cost approximately £60-80")
    
    confirm = input("\nProceed? (y/n): ")
    if confirm.lower() != 'y':
        print("\n❌ Cancelled")
        return
    
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
    print("✅ CASE BIBLE BUILD COMPLETE!")
    print("="*70)
    print(f"\n📄 Bible saved to: {bible_path}")
    print(f"\n🚀 NEXT STEPS:")
    print(f"  1. Review the Case Bible at: {bible_path}")
    print(f"  2. Use chat.py to ask questions (Bible will be cached)")
    print(f"  3. Each query will cost ~£0.15 instead of £2-5!")
    print(f"\n💡 The Bible is the foundation - everything builds on it!")


if __name__ == '__main__':
    main()
