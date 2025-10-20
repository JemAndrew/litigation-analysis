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
from typing import Dict

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
    
    def get_bible_generation_prompt(
        self,
        case_name: str,
        claimant: str,
        respondent: str,
        tribunal: str,
        pleadings: Dict[str, str],
        indices: Dict[str, str],
        witness_statements: str = "",
        late_disclosure_context: str = "",
        tribunal_rulings: str = ""
    ) -> str:
        """
        Build the complete Bible generation prompt
        
        Args:
            case_name: Full case name
            claimant: Claimant name
            respondent: Respondent name
            tribunal: Tribunal name
            pleadings: Dict with 'claim', 'defence', 'reply', etc.
            indices: Dict with 'claimant', 'respondent' indices
            witness_statements: Extracted trial witness statements
            late_disclosure_context: Context about late disclosure
            tribunal_rulings: Procedural orders/rulings
        
        Returns:
            Complete prompt for Bible generation
        """
        
        prompt = f"""You are building a **Case Bible** for the litigation case: **{case_name}**.

⚖️ CASE CONTEXT:
- Claimant: {claimant}
- Respondent: {respondent}
- Tribunal: {tribunal}

═══════════════════════════════════════════════════════════════════════
CRITICAL INSTRUCTIONS
═══════════════════════════════════════════════════════════════════════

1. XML STRUCTURED OUTPUT (for claims, defences, quantum):

Example claim structure:
<claim id="1">
  <legal_basis>Breach of Warranty 12.3</legal_basis>
  <factual_allegation>PH failed to disclose £2.3M penalties [C-045]</factual_allegation>
  <quantum_gbp>2300000</quantum_gbp>
  <evidence>
    <smoking_gun id="C-045">Email dated 28 March 2024 proves PH knew about penalties</smoking_gun>
    <smoking_gun id="C-087">Board minutes confirm decision to conceal</smoking_gun>
  </evidence>
  <ph_defence>PH argues penalties were immaterial</ph_defence>
  <lismore_rebuttal>Immateriality fails - £2.3M is 15% of purchase price. PH's materiality argument fails.</lismore_rebuttal>
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
9. LATE DISCLOSURE ANALYSIS (Why did PH disclose documents late?)
10. LEGAL FRAMEWORK (Applicable law, key precedents)
11. PROCEDURAL HISTORY & KEY RULINGS
12. STRATEGIC ASSESSMENT (Win probability, strongest arguments, risks)
13. WITNESS & EXPERT EVIDENCE (Summary of statements with credibility)
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
        
        # Add Trial Witness Statements
        if witness_statements:
            prompt += f"""
───────────────────────────────────────────────────────────────────────
TRIAL WITNESS STATEMENTS (21 KEY WITNESSES)
───────────────────────────────────────────────────────────────────────

These witnesses TESTIFIED at trial. Their credibility is CRITICAL.

For each witness statement:
- Identify KEY FACTS claimed by the witness
- Note CONTRADICTIONS with documents (smoking guns for cross-exam)
- Assess CREDIBILITY (0-10 score)
- Identify CROSS-EXAMINATION ATTACK POINTS

FORMAT FOR SECTION 13:

**WITNESS: [Name]**
- Role: [Position at PH/Lismore]
- Statement dated: [Date]
- Key facts claimed:
  1. [Fact 1 with citation to para]
  2. [Fact 2 with citation to para]
- Contradictions with documents:
  • Says "[Quote]" but [DOC_ID] proves [Opposite]
  • Claims "didn't know X" but email [DOC_ID] shows knew on [Date]
- Credibility: [X]/10
- Cross-exam attack points:
  1. "You stated in para X that... but DOC_Y proves..."
  2. "How do you explain the contradiction between your statement and DOC_Z?"

{witness_statements[:150000]}

[Witness statements truncated if > 150K chars]

"""
        
        # Add Late Disclosure Context
        if late_disclosure_context:
            prompt += f"""
───────────────────────────────────────────────────────────────────────
LATE DISCLOSURE (15 September 2025 - Critical Context)
───────────────────────────────────────────────────────────────────────

⚠️ CRITICAL: PH disclosed documents on 15 September 2025.

Analyse for SECTION 9:
- When was this disclosure (relative to Defence filing)?
- Why was disclosure so late?
- What does timing suggest about PH's conduct?
- What are the strategic implications?
- Does late timing indicate spoliation/concealment?

{late_disclosure_context[:50000]}

"""
        
        # Add Tribunal Rulings
        if tribunal_rulings:
            prompt += f"""
───────────────────────────────────────────────────────────────────────
TRIBUNAL RULINGS & PROCEDURAL ORDERS
───────────────────────────────────────────────────────────────────────

{tribunal_rulings[:50000]}

"""
        
        # Final instructions
        prompt += """
───────────────────────────────────────────────────────────────────────
OUTPUT REQUIREMENTS
───────────────────────────────────────────────────────────────────────

- Write in clear, professional British English
- Be comprehensive but concise
- Use bullet points and structured formatting
- Target length: 40-60 pages total
- This will be read by Claude for EVERY future query, so include everything essential
- DO NOT include irrelevant details that won't help future analysis

BEGIN THE CASE BIBLE NOW:"""

        return prompt


# Singleton instance
_prompts = BiblePrompts()

# Module-level functions for backward compatibility
def get_system_prompt() -> str:
    """Get system prompt"""
    return _prompts.get_system_prompt()

def get_bible_generation_prompt(
    case_name: str,
    claimant: str,
    respondent: str,
    tribunal: str,
    pleadings: Dict[str, str],
    indices: Dict[str, str],
    witness_statements: str = "",
    late_disclosure_context: str = "",
    tribunal_rulings: str = ""
) -> str:
    """Get Bible generation prompt"""
    return _prompts.get_bible_generation_prompt(
        case_name=case_name,
        claimant=claimant,
        respondent=respondent,
        tribunal=tribunal,
        pleadings=pleadings,
        indices=indices,
        witness_statements=witness_statements,
        late_disclosure_context=late_disclosure_context,
        tribunal_rulings=tribunal_rulings
    )