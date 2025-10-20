# src/core/case_bible_builder.py (NEW FILE)

class CaseBibleBuilder:
    """
    Builds comprehensive case foundation document from pleadings
    
    This is cached in Claude's context for 95% cost savings
    """
    
    def build_case_bible(self, case_id: str) -> str:
        """
        Create structured case bible:
        1. Case overview
        2. Parties & representatives
        3. Key dates & timeline
        4. All claims summarised
        5. All defences summarised
        6. Key allegations
        7. Disputed facts
        8. Legal framework
        9. Quantum summary
        """
        
        # Read pleadings
        pleadings = self._load_pleadings(case_id)
        
        # Generate using Claude with extended thinking
        bible_prompt = f"""
        Read these pleadings and create a comprehensive case bible:
        
        {pleadings}
        
        Structure:
        1. CASE OVERVIEW (parties, tribunal, key dates)
        2. CLAIMS (each claim with legal basis)
        3. DEFENCES (each defence argument)
        4. KEY ALLEGATIONS
        5. DISPUTED FACTS
        6. LEGAL FRAMEWORK (applicable law, precedents)
        7. QUANTUM (amounts claimed per head)
        """
        
        # Call Claude once
        bible = self._call_claude_for_bible(bible_prompt)
        
        # Save to case directory
        self._save_bible(case_id, bible)
        
        return bible