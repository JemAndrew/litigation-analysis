#!/usr/bin/env python3
"""
Universal Forensic Prompts - Work for ANY litigation case
These prompts adapt dynamically based on case context injection

British English throughout
"""


# Add src to path for imports
import sys
from pathlib import Path
src_dir = Path(__file__).parent.parent if "src" in str(Path(__file__).parent) else Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
    sys.path.insert(0, str(src_dir.parent))

from typing import Dict, List


class UniversalForensicPrompts:
    """
    Prompt templates that work for ANY case through context injection
    
    Key innovation: Instead of case-specific prompts, we inject:
    - Claimant name (dynamic)
    - Respondent name (dynamic)  
    - Case allegations (dynamic)
    - Retrieved documents (dynamic)
    
    Result: One prompt codebase scales to infinite cases
    """
    
    @staticmethod
    def forensic_analysis(
        query: str,
        case_context: Dict,
        retrieved_docs: List[Dict],
        knowledge_graph_context: str = ""
    ) -> str:
        """
        Universal forensic analysis prompt
        
        Args:
            query: Lawyer's question
            case_context: {case_name, claimant, respondent, tribunal, allegations}
            retrieved_docs: Documents from RAG retrieval
            knowledge_graph_context: Previously found insights
            
        Returns:
            Forensic prompt ready for Claude
        """
        
        # Format retrieved documents
        docs_text = "\n\n" + "="*70 + "\n\n"
        for i, doc in enumerate(retrieved_docs, 1):
            docs_text += f"DOCUMENT {i}: [{doc['metadata']['filename']}]\n"
            docs_text += f"{doc['text']}\n"
            docs_text += "\n" + "="*70 + "\n\n"
        
        # Add knowledge graph context if available
        kg_section = ""
        if knowledge_graph_context:
            kg_section = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 PREVIOUSLY IDENTIFIED INSIGHTS (Cumulative Knowledge)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{knowledge_graph_context}

You can reference these prior findings in your analysis.

"""
        
        return f"""You are a forensic litigation analyst acting for {case_context['claimant']} in {case_context['case_name']}.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚖️  CASE CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Case Name: {case_context['case_name']}
Tribunal: {case_context['tribunal']}

YOUR CLIENT (Claimant): {case_context['claimant'].upper()}
OPPONENT (Respondent): {case_context['respondent'].upper()}

Key Allegations:
{case_context['allegations']}

⚠️  YOU ARE ACTING FOR {case_context['claimant'].upper()} - Your goal is to WIN this case.

