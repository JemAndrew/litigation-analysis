#!/usr/bin/env python3
"""
Query Bible Utility - Examples of querying structured Bible

Demonstrates SQL-like capabilities without a database!

British English throughout.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional


class BibleQuery:
    """Query structured Bible data"""
    
    def __init__(self, case_id: str = "lismore_v_ph"):
        """Load structured Bible"""
        bible_path = Path(f"cases/{case_id}/case_bible_structured.json")
        
        if not bible_path.exists():
            raise FileNotFoundError(f"Structured Bible not found: {bible_path}")
        
        with open(bible_path, 'r', encoding='utf-8') as f:
            self.bible = json.load(f)
    
    # CLAIMS QUERIES
    
    def get_all_claims(self) -> List[Dict]:
        """Get all claims"""
        return self.bible.get('claims', [])
    
    def get_high_value_claims(self, min_gbp: float = 1_000_000) -> List[Dict]:
        """Get claims above a value threshold"""
        return [
            c for c in self.bible.get('claims', [])
            if c.get('quantum_gbp', 0) > min_gbp
        ]
    
    def get_claims_by_strength(self, strength: str) -> List[Dict]:
        """Get claims by strength (STRONG, MEDIUM, WEAK)"""
        return [
            c for c in self.bible.get('claims', [])
            if c.get('strength', '').upper() == strength.upper()
        ]
    
    def get_claims_above_win_probability(self, min_prob: float = 0.7) -> List[Dict]:
        """Get claims with win probability above threshold"""
        return [
            c for c in self.bible.get('claims', [])
            if c.get('win_probability', 0) >= min_prob
        ]
    
    # EVIDENCE QUERIES
    
    def get_evidence_for_claim(self, claim_id: int) -> List[Dict]:
        """Get all evidence for a specific claim"""
        claim = next(
            (c for c in self.bible.get('claims', []) if c['claim_id'] == claim_id),
            None
        )
        
        if not claim:
            return []
        
        evidence_ids = claim.get('evidence_ids', [])
        exhibits = self.bible.get('exhibits', {})
        
        return [exhibits[eid] for eid in evidence_ids if eid in exhibits]
    
    def get_smoking_guns(self) -> Dict[str, Dict]:
        """Get all smoking gun evidence"""
        return {
            k: v for k, v in self.bible.get('exhibits', {}).items()
            if v.get('category') == 'smoking_gun'
        }
    
    def get_exhibits_by_party(self, party: str) -> Dict[str, Dict]:
        """Get all exhibits from a party (claimant/respondent)"""
        return {
            k: v for k, v in self.bible.get('exhibits', {}).items()
            if v.get('party') == party.lower()
        }
    
    # QUANTUM QUERIES
    
    def get_total_quantum(self) -> float:
        """Get total quantum claimed"""
        return self.bible.get('quantum_breakdown', {}).get('total_gbp', 0)
    
    def get_quantum_by_head(self) -> List[Dict]:
        """Get quantum breakdown by head"""
        return self.bible.get('quantum_breakdown', {}).get('by_head', [])
    
    # STRATEGIC QUERIES
    
    def get_win_probability(self) -> float:
        """Get overall win probability"""
        return self.bible.get('strategic_assessment', {}).get('overall_win_probability', 0)
    
    def get_strongest_arguments(self) -> List[str]:
        """Get Lismore's strongest arguments"""
        return self.bible.get('strategic_assessment', {}).get('strongest_arguments', [])
    
    def get_settlement_range(self) -> Dict:
        """Get settlement range"""
        return self.bible.get('strategic_assessment', {}).get('settlement_range', {})
    
    # TIMELINE QUERIES
    
    def get_timeline(self) -> List[Dict]:
        """Get full timeline"""
        return self.bible.get('timeline', [])
    
    def get_events_after_date(self, date: str) -> List[Dict]:
        """Get events after a specific date (YYYY-MM-DD)"""
        return [
            e for e in self.bible.get('timeline', [])
            if e.get('date', '') > date
        ]
    
    # SUMMARY QUERIES
    
    def get_summary(self) -> Dict:
        """Get high-level summary"""
        claims = self.bible.get('claims', [])
        
        return {
            'case': self.bible.get('case_overview', {}).get('claimant', 'Unknown') + ' v ' + 
                   self.bible.get('case_overview', {}).get('respondent', 'Unknown'),
            'total_claims': len(claims),
            'total_quantum_gbp': self.get_total_quantum(),
            'high_value_claims': len(self.get_high_value_claims(1_000_000)),
            'strong_claims': len(self.get_claims_by_strength('STRONG')),
            'win_probability': self.get_win_probability(),
            'smoking_guns': len(self.get_smoking_guns()),
            'total_exhibits': len(self.bible.get('exhibits', {}))
        }


def main():
    """Demo queries"""
    
    print("="*70)
    print("CASE BIBLE QUERY EXAMPLES")
    print("="*70)
    
    try:
        bible = BibleQuery()
        
        # Summary
        print("\n📊 SUMMARY:")
        summary = bible.get_summary()
        for key, value in summary.items():
            print(f"   {key}: {value}")
        
        # High value claims
        print("\n💰 HIGH VALUE CLAIMS (> £1M):")
        high_value = bible.get_high_value_claims(1_000_000)
        for claim in high_value:
            print(f"   • Claim {claim['claim_id']}: {claim['title']}")
            print(f"     Quantum: £{claim.get('quantum_gbp', 0):,.0f}")
            print(f"     Win probability: {claim.get('win_probability', 0)*100:.0f}%")
        
        # Smoking guns
        print("\n🔥 SMOKING GUNS:")
        smoking_guns = bible.get_smoking_guns()
        for exhibit_id, exhibit in smoking_guns.items():
            print(f"   • {exhibit_id}: {exhibit['description']}")
        
        # Settlement range
        print("\n🤝 SETTLEMENT RANGE:")
        settlement = bible.get_settlement_range()
        for key, value in settlement.items():
            print(f"   {key}: £{value:,.0f}")
        
        print("\n✅ Query demo complete!")
        print("\nYou can now use these queries in your code!")
        
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        print("   Build the Bible first with: python build_bible.py")


if __name__ == '__main__':
    main()
