#!/usr/bin/env python3
"""
Bible Parser - Convert Plain Text Bible to Structured JSON

Takes the plain text Case Bible and extracts structured data.
This gives SQL-like query capabilities while maintaining caching benefits.

British English throughout.
"""

import re
import json
from typing import Dict, List, Optional, Any
from pathlib import Path


class BibleParser:
    """
    Parses plain text Case Bible into structured JSON
    
    Extracts:
    - Claims (with quantum, evidence, win probability)
    - Defences
    - Disputed facts
    - Exhibits
    - Timeline
    - Quantum breakdown
    - Strategic assessment
    """
    
    def __init__(self):
        """Initialise parser"""
        pass
    
    def parse_bible(self, bible_text: str) -> Dict[str, Any]:
        """
        Parse complete Bible into structured format
        
        Args:
            bible_text: Plain text Case Bible
        
        Returns:
            Structured dict
        """
        
        print("\n📊 Parsing Bible into structured format...")
        
        structured = {
            'case_overview': self._parse_case_overview(bible_text),
            'claims': self._parse_claims(bible_text),
            'defences': self._parse_defences(bible_text),
            'disputed_facts': self._parse_disputed_facts(bible_text),
            'exhibits': self._parse_exhibits(bible_text),
            'timeline': self._parse_timeline(bible_text),
            'quantum_breakdown': self._parse_quantum(bible_text),
            'strategic_assessment': self._parse_strategic_assessment(bible_text),
            'legal_authorities': self._parse_legal_authorities(bible_text)
        }
        
        print(f"   ✅ Parsed {len(structured['claims'])} claims")
        print(f"   ✅ Parsed {len(structured['defences'])} defences")
        print(f"   ✅ Parsed {len(structured['exhibits'])} exhibits")
        print(f"   ✅ Parsed {len(structured['timeline'])} timeline events")
        
        return structured
    
    def _parse_case_overview(self, text: str) -> Dict[str, Any]:
        """Parse case overview section"""
        
        overview = {}
        
        # Extract parties
        claimant_match = re.search(r'Claimant:\s*([^\n]+)', text, re.IGNORECASE)
        if claimant_match:
            overview['claimant'] = claimant_match.group(1).strip()
        
        respondent_match = re.search(r'Respondent:\s*([^\n]+)', text, re.IGNORECASE)
        if respondent_match:
            overview['respondent'] = respondent_match.group(1).strip()
        
        # Extract tribunal
        tribunal_match = re.search(r'Forum:\s*([^\n]+)', text, re.IGNORECASE)
        if tribunal_match:
            overview['tribunal'] = tribunal_match.group(1).strip()
        
        # Extract applicable law
        law_match = re.search(r'Applicable law:\s*([^\n]+)', text, re.IGNORECASE)
        if law_match:
            overview['applicable_law'] = law_match.group(1).strip()
        
        # Extract total claimed
        total_match = re.search(r'Total.*[Cc]laimed:\s*£?([\d,\.]+)\s*(?:million|M)?', text)
        if total_match:
            amount_str = total_match.group(1).replace(',', '')
            # Check if it's in millions
            if 'million' in total_match.group(0).lower() or 'M' in total_match.group(0):
                overview['total_claimed_gbp'] = float(amount_str) * 1_000_000
            else:
                overview['total_claimed_gbp'] = float(amount_str)
        
        return overview
    
    def _parse_claims(self, text: str) -> List[Dict[str, Any]]:
        """Parse all claims"""
        
        claims = []
        
        # Find claims section
        claims_section_match = re.search(
            r'2\.\s+LISMORE\'S CLAIMS.*?(?=\n═+\n\d+\.|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        
        if not claims_section_match:
            return claims
        
        claims_text = claims_section_match.group(0)
        
        # Find individual claims (CLAIM 1:, CLAIM 2:, etc.)
        claim_pattern = r'(?:^|\n)\*?\*?CLAIM\s+(\d+):\s*([^\n]+)(.*?)(?=\n\*?\*?CLAIM\s+\d+:|\n─+\n\*?\*?CLAIM|\Z)'
        
        for match in re.finditer(claim_pattern, claims_text, re.DOTALL | re.IGNORECASE):
            claim_num = int(match.group(1))
            claim_title = match.group(2).strip()
            claim_body = match.group(3)
            
            claim = {
                'claim_id': claim_num,
                'claim_number': claim_num,
                'title': claim_title
            }
            
            # Extract legal basis
            legal_basis_match = re.search(r'Legal Basis:\s*([^\n]+)', claim_body)
            if legal_basis_match:
                claim['legal_basis'] = legal_basis_match.group(1).strip()
            
            # Extract SPA clause
            clause_match = re.search(r'Contractual Provision:\s*([^\n]+)|SPA Clause:\s*([^\n]+)', claim_body)
            if clause_match:
                claim['spa_clause'] = (clause_match.group(1) or clause_match.group(2)).strip()
            
            # Extract quantum
            quantum_match = re.search(r'Quantum Claimed:\s*£?([\d,\.]+)\s*(?:million|M)?', claim_body)
            if quantum_match:
                amount_str = quantum_match.group(1).replace(',', '')
                if 'million' in quantum_match.group(0).lower() or 'M' in quantum_match.group(0):
                    claim['quantum_gbp'] = float(amount_str) * 1_000_000
                else:
                    claim['quantum_gbp'] = float(amount_str)
            
            # Extract evidence IDs
            evidence_section = re.search(
                r'Key Evidence[^\n]*:\s*(.*?)(?=\n\n[A-Z]|\nPH\'s Defence|\n\*\*|$)',
                claim_body,
                re.DOTALL
            )
            if evidence_section:
                evidence_text = evidence_section.group(1)
                # Find all C-XXX, R1-XXX style IDs
                evidence_ids = re.findall(r'\b([CR]\d?-\d+)\b', evidence_text)
                claim['evidence_ids'] = list(set(evidence_ids))  # Remove duplicates
            
            # Extract PH's defence
            defence_match = re.search(r'PH\'s Defence[^\n]*:\s*([^\n]+)', claim_body)
            if defence_match:
                claim['ph_defence'] = defence_match.group(1).strip()
            
            # Extract win probability
            prob_match = re.search(r'Win probability[^\n]*:\s*([\d\.]+)%', claim_body, re.IGNORECASE)
            if prob_match:
                claim['win_probability'] = float(prob_match.group(1)) / 100
            
            # Extract strength assessment
            strength_match = re.search(r'Evidence strength:\s*([A-Z]+)', claim_body, re.IGNORECASE)
            if strength_match:
                claim['strength'] = strength_match.group(1).upper()
            
            # Extract key risks
            risks_section = re.search(r'Key risk factors:\s*(.*?)(?=\n\n|\n─|\Z)', claim_body, re.DOTALL)
            if risks_section:
                risks_text = risks_section.group(1)
                # Split by bullet points or newlines
                risks = [r.strip(' •-') for r in risks_text.split('\n') if r.strip(' •-')]
                claim['key_risks'] = risks
            
            claims.append(claim)
        
        return claims
    
    def _parse_defences(self, text: str) -> List[Dict[str, Any]]:
        """Parse PH's defences"""
        
        defences = []
        
        # Find defences section
        defences_section_match = re.search(
            r'3\.\s+PH\'S DEFENCES.*?(?=\n═+\n\d+\.|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        
        if not defences_section_match:
            return defences
        
        defences_text = defences_section_match.group(0)
        
        # Find individual defences
        defence_pattern = r'(?:^|\n)\*?\*?DEFENCE\s+(\d+):\s*([^\n]+)(.*?)(?=\n\*?\*?DEFENCE\s+\d+:|\n\*?\*?COUNTERCLAIM|\Z)'
        
        for match in re.finditer(defence_pattern, defences_text, re.DOTALL | re.IGNORECASE):
            defence_num = int(match.group(1))
            defence_title = match.group(2).strip()
            defence_body = match.group(3)
            
            defence = {
                'defence_id': defence_num,
                'title': defence_title
            }
            
            # Extract PH's argument
            arg_match = re.search(r'PH\'s Position:\s*([^\n]+)', defence_body)
            if arg_match:
                defence['ph_argument'] = arg_match.group(1).strip()
            
            # Extract legal basis
            legal_match = re.search(r'Legal Basis:\s*([^\n]+)', defence_body)
            if legal_match:
                defence['legal_basis'] = legal_match.group(1).strip()
            
            # Extract evidence
            evidence_section = re.search(
                r'Evidence[^\n]*:\s*(.*?)(?=\n\n[A-Z]|\nLismore\'s Rebuttal|\Z)',
                defence_body,
                re.DOTALL
            )
            if evidence_section:
                evidence_text = evidence_section.group(1)
                evidence_ids = re.findall(r'\b([CR]\d?-\d+)\b', evidence_text)
                defence['evidence_ids'] = list(set(evidence_ids))
            
            # Extract Lismore's rebuttal
            rebuttal_match = re.search(r'Lismore\'s Rebuttal:\s*([^\n]+)', defence_body)
            if rebuttal_match:
                defence['lismore_rebuttal'] = rebuttal_match.group(1).strip()
            
            # Extract weakness assessment
            weakness_match = re.search(r'Weakness[^\n]*:\s*([A-Z]+)', defence_body, re.IGNORECASE)
            if weakness_match:
                defence['weakness'] = weakness_match.group(1).upper()
            
            defences.append(defence)
        
        return defences
    
    def _parse_disputed_facts(self, text: str) -> List[Dict[str, Any]]:
        """Parse disputed facts"""
        
        facts = []
        
        # Find disputed facts section
        facts_section_match = re.search(
            r'4\.\s+KEY DISPUTED FACTS.*?(?=\n═+\n\d+\.|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        
        if not facts_section_match:
            return facts
        
        facts_text = facts_section_match.group(0)
        
        # Find individual facts
        fact_pattern = r'(?:^|\n)\*?\*?DISPUTED FACT\s+(\d+):\s*([^\n]+)(.*?)(?=\n\*?\*?DISPUTED FACT\s+\d+:|\Z)'
        
        for match in re.finditer(fact_pattern, facts_text, re.DOTALL | re.IGNORECASE):
            fact_num = int(match.group(1))
            fact_issue = match.group(2).strip()
            fact_body = match.group(3)
            
            fact = {
                'fact_id': fact_num,
                'issue': fact_issue
            }
            
            # Extract positions
            lismore_match = re.search(r'Lismore\'s Position:\s*([^\n]+)', fact_body)
            if lismore_match:
                fact['lismore_position'] = lismore_match.group(1).strip()
            
            ph_match = re.search(r'PH\'s Position:\s*([^\n]+)', fact_body)
            if ph_match:
                fact['ph_position'] = ph_match.group(1).strip()
            
            # Extract evidence
            lismore_ev_match = re.search(r'Evidence Supporting Lismore:\s*(.*?)(?=\n\n|Evidence Supporting PH|\Z)', fact_body, re.DOTALL)
            if lismore_ev_match:
                ev_text = lismore_ev_match.group(1)
                fact['lismore_evidence'] = re.findall(r'\b([CR]\d?-\d+)\b', ev_text)
            
            ph_ev_match = re.search(r'Evidence Supporting PH:\s*(.*?)(?=\n\n|Assessment:|\Z)', fact_body, re.DOTALL)
            if ph_ev_match:
                ev_text = ph_ev_match.group(1)
                fact['ph_evidence'] = re.findall(r'\b([CR]\d?-\d+)\b', ev_text)
            
            # Extract assessment
            assess_match = re.search(r'Assessment:\s*([^\n]+)', fact_body)
            if assess_match:
                fact['assessment'] = assess_match.group(1).strip()
            
            facts.append(fact)
        
        return facts
    
    def _parse_exhibits(self, text: str) -> Dict[str, Dict[str, Any]]:
        """Parse exhibit map"""
        
        exhibits = {}
        
        # Find exhibit map section
        exhibit_section_match = re.search(
            r'6\.\s+EXHIBIT MAP.*?(?=\n═+\n\d+\.|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        
        if not exhibit_section_match:
            return exhibits
        
        exhibit_text = exhibit_section_match.group(0)
        
        # Find all exhibit references (C-XXX:, R1-XXX:)
        exhibit_pattern = r'\n\s*[•\-]?\s*([CR]\d?-\d+):\s*([^\n]+)'
        
        for match in re.finditer(exhibit_pattern, exhibit_text):
            exhibit_id = match.group(1)
            description = match.group(2).strip()
            
            # Determine category based on context around it
            context_start = max(0, match.start() - 200)
            context = exhibit_text[context_start:match.start()].lower()
            
            category = 'evidence'
            if 'smoking gun' in context:
                category = 'smoking_gun'
            elif 'warrant' in context or 'disclosure' in context:
                category = 'contract'
            elif 'financial' in context:
                category = 'financial'
            elif 'communication' in context or 'email' in context or 'letter' in context:
                category = 'correspondence'
            
            exhibits[exhibit_id] = {
                'exhibit_id': exhibit_id,
                'description': description,
                'category': category,
                'party': 'claimant' if exhibit_id.startswith('C') else 'respondent'
            }
        
        return exhibits
    
    def _parse_timeline(self, text: str) -> List[Dict[str, Any]]:
        """Parse timeline"""
        
        timeline = []
        
        # Find timeline section
        timeline_section_match = re.search(
            r'7\.\s+TIMELINE.*?(?=\n═+\n\d+\.|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        
        if not timeline_section_match:
            return timeline
        
        timeline_text = timeline_section_match.group(0)
        
        # Find timeline entries (YYYY-MM-DD format)
        timeline_pattern = r'(\d{4}-\d{2}-\d{2})\s*[–-]\s*([^\n]+)\nSource:\s*([^\n]+)(?:\nSignificance:\s*([^\n]+))?'
        
        for match in re.finditer(timeline_pattern, timeline_text):
            event = {
                'date': match.group(1),
                'event': match.group(2).strip(),
                'source': match.group(3).strip()
            }
            
            if match.group(4):
                event['significance'] = match.group(4).strip()
            
            timeline.append(event)
        
        return sorted(timeline, key=lambda x: x['date'])
    
    def _parse_quantum(self, text: str) -> Dict[str, Any]:
        """Parse quantum breakdown"""
        
        quantum = {
            'total_gbp': 0,
            'by_head': []
        }
        
        # Find quantum section
        quantum_section_match = re.search(
            r'8\.\s+QUANTUM.*?(?=\n═+\n\d+\.|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        
        if not quantum_section_match:
            return quantum
        
        quantum_text = quantum_section_match.group(0)
        
        # Extract total
        total_match = re.search(r'Total[^\n]*:\s*£?([\d,\.]+)\s*(?:million|M)?', quantum_text)
        if total_match:
            amount_str = total_match.group(1).replace(',', '')
            if 'million' in total_match.group(0).lower() or 'M' in total_match.group(0):
                quantum['total_gbp'] = float(amount_str) * 1_000_000
            else:
                quantum['total_gbp'] = float(amount_str)
        
        # Extract heads
        head_pattern = r'\*?\*?Head\s+\d+:\s*([^\n]+)\nAmount:\s*£?([\d,\.]+)\s*(?:million|M)?'
        
        for match in re.finditer(head_pattern, quantum_text, re.IGNORECASE):
            head_name = match.group(1).strip()
            amount_str = match.group(2).replace(',', '')
            
            if 'million' in match.group(0).lower() or 'M' in match.group(0):
                amount = float(amount_str) * 1_000_000
            else:
                amount = float(amount_str)
            
            quantum['by_head'].append({
                'head': head_name,
                'amount_gbp': amount
            })
        
        return quantum
    
    def _parse_strategic_assessment(self, text: str) -> Dict[str, Any]:
        """Parse strategic assessment"""
        
        assessment = {}
        
        # Find strategic assessment section
        strat_section_match = re.search(
            r'12\.\s+STRATEGIC ASSESSMENT.*?(?=\n═+\n\d+\.|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        
        if not strat_section_match:
            return assessment
        
        strat_text = strat_section_match.group(0)
        
        # Extract overall win probability
        prob_match = re.search(r'(?:Overall\s+)?Win Probability:\s*([\d\.]+)%', strat_text, re.IGNORECASE)
        if prob_match:
            assessment['overall_win_probability'] = float(prob_match.group(1)) / 100
        
        # Extract strongest arguments
        args_section = re.search(
            r'Lismore\'s Strongest Arguments:.*?\n(.*?)(?=\n\n[A-Z]|PH\'s Weakest|\Z)',
            strat_text,
            re.DOTALL | re.IGNORECASE
        )
        if args_section:
            args_text = args_section.group(1)
            arguments = [a.strip(' •\-\d.') for a in args_text.split('\n') if a.strip(' •\-\d.')]
            assessment['strongest_arguments'] = arguments
        
        # Extract key risks
        risks_section = re.search(
            r'Lismore\'s Vulnerabilities:.*?\n(.*?)(?=\n\n[A-Z]|\Z)',
            strat_text,
            re.DOTALL | re.IGNORECASE
        )
        if risks_section:
            risks_text = risks_section.group(1)
            risks = [r.strip(' •\-\d.') for r in risks_text.split('\n') if r.strip(' •\-\d.')]
            assessment['key_risks'] = risks
        
        # Extract settlement range
        settlement_section = re.search(
            r'Settlement Range:(.*?)(?=\n\n[A-Z]|\Z)',
            strat_text,
            re.DOTALL | re.IGNORECASE
        )
        if settlement_section:
            settlement_text = settlement_section.group(1)
            
            settlement = {}
            
            min_match = re.search(r'minimum.*?£?([\d,\.]+)\s*(?:million|M)?', settlement_text, re.IGNORECASE)
            if min_match:
                amount_str = min_match.group(1).replace(',', '')
                if 'million' in min_match.group(0).lower() or 'M' in min_match.group(0):
                    settlement['lismore_minimum_gbp'] = float(amount_str) * 1_000_000
                else:
                    settlement['lismore_minimum_gbp'] = float(amount_str)
            
            fair_match = re.search(r'fair.*?£?([\d,\.]+)\s*(?:million|M)?', settlement_text, re.IGNORECASE)
            if fair_match:
                amount_str = fair_match.group(1).replace(',', '')
                if 'million' in fair_match.group(0).lower() or 'M' in fair_match.group(0):
                    settlement['fair_value_gbp'] = float(amount_str) * 1_000_000
                else:
                    settlement['fair_value_gbp'] = float(amount_str)
            
            assessment['settlement_range'] = settlement
        
        return assessment
    
    def _parse_legal_authorities(self, text: str) -> Dict[str, Any]:
        """Parse legal authorities section"""
        
        authorities = {
            'total_count': 0,
            'by_bundle': {}
        }
        
        # Find legal authorities section
        legal_section_match = re.search(
            r'14\.\s+LEGAL AUTHORITIES.*?(?=\n═+\n\d+\.|$)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        
        if not legal_section_match:
            return authorities
        
        legal_text = legal_section_match.group(0)
        
        # Extract total count
        count_match = re.search(r'approximately\s+(\d+)\s+(?:case\s+)?authorit', legal_text, re.IGNORECASE)
        if count_match:
            authorities['total_count'] = int(count_match.group(1))
        
        # Find bundle sections
        bundle_pattern = r'(Bundle\s+[A-Z\d]+|[A-Z]+LA).*?contains[^\n]*:.*?\n(.*?)(?=\n\n[A-Z]|\Z)'
        
        for match in re.finditer(bundle_pattern, legal_text, re.DOTALL | re.IGNORECASE):
            bundle_name = match.group(1).strip()
            bundle_content = match.group(2)
            
            # Extract file names
            files = re.findall(r'[•\-]\s*([^\n]+)', bundle_content)
            authorities['by_bundle'][bundle_name] = [f.strip() for f in files if f.strip()]
        
        return authorities


def main():
    """Test the parser"""
    
    # Test on a sample Bible file
    bible_path = Path('cases/lismore_v_ph/case_bible.txt')
    
    if not bible_path.exists():
        print(f"❌ Bible not found at: {bible_path}")
        print("   Build the Bible first with: python build_bible.py")
        return
    
    # Load Bible
    bible_text = bible_path.read_text(encoding='utf-8')
    
    # Parse
    parser = BibleParser()
    structured = parser.parse_bible(bible_text)
    
    # Save structured version
    structured_path = bible_path.parent / 'case_bible_structured.json'
    with open(structured_path, 'w', encoding='utf-8') as f:
        json.dump(structured, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Structured Bible saved to: {structured_path}")
    
    # Show summary
    print("\n" + "="*70)
    print("STRUCTURED DATA SUMMARY")
    print("="*70)
    print(f"\nClaims: {len(structured['claims'])}")
    print(f"Defences: {len(structured['defences'])}")
    print(f"Disputed Facts: {len(structured['disputed_facts'])}")
    print(f"Exhibits: {len(structured['exhibits'])}")
    print(f"Timeline Events: {len(structured['timeline'])}")
    
    if structured.get('quantum_breakdown', {}).get('total_gbp'):
        print(f"Total Quantum: £{structured['quantum_breakdown']['total_gbp']:,.0f}")
    
    if structured.get('strategic_assessment', {}).get('overall_win_probability'):
        print(f"Win Probability: {structured['strategic_assessment']['overall_win_probability']*100:.0f}%")


if __name__ == '__main__':
    main()