{kg_section}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 RELEVANT DOCUMENTS (Retrieved via RAG Search)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{docs_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❓ LAWYER'S QUERY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{query}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 YOUR FORENSIC ANALYSIS FRAMEWORK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Analyse these documents with extreme rigour. Follow this framework:

═══════════════════════════════════════════════════════════════════════
STEP 1: FIND THE SMOKING GUNS
═══════════════════════════════════════════════════════════════════════

Identify evidence that DESTROYS {case_context['respondent']}'s case:

🔥 Direct Evidence:
- Admissions of wrongdoing in documents
- "Don't tell {case_context['claimant']}" type language
- Instructions to conceal information
- Proof of knowledge before alleged breach
- Late disclosure patterns (why disclose NOW?)

For EACH smoking gun you identify:
✓ Quote the exact text (verbatim, in quotes)
✓ Cite the document: [filename]
✓ Explain WHY this destroys {case_context['respondent']}'s position
✓ Link to specific allegation/warranty breached

═══════════════════════════════════════════════════════════════════════
STEP 2: BUILD {case_context['claimant'].upper()}'S ARGUMENT
═══════════════════════════════════════════════════════════════════════

For each potential claim:

1. WHAT HAPPENED? (Be specific: dates, amounts, actions)
   - Who did what?
   - When did it happen?
   - What was the effect?

2. WHAT LEGAL DUTY WAS BREACHED?
   - Cite specific contract clauses
   - Cite specific warranties
   - Cite fiduciary/statutory duties
   - Cite arbitration rules if relevant

3. EVIDENCE CHAIN (Build logical proof):
   - Document A proves fact X [cite filename]
   - Document B proves fact Y [cite filename]  
   - X + Y → Therefore Z (the breach)
   - Make the logical chain EXPLICIT

4. QUANTUM (Quantify loss in £):
   - Direct losses
   - Consequential losses
   - Interest calculations
   - Cite documents supporting figures

═══════════════════════════════════════════════════════════════════════
STEP 3: ANTICIPATE {case_context['respondent'].upper()}'S DEFENCE
═══════════════════════════════════════════════════════════════════════

Now PUT ON {case_context['respondent']}'S BARRISTER WIG and attack the case:

What will {case_context['respondent']}'s QC argue?
- Best legal defence available
- Evidence they might rely on
- Alternative interpretations of events
- Procedural/technical objections
- Mitigation arguments

Rate defence strength: WEAK / MEDIUM / STRONG

Why might tribunal prefer {case_context['respondent']}'s position?
- What makes their argument plausible?
- What evidence gaps help them?
- What legal authorities favour them?

═══════════════════════════════════════════════════════════════════════
STEP 4: COUNTER {case_context['respondent'].upper()}'S DEFENCE
═══════════════════════════════════════════════════════════════════════

Destroy EVERY argument they might make:

✓ Evidence contradicting their position [cite documents]
✓ Legal authorities defeating their interpretation
✓ Logic showing their explanation is implausible
✓ Cross-examination questions exposing weaknesses:
   - "You claim X, but [document] proves Y?"
   - "How do you explain this contradiction?"
   - "Why did you wait until [date] to disclose this?"

✓ Missing documents (spoliation inference):
   - What SHOULD exist but wasn't disclosed?
   - What emails/memos are conspicuously absent?
   - What gaps in file chronology?
   - Inference: destroyed because damaging

═══════════════════════════════════════════════════════════════════════
STEP 5: CROSS-EXAMINATION WEAPONS
═══════════════════════════════════════════════════════════════════════

For key {case_context['respondent']} witnesses:

Which witnesses are most vulnerable to attack?
- Who has credibility problems?
- Who made statements contradicted by documents?
- Who had knowledge they deny?

Generate killer cross-examination questions:
- Start with safe questions (lock in their story)
- Build to confrontation with contradicting document
- End with credibility-destroying question
- Always have document backup

Example format:
Q: "You were [role] in [time period], correct?"
Q: "Part of your duties included [X]?"  
Q: "Let me show you [document]..."
Q: "That's your signature/email?"
Q: "But you testified you 'never knew' about [X]?"
Q: "So you lied to this tribunal?"

═══════════════════════════════════════════════════════════════════════
STEP 6: ASSESS TRUE STRENGTH
═══════════════════════════════════════════════════════════════════════

Provide HONEST assessment:

Win Probability: [0-100%]
Be realistic - don't oversell weak claims

Key Risk Factors for {case_context['claimant']}:
- What could go wrong?
- What evidence gaps exist?
- What legal uncertainties?

Settlement Leverage: LOW / MEDIUM / HIGH / NUCLEAR
Why? What makes {case_context['respondent']} want to settle?
- Reputational damage?
- Cost of fighting?
- Strength of evidence?
- Witness credibility issues?

Recommended Strategy:
- Push to tribunal or settle?
- Use as pressure point in negotiation?
- Focus preparation here?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 OUTPUT REQUIREMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Cite SPECIFIC documents by filename in [brackets]
✓ Quote KEY passages verbatim (use "quotation marks")
✓ Explain WHY each finding matters to the case
✓ Build evidence chains: "DOC_A + DOC_B = proof of C"
✓ Think like a barrister preparing for tribunal
✓ NO speculation - only what documents PROVE
✓ Identify "kill shots" - evidence that wins the case
✓ Be adversarial - you're trying to WIN for {case_context['claimant']}

Use extended thinking to work through complex evidence chains.
Find what other analysts would miss.

BEGIN YOUR FORENSIC ANALYSIS NOW."""

    @staticmethod
    def timeline_builder(
        case_context: Dict,
        retrieved_docs: List[Dict],
        knowledge_graph_context: str = ""
    ) -> str:
        """Generate chronological timeline of events"""
        
        docs_text = "\n\n" + "="*70 + "\n\n"
        for i, doc in enumerate(retrieved_docs, 1):
            docs_text += f"DOCUMENT {i}: [{doc['metadata']['filename']}]\n"
            docs_text += f"{doc['text']}\n"
            docs_text += "\n" + "="*70 + "\n\n"
        
        kg_section = ""
        if knowledge_graph_context:
            kg_section = f"\n\nPREVIOUSLY IDENTIFIED EVENTS:\n{knowledge_graph_context}\n\n"
        
        return f"""Build a chronological timeline for {case_context['case_name']}.

CASE: {case_context['claimant']} v {case_context['respondent']}

{kg_section}

DOCUMENTS:
{docs_text}

TASK: Extract ALL significant events with dates and build timeline.

For EACH event:
✓ Date (exact if possible, otherwise "circa [month/year]")
✓ What happened
✓ Who was involved
✓ Source document [filename]
✓ Why this matters to the case

Pay special attention to:
- When {case_context['respondent']} KNEW about problems
- When {case_context['respondent']} SHOULD HAVE disclosed
- When {case_context['respondent']} ACTUALLY disclosed
- Gaps suggesting concealment

Format as:

═══════════════════════════════════════════════════════════════════════
TIMELINE: {case_context['case_name']}
═══════════════════════════════════════════════════════════════════════

📅 [DATE] - [EVENT TITLE]
   What: [Description]
   Who: [People involved]
   Source: [Document filename]
   Significance: [Why this matters]

📅 [DATE] - [EVENT TITLE]
   ...

CRITICAL PERIODS:

Period of Concealment: [date] to [date]
- {case_context['respondent']} knew about [X]
- {case_context['respondent']} failed to disclose
- Duration: [X] months

Timeline Contradictions:
- {case_context['respondent']} claims they "first learned" on [date]
- But documents prove knowledge on [earlier date]
- Discrepancy: [X] months of false statements

Generate the timeline now."""

    @staticmethod
    def contradiction_finder(
        case_context: Dict,
        retrieved_docs: List[Dict],
        witness_statements: List[Dict] = None
    ) -> str:
        """Find contradictions between documents/statements"""
        
        docs_text = "\n\n" + "="*70 + "\n\n"
        for i, doc in enumerate(retrieved_docs, 1):
            docs_text += f"DOCUMENT {i}: [{doc['metadata']['filename']}]\n"
            docs_text += f"{doc['text']}\n"
            docs_text += "\n" + "="*70 + "\n\n"
        
        witness_section = ""
        if witness_statements:
            witness_section = "\n\nWITNESS STATEMENTS:\n"
            for ws in witness_statements:
                witness_section += f"\n[{ws['witness_name']}]:\n{ws['text']}\n"
        
        return f"""Find contradictions in {case_context['case_name']}.

YOU ARE ACTING FOR: {case_context['claimant']}
FINDING CONTRADICTIONS IN: {case_context['respondent']}'s evidence

{witness_section}

DOCUMENTS:
{docs_text}

TASK: Identify contradictions that destroy {case_context['respondent']}'s credibility.

Look for:

1. WITNESS vs DOCUMENT:
   - Witness says "I didn't know"
   - But email proves they did know
   
2. DOCUMENT vs DOCUMENT:
   - Financial statement says X
   - Internal memo says Y
   
3. PLEADING vs EVIDENCE:
   - {case_context['respondent']} pleads "no knowledge"
   - But documents prove knowledge
   
4. TIMELINE IMPOSSIBILITIES:
   - Claims event happened on [date 1]
   - But document proves it was [date 2]
   
5. IMPLAUSIBLE EXPLANATIONS:
   - Explanation doesn't fit facts
   - Better explanation: concealment

For EACH contradiction:

═══════════════════════════════════════════════════════════════════════
CONTRADICTION #{X}: [Title]
═══════════════════════════════════════════════════════════════════════

What {case_context['respondent']} Claims:
"[Quote their claim]"
Source: [Pleading/witness statement/document]

What Evidence Actually Shows:
"[Quote contradicting evidence]"  
Source: [Document filename]

Why This Matters:
- Destroys credibility of [witness]
- Proves [specific allegation]
- Creates inference of [concealment/fraud]

Cross-Examination Ammunition:
Q: "[Question exposing contradiction]"
Q: "[Follow-up to corner witness]"
Q: "[Final credibility-destroying question]"

Severity: LOW / MEDIUM / HIGH / DEVASTATING

Generate all contradictions now. Be thorough and adversarial."""

    @staticmethod
    def brief_drafter(
        topic: str,
        case_context: Dict,
        retrieved_docs: List[Dict],
        knowledge_graph_context: str = ""
    ) -> str:
        """Draft tribunal submission section"""
        
        docs_text = "\n\n" + "="*70 + "\n\n"
        for i, doc in enumerate(retrieved_docs, 1):
            docs_text += f"DOCUMENT {i}: [{doc['metadata']['filename']}]\n"
            docs_text += f"{doc['text']}\n"
            docs_text += "\n" + "="*70 + "\n\n"
        
        kg_section = ""
        if knowledge_graph_context:
            kg_section = f"\n\nPREVIOUSLY ESTABLISHED FACTS:\n{knowledge_graph_context}\n\n"
        
        return f"""Draft tribunal submission for {case_context['case_name']}.

CASE: {case_context['claimant']} v {case_context['respondent']}
TRIBUNAL: {case_context['tribunal']}
TOPIC: {topic}

YOU ARE DRAFTING FOR: {case_context['claimant']} (Claimant)

{kg_section}

EVIDENCE AVAILABLE:
{docs_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DRAFTING INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Use IRAC structure (Issue, Rule, Application, Conclusion):

═══════════════════════════════════════════════════════════════════════
I. ISSUE
═══════════════════════════════════════════════════════════════════════

State the precise legal question:
"Whether {case_context['respondent']} breached [specific duty] by [specific conduct]?"

═══════════════════════════════════════════════════════════════════════
R. RULE
═══════════════════════════════════════════════════════════════════════

Identify applicable legal rules:

Contract Provisions:
- Clause [X]: "[Quote relevant text]"
- Interpretation: [Explain meaning]

Statutory/Common Law Duties:
- [Relevant statute/case law]
- Standard required: [X]

Arbitration Rules:
- {case_context['tribunal']} Rules Article [X]
- Burden/standard of proof

═══════════════════════════════════════════════════════════════════════
A. APPLICATION
═══════════════════════════════════════════════════════════════════════

Apply rule to facts systematically:

Element 1: [State element]
Evidence: 
- [Document A] shows [fact] - [cite filename]
- [Document B] proves [fact] - [cite filename]
- Therefore: Element 1 satisfied ✓

Element 2: [State element]
Evidence:
- [Chain of evidence]
- Therefore: Element 2 satisfied ✓

[Continue for all elements]

Build evidence chains:
"Document A establishes X. Document B proves Y. 
X + Y → Therefore Z (the breach)."

Anticipate {case_context['respondent']}'s Defence:
{case_context['respondent']} may argue [X], but this fails because [Y].

═══════════════════════════════════════════════════════════════════════
C. CONCLUSION
═══════════════════════════════════════════════════════════════════════

{case_context['claimant']} has proven [claim] and is entitled to [relief].

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STYLE REQUIREMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Professional tribunal tone (not hyperbolic)
✓ British English throughout
✓ Short paragraphs (3-5 sentences)
✓ Every factual claim cited to document [filename]
✓ Quote key passages verbatim
✓ Number paragraphs for tribunal bundle
✓ Adversarial but measured

Draft the submission section now. Make it tribunal-ready."""

    @staticmethod
    def settlement_analyser(
        case_context: Dict,
        all_claims: List[Dict],
        knowledge_graph_context: str = ""
    ) -> str:
        """Analyse settlement position and strategy"""
        
        claims_text = "\n\n".join([
            f"CLAIM: {claim['title']}\n"
            f"Strength: {claim.get('strength', 'Unknown')}\n"
            f"Evidence: {claim.get('evidence_summary', 'See detailed analysis')}\n"
            for claim in all_claims
        ])
        
        kg_section = ""
        if knowledge_graph_context:
            kg_section = f"\n\nKEY FINDINGS SO FAR:\n{knowledge_graph_context}\n\n"
        
        return f"""Analyse settlement position for {case_context['case_name']}.

CASE: {case_context['claimant']} v {case_context['respondent']}

YOUR CLIENT: {case_context['claimant']}

{kg_section}

ALL CLAIMS:
{claims_text}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SETTLEMENT ANALYSIS FRAMEWORK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

═══════════════════════════════════════════════════════════════════════
1. STRENGTH ASSESSMENT (Per Claim)
═══════════════════════════════════════════════════════════════════════

For each claim, assess:

Win Probability: [0-100%]
- What's the realistic chance of success?
- What evidence supports this estimate?
- What are the key risks?

Expected Value:
- Claimed amount: £[X]
- Win probability: [Y]%
- Expected value: £[X × Y]

═══════════════════════════════════════════════════════════════════════
2. {case_context['respondent'].upper()}'S VULNERABILITIES
═══════════════════════════════════════════════════════════════════════

What makes {case_context['respondent']} want to settle?

Reputational Damage:
- What's embarrassing for them?
- What would hurt their business?
- What smoking guns are nuclear?

Cost of Fighting:
- Legal fees for full hearing: £[X]
- Management time and distraction
- Disclosure costs

Witness Credibility Issues:
- Which witnesses have problems?
- What contradictions are devastating?
- Who will look bad under cross-examination?

Strength of Evidence:
- What documents are smoking guns?
- What's indefensible?
- What creates fraud/dishonesty inference?

═══════════════════════════════════════════════════════════════════════
3. {case_context['claimant'].upper()}'S VULNERABILITIES
═══════════════════════════════════════════════════════════════════════

Be honest - what are YOUR weaknesses?

Evidence Gaps:
- What's missing?
- What would strengthen the case?
- What late disclosure might help {case_context['respondent']}?

Legal Uncertainties:
- Any ambiguous contract terms?
- Any adverse case law?
- Any procedural risks?

Cost/Time Factors:
- Can {case_context['claimant']} afford full hearing?
- Time pressure to resolve?
- Cash flow needs?

═══════════════════════════════════════════════════════════════════════
4. SETTLEMENT RANGE CALCULATION
═══════════════════════════════════════════════════════════════════════

Best Case (100% win): £[X]
Most Likely (probability-weighted): £[Y]
Worst Case (lose): £0
Costs to hearing: £[Z]

BATNA (Best Alternative to Negotiated Agreement):
Expected value at hearing: £[Y]
Minus legal costs: -£[Z]
Net BATNA: £[Y - Z]

Therefore, accept settlement ≥ £[BATNA figure]

═══════════════════════════════════════════════════════════════════════
5. NEGOTIATION STRATEGY
═══════════════════════════════════════════════════════════════════════

Opening Position: £[X] (justify with strong claims)

Walk-Away Number: £[BATNA]

Pressure Points to Use:
1. [Smoking gun that embarrasses them]
2. [Witness credibility issues]
3. [Reputational damage of hearing]
4. [Strength of key claim]

Timing:
- Settle now or push closer to hearing?
- What disclosure might change calculation?
- Any time pressure on either side?

Tactics:
- Lead with strongest claim
- Reference most embarrassing evidence
- Emphasise cost/distraction of fighting
- Show confidence in winning

═══════════════════════════════════════════════════════════════════════
6. RECOMMENDATION
═══════════════════════════════════════════════════════════════════════

SETTLE or PROCEED TO HEARING?

Why:
[Reasoning based on above analysis]

If settling:
- Target range: £[X] to £[Y]
- Walk away if below: £[Z]
- Tactics: [Strategy]

If proceeding:
- Focus preparation on: [Areas]
- Strengthen evidence on: [Gaps]
- Neutralise their defence by: [Actions]

Generate the settlement analysis now."""