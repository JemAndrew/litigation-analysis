#!/usr/bin/env python3
"""
Enhanced Analysis Prompts - For Detailed Document Explanations
British English throughout
"""


class EnhancedAnalysisPrompts:
    """Prompts that provide detailed explanations for every score"""
    
    @staticmethod
    def detailed_document_analysis(
        doc_id: str,
        document_name: str,
        date: str,
        content: str,
        claimant: str,
        respondent: str
    ) -> str:
        """
        Comprehensive analysis prompt with structured explanations
        
        Returns detailed breakdown of:
        - Document summary
        - Scoring with explanations
        - Litigation value
        - Tactical recommendations
        """
        
        return f"""You are a forensic litigation analyst for {claimant} in the case against {respondent}.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DOCUMENT TO ANALYSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Doc ID: {doc_id}
Document Name: {document_name}
Date: {date}

CONTENT:
{content}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOUR TASK: COMPLETE FORENSIC ANALYSIS WITH DETAILED EXPLANATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Provide analysis in this EXACT structure:

═══════════════════════════════════════════════════════════════════════
1. DOCUMENT SUMMARY
═══════════════════════════════════════════════════════════════════════
[Write 2-3 sentences explaining:]
- What type of document this is (email, memo, contract, minutes, etc.)
- Who created it and who received it
- What the document discusses or contains
- Key dates or events mentioned

═══════════════════════════════════════════════════════════════════════
2. SMOKING GUN SCORE: [X.X/10]
═══════════════════════════════════════════════════════════════════════

SCORE EXPLANATION:
[Explain WHY you gave this score. Consider:]
- Admissions of wrongdoing or liability
- Concealment language ("don't tell", "withhold", "hide", "not disclose")
- Knowledge demonstrated before alleged breach
- Instructions to deceive or mislead
- Direct evidence of bad faith
- Late disclosure patterns (why disclosed NOW?)

KEY EVIDENCE QUOTES:
1. "[Exact quote from document that proves smoking gun]"
2. "[Another exact quote if relevant]"
3. "[Another exact quote if relevant]"

REASONING:
[2-3 sentences explaining how the quotes above justify this score]

If score is 8-10: This is nuclear evidence
If score is 6-7: This is strong evidence
If score is 4-5: This is moderate evidence
If score is 0-3: This is weak or no evidence

═══════════════════════════════════════════════════════════════════════
3. CONCEALMENT SCORE: [X.X/10]
═══════════════════════════════════════════════════════════════════════

SCORE EXPLANATION:
[Explain WHY you gave this score. Consider:]
- Deliberate withholding of material information
- "Wait until after" or timing-based concealment
- False or misleading representations
- Omissions from disclosure schedules
- Pattern of selective disclosure
- Evidence of concealment strategy

KEY EVIDENCE QUOTES:
1. "[Exact quote showing concealment]"
2. "[Another exact quote if relevant]"

REASONING:
[Explain the concealment pattern and why it matters]

═══════════════════════════════════════════════════════════════════════
4. CONTRADICTION SCORE: [X.X/10]
═══════════════════════════════════════════════════════════════════════

SCORE EXPLANATION:
[Explain WHY you gave this score. Consider:]
- Contradicts witness statements
- Contradicts earlier disclosure or pleadings
- Contradicts warranties in the SPA
- Timeline impossibilities
- Inconsistent positions taken
- Statements that contradict observable facts

CONTRADICTIONS IDENTIFIED:
1. [Document says X, but {respondent} claimed Y in witness statement]
2. [Document dated A, but {respondent} claimed event happened on date B]
3. [Another contradiction if relevant]

REASONING:
[Explain why these contradictions destroy credibility]

═══════════════════════════════════════════════════════════════════════
5. OVERALL RANKING: [X.X/10]
═══════════════════════════════════════════════════════════════════════

CATEGORY: [CRITICAL / HIGH / MEDIUM / LOW]

Scoring Guide:
- 9.0-10.0 = CRITICAL (nuclear evidence, case-winning)
- 7.0-8.9 = HIGH (very strong evidence)
- 5.0-6.9 = MEDIUM (relevant evidence)
- 0.0-4.9 = LOW (peripheral or weak)

OVERALL EXPLANATION:
[3-4 sentences synthesising the above scores explaining:]
- Why this document matters to {claimant}'s case
- What it proves or disproves
- How it advances {claimant}'s position
- Why {respondent} should fear this document

CRITICAL FACTORS DRIVING SCORE:
1. [Primary factor - most important thing about this document]
2. [Secondary factor - second most important]
3. [Tertiary factor - supporting element]

═══════════════════════════════════════════════════════════════════════
6. LITIGATION VALUE
═══════════════════════════════════════════════════════════════════════

This document is strategically valuable because:

PROVES/ESTABLISHES:
1. [Specific fact or element this document proves]
2. [Another specific fact or element]
3. [Another specific fact or element]

DESTROYS {respondent.upper()}'S POSITION BY:
- [Specific way it undermines their case]
- [Another specific way if applicable]

STRENGTHENS {claimant.upper()}'S POSITION BY:
- [Specific way it helps your case]
- [Another specific way if applicable]

DAMAGES QUANTIFICATION:
[If applicable, explain how this document supports damages claims]
[If not applicable, write "Not directly relevant to quantum"]

═══════════════════════════════════════════════════════════════════════
7. RECOMMENDED TACTICAL USE
═══════════════════════════════════════════════════════════════════════

**OPENING SUBMISSIONS:**
[How to use this document in opening - be specific]
Example: "Lead with this as Exhibit A proving concealment"

**CROSS-EXAMINATION:**
[Generate 3-5 killer questions for relevant witness]
Q1: "[Specific question using this document]"
Q2: "[Follow-up question that corners witness]"
Q3: "[Devastating final question]"

**CLOSING ARGUMENTS:**
[How to use this document in closing]
Example: "This document proves the entire concealment strategy"

**SETTLEMENT NEGOTIATIONS:**
[How this affects settlement leverage]
Example: "Wave this document at mediation - they'll settle immediately"

**TRIBUNAL BUNDLE:**
Priority: [HIGH / MEDIUM / LOW]
Bundle tab recommendation: [Where it should go in bundle]

═══════════════════════════════════════════════════════════════════════
8. RELATED DOCUMENTS TO REVIEW
═══════════════════════════════════════════════════════════════════════

This document should be cross-referenced with:
1. [Doc ID or description: Why it's related and what to look for]
2. [Another document: Why it's related]
3. [Another document: Why it's related]

SUGGESTED EVIDENCE CHAIN:
[Describe how this document fits into a larger evidence chain]
Example: "Doc A + This Document + Doc C = Complete proof of concealment"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL REMINDERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Quote exact text from the document (use quotation marks)
✓ Be specific about dates, amounts, people mentioned
✓ Explain your reasoning clearly - lawyers need to understand WHY
✓ Think adversarially - you're trying to WIN for {claimant}
✓ British English throughout
✓ Be honest about weaknesses (don't oversell weak documents)
✓ Focus on actionable intelligence lawyers can use

BEGIN YOUR DETAILED ANALYSIS NOW:
"""

    @staticmethod
    def batch_prioritisation(documents_summary: str, case_context: str) -> str:
        """
        After analysing multiple documents, prioritise which need deep review
        """
        
        return f"""You have analysed multiple documents. Now prioritise them.

CASE CONTEXT:
{case_context}

DOCUMENTS ANALYSED:
{documents_summary}

Create a prioritised list:

TIER 1: CRITICAL (Must review immediately)
[List doc IDs and 1-line reason]

TIER 2: HIGH (Review this week)
[List doc IDs and 1-line reason]

TIER 3: MEDIUM (Review when time permits)
[List doc IDs and 1-line reason]

TIER 4: LOW (Archive/background only)
[List doc IDs and 1-line reason]

Provide strategic recommendations for the legal team."""