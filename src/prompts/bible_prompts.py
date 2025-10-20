#!/usr/bin/env python3
"""
Bible Prompts - Enhanced with Claude Best Practices

Uses Claude's advanced capabilities:
- Strong role prompting (Senior Litigation Barrister)
- XML tags for structured output
- Mandatory citations for every claim
- Prefilling for format consistency
- Chain of thought instructions

British English throughout.
"""

class BiblePrompts:
    """
    Generates prompts for Case Bible building
    
    Enhanced with Claude best practices:
    - Clear role definition
    - XML structured output
    - Citation requirements
    - Thinking instructions
    """
    
    def __init__(self):
        """Initialise prompts"""
        pass
    
    def get_system_prompt(self) -> str:
        """
        Get enhanced system prompt with strong role definition
        
        Returns:
            System prompt optimised for litigation analysis
        """
        
        return """You are a Senior Litigation Barrister with 20+ years of experience in international commercial arbitration. You specialise in:
- Share purchase agreement disputes
- Warranty and indemnity claims
- Forensic document analysis
- LCIA arbitration procedure

CRITICAL CAPABILITIES YOU MUST USE:

1. EXTENDED THINKING: Before responding, use your extended thinking to:
   - Analyse the structure of pleadings
   - Identify factual patterns across documents
   - Assess strength of evidence chains
   - Evaluate legal arguments

2. MANDATORY CITATIONS: Every factual claim MUST cite source documents:
   - Format: [DOC_ID] or [DOC_ID, para X]
   - Example: "PH failed to disclose penalties [C-045, para 3]"
   - Never make factual assertions without documentary support

3. XML STRUCTURED OUTPUT: Use XML tags to structure information:
   - <claim id="X">...</claim>
   - <evidence id="DOC_ID">...</evidence>
   - <quantum_gbp>...</quantum_gbp>
   This enables programmatic parsing while maintaining readability.

4. PARTISAN ANALYSIS: You represent the CLAIMANT (Lismore). Every analysis should:
   - Favour Lismore's interpretation
   - Attack PH's defences aggressively
   - Find smoking guns that destroy PH's case
   - Build Lismore's strongest possible arguments

5. FORENSIC PRECISION:
   - Extract exact dates, amounts, clause numbers
   - Note contradictions between documents
   - Identify suspicious timing (e.g., late disclosure)
   - Flag potential fraud/concealment indicators

Your goal: Build a Case Bible that gives Lismore's legal team TOTAL COMMAND of the case.

Use British English exclusively: analyse, favour, colour, organisation, etc."""
    
    def generate_bible_prompt(
        self,
        pleadings: dict,
        indices: dict,
        late_disclosure_context: str,
        tribunal_rulings: str
    ) -> str:
        """
        Generate enhanced Bible building prompt
        
        Args:
            pleadings: Dict with 'claim', 'defence', 'reply', 'rejoinder'
            indices: Dict with exhibit indices
            late_disclosure_context: Late disclosure sampling
            tribunal_rulings: Tribunal rulings text
        
        Returns:
            Complete prompt with XML structure requirements
        """
        
        prompt = f"""═══════════════════════════════════════════════════════════════════════
CASE BIBLE GENERATION - LISMORE CAPITAL v PROCESS HOLDINGS
═══════════════════════════════════════════════════════════════════════

⚖️ YOU ARE ACTING FOR LISMORE CAPITAL AGAINST PROCESS HOLDINGS (PH)

Your mission: Extract EVERY piece of information from the pleadings and documents below, then build a comprehensive Case Bible that gives Lismore's legal team complete mastery of this case.

═══════════════════════════════════════════════════════════════════════
INSTRUCTIONS - READ CAREFULLY
═══════════════════════════════════════════════════════════════════════

OUTPUT FORMAT REQUIREMENTS:

1. Use XML tags for ALL structured data (claims, evidence, quantum):

<claim id="1">
  <title>Breach of Warranty 12.3 (Disclosure of Liabilities)</title>
  <legal_basis>Breach of warranty under SPA Clause 12.3</legal_basis>
  <quantum_gbp>2300000</quantum_gbp>
  <facts>
    <fact>PH warranted complete disclosure of liabilities [C-001, Warranty Schedule para 12.3]</fact>
    <fact>PH failed to disclose £2.3M supplier penalties [C-045, para 3]</fact>
    <fact>PH knew about penalties pre-SPA [C-091, Board Minutes dated 15 March 2024]</fact>
  </facts>
  <evidence>
    <smoking_gun id="C-045">Email from PH CFO discussing "withholding bad news from buyer"</smoking_gun>
    <smoking_gun id="C-091">Board minutes proving PH discussed penalties 2 weeks before SPA</smoking_gun>
  </evidence>
  <ph_defence>PH claims penalties were "immaterial" under SPA definition</ph_defence>
  <lismore_rebuttal>£2.3M is 46% of target EBITDA - clearly material. PH's materiality argument fails.</lismore_rebuttal>
  <win_probability>0.75</win_probability>
  <strength>STRONG</strength>
  <key_risks>
    <risk>PH may argue oral disclosure (uncorroborated)</risk>
  </key_risks>
</claim>

2. MANDATORY CITATIONS:
   - Every fact MUST cite source: [DOC_ID] or [DOC_ID, para/page X]
   - If you cannot cite a source, DO NOT include the fact
   - Prefer specific citations: [C-045, para 3] over generic [C-045]

3. THINKING PROCESS (use your extended thinking):
   - First, read all pleadings carefully
   - Then, map exhibits to claims using the indices
   - Then, identify contradictions and smoking guns
   - Then, assess strength of each claim
   - Finally, build strategic recommendations

4. PARTISAN ANALYSIS:
   - You represent LISMORE, not a neutral arbitrator
   - Frame everything to favour Lismore's case
   - Attack PH's defences mercilessly
   - Highlight PH's credibility problems (e.g., late disclosure)

5. FORENSIC PRECISION:
   - Extract exact amounts: £2,300,000 (not "approximately £2M")
   - Extract exact dates: 28 March 2024 (not "March 2024")
   - Extract exact clause references: Warranty 12.3 (not "the warranty")

═══════════════════════════════════════════════════════════════════════
REQUIRED SECTIONS (Use this exact structure)
═══════════════════════════════════════════════════════════════════════

Generate a Case Bible with these sections:

1. CASE OVERVIEW
2. LISMORE'S CLAIMS (Extract EVERY claim with XML tags)
3. PH'S DEFENCES & COUNTERCLAIMS (Extract with XML tags)
4. KEY DISPUTED FACTS (10-20 critical factual disputes)
5. THE CONTRACT - KEY PROVISIONS (SPA clauses that matter)
6. EXHIBIT MAP (Index of ALL key exhibits by category)
7. TIMELINE OF KEY EVENTS (Chronological, with sources)
8. QUANTUM BREAKDOWN (With XML tags for each head)
9. LATE DISCLOSURE ANALYSIS (Why did PH disclose 1,612 docs on 15 Sep 2025?)
10. LEGAL FRAMEWORK (Applicable law, key precedents)
11. PROCEDURAL HISTORY & KEY RULINGS
12. STRATEGIC ASSESSMENT (Win probability, strongest arguments, risks)
13. WITNESS & EXPERT EVIDENCE (Summary of statements)
14. LEGAL AUTHORITIES REFERENCED (Note existence, don't extract)

═══════════════════════════════════════════════════════════════════════
SOURCE DOCUMENTS
═══════════════════════════════════════════════════════════════════════

"""
        
        # Add Statement of Claim
        if 'claim' in pleadings:
            prompt += f"""
───────────────────────────────────────────────────────────────────────
DOCUMENT: LISMORE'S STATEMENT OF CLAIM
───────────────────────────────────────────────────────────────────────

{pleadings['claim'][:100000]}  

[Claim truncated if > 100K chars]

"""
        
        # Add Statement of Defence
        if 'defence' in pleadings:
            prompt += f"""
───────────────────────────────────────────────────────────────────────
DOCUMENT: PH'S STATEMENT OF DEFENCE
───────────────────────────────────────────────────────────────────────

{pleadings['defence'][:100000]}

[Defence truncated if > 100K chars]

"""
        
        # Add Reply/Rejoinder
        if 'reply' in pleadings:
            prompt += f"""
───────────────────────────────────────────────────────────────────────
DOCUMENT: LISMORE'S REPLY & REJOINDER
───────────────────────────────────────────────────────────────────────

{pleadings.get('reply', '')[:100000]}

[Reply truncated if > 100K chars]

"""
        
        # Add Exhibit Indices
        if indices:
            prompt += f"""
───────────────────────────────────────────────────────────────────────
EXHIBIT INDICES (Critical for mapping exhibits to claims)
───────────────────────────────────────────────────────────────────────

"""
            for key, index_text in indices.items():
                prompt += f"\n[{key.upper()} INDEX]\n{index_text[:50000]}\n"
        
        # Add Late Disclosure Context
        prompt += f"""
───────────────────────────────────────────────────────────────────────
LATE DISCLOSURE (15 September 2025 - 1,612 documents)
───────────────────────────────────────────────────────────────────────

⚠️ CRITICAL: PH disclosed 1,612 documents on 15 September 2025.
This is 11 months AFTER filing their Defence (15 October 2024).

Analyse WHY this disclosure was so late. What are the strategic implications?

{late_disclosure_context}

"""
        
        # Add Tribunal Rulings
        if tribunal_rulings:
            prompt += f"""
───────────────────────────────────────────────────────────────────────
TRIBUNAL RULINGS
───────────────────────────────────────────────────────────────────────

{tribunal_rulings}

"""
        
        # Final instructions
        prompt += """
═══════════════════════════════════════════════════════════════════════
BEGIN CASE BIBLE GENERATION
═══════════════════════════════════════════════════════════════════════

Using your extended thinking, analyse all documents above and generate the complete Case Bible following the structure and XML requirements specified.

Remember:
✅ Use XML tags for structured data
✅ Cite sources for EVERY fact [DOC_ID, location]
✅ Favour Lismore's position (you represent them!)
✅ Be forensically precise (exact dates, amounts, clauses)
✅ Identify smoking guns aggressively
✅ Attack PH's credibility

Begin with: "═══════════════════════════════════════════════════════════════════════"
"""
        
        return prompt


def main():
    """Test the enhanced prompts"""
    
    prompts = BiblePrompts()
    
    print("="*70)
    print("ENHANCED BIBLE PROMPTS")
    print("="*70)
    
    print("\nSYSTEM PROMPT:")
    print(prompts.get_system_prompt()[:500] + "...")
    
    print("\n✅ Enhanced with:")
    print("  • Strong role definition (Senior Barrister)")
    print("  • XML tag requirements")
    print("  • Mandatory citation rules")
    print("  • Extended thinking instructions")
    print("  • Partisan framing (pro-Lismore)")


if __name__ == '__main__':
    main()