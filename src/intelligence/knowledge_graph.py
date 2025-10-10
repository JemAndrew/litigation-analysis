#!/usr/bin/env python3
"""
Cumulative Knowledge Graph - System "learns" across queries

Stores findings from each query and makes them available to future queries.
This creates a snowball effect where each query makes the next one smarter.

British English throughout.
"""

from pathlib import Path

# Add src to path for imports
import sys
from pathlib import Path
src_dir = Path(__file__).parent.parent if "src" in str(Path(__file__).parent) else Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
    sys.path.insert(0, str(src_dir.parent))

from typing import Dict, List, Optional
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CumulativeKnowledgeGraph:
    """
    Knowledge graph that accumulates insights across queries
    
    After each query, extracts and stores:
    - Smoking guns found
    - Evidence chains built
    - Contradictions identified
    - Cross-exam questions generated
    - Legal arguments formulated
    
    Future queries can reference prior findings.
    """
    
    def __init__(self, case_dir: Path):
        """
        Initialise knowledge graph
        
        Args:
            case_dir: Path to case directory
        """
        self.case_dir = Path(case_dir)
        self.graph_file = self.case_dir / "knowledge_graph.json"
        
        # Graph structure
        self.graph = {
            'smoking_guns': [],
            'contradictions': [],
            'evidence_chains': [],
            'cross_exam_questions': [],
            'legal_arguments': [],
            'timelines': [],
            'settlement_analysis': [],
            'query_history': []
        }
        
        # Load existing graph
        self._load_graph()
    
    def _load_graph(self):
        """Load graph from disk"""
        if self.graph_file.exists():
            try:
                with open(self.graph_file, 'r', encoding='utf-8') as f:
                    self.graph = json.load(f)
                logger.info(f"📚 Loaded knowledge graph: {len(self.graph.get('query_history', []))} prior queries")
            except Exception as e:
                logger.error(f"Failed to load knowledge graph: {e}")
    
    def _save_graph(self):
        """Save graph to disk"""
        try:
            with open(self.graph_file, 'w', encoding='utf-8') as f:
                json.dump(self.graph, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save knowledge graph: {e}")
    
    def add_finding(self, finding: Dict):
        """
        Add finding from query to knowledge graph
        
        Args:
            finding: Dict with query, analysis, citations, etc.
        """
        try:
            # Add to query history
            self.graph['query_history'].append({
                'query': finding.get('query'),
                'prompt_type': finding.get('prompt_type'),
                'timestamp': finding.get('timestamp'),
                'citations': finding.get('citations', [])
            })
            
            # Extract and categorise findings from analysis
            analysis = finding.get('analysis', '')
            
            # Extract smoking guns (look for markers in analysis)
            if 'SMOKING GUN' in analysis.upper():
                self._extract_smoking_guns(analysis, finding)
            
            # Extract contradictions
            if 'CONTRADICTION' in analysis.upper():
                self._extract_contradictions(analysis, finding)
            
            # Extract evidence chains
            if 'EVIDENCE CHAIN' in analysis.upper() or 'THEREFORE' in analysis.upper():
                self._extract_evidence_chains(analysis, finding)
            
            # Store cross-exam questions
            if finding.get('prompt_type') == 'cross_examination':
                self._extract_cross_exam(analysis, finding)
            
            # Store legal arguments
            if finding.get('prompt_type') in ['brief_generation', 'forensic_analysis']:
                self._extract_legal_arguments(analysis, finding)
            
            # Store timeline
            if finding.get('prompt_type') == 'timeline':
                self._extract_timeline(analysis, finding)
            
            # Store settlement analysis
            if finding.get('prompt_type') == 'settlement_analysis':
                self._extract_settlement(analysis, finding)
            
            # Save updated graph
            self._save_graph()
            
            logger.info("📚 Knowledge graph updated")
            
        except Exception as e:
            logger.error(f"Failed to add finding to knowledge graph: {e}")
    
    def _extract_smoking_guns(self, analysis: str, finding: Dict):
        """Extract smoking gun evidence from analysis"""
        # Simple extraction - look for smoking gun sections
        lines = analysis.split('\n')
        current_gun = None
        
        for line in lines:
            if 'SMOKING GUN' in line.upper() and ':' in line:
                if current_gun:
                    self.graph['smoking_guns'].append(current_gun)
                current_gun = {
                    'title': line.split(':')[-1].strip(),
                    'source_query': finding.get('query'),
                    'timestamp': finding.get('timestamp'),
                    'details': []
                }
            elif current_gun and line.strip():
                current_gun['details'].append(line.strip())
        
        if current_gun:
            self.graph['smoking_guns'].append(current_gun)
    
    def _extract_contradictions(self, analysis: str, finding: Dict):
        """Extract contradictions from analysis"""
        lines = analysis.split('\n')
        current_contradiction = None
        
        for line in lines:
            if 'CONTRADICTION' in line.upper() and ('#' in line or ':' in line):
                if current_contradiction:
                    self.graph['contradictions'].append(current_contradiction)
                current_contradiction = {
                    'title': line.strip(),
                    'source_query': finding.get('query'),
                    'timestamp': finding.get('timestamp'),
                    'details': []
                }
            elif current_contradiction and line.strip():
                current_contradiction['details'].append(line.strip())
        
        if current_contradiction:
            self.graph['contradictions'].append(current_contradiction)
    
    def _extract_evidence_chains(self, analysis: str, finding: Dict):
        """Extract evidence chains from analysis"""
        # Look for numbered lists with document citations
        lines = analysis.split('\n')
        current_chain = []
        
        for line in lines:
            # Look for evidence chain patterns: "1. [DOC_X] shows..."
            if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('-')):
                if '[' in line or 'DOC_' in line:
                    current_chain.append(line.strip())
            elif current_chain and ('THEREFORE' in line.upper() or 'CONCLUSION' in line.upper()):
                current_chain.append(line.strip())
                self.graph['evidence_chains'].append({
                    'chain': current_chain,
                    'source_query': finding.get('query'),
                    'timestamp': finding.get('timestamp')
                })
                current_chain = []
        
        if current_chain and len(current_chain) >= 2:
            self.graph['evidence_chains'].append({
                'chain': current_chain,
                'source_query': finding.get('query'),
                'timestamp': finding.get('timestamp')
            })
    
    def _extract_cross_exam(self, analysis: str, finding: Dict):
        """Extract cross-examination questions"""
        lines = analysis.split('\n')
        questions = []
        
        for line in lines:
            if line.strip().startswith('Q:') or line.strip().startswith('Q.'):
                questions.append(line.strip())
        
        if questions:
            self.graph['cross_exam_questions'].append({
                'questions': questions,
                'source_query': finding.get('query'),
                'timestamp': finding.get('timestamp')
            })
    
    def _extract_legal_arguments(self, analysis: str, finding: Dict):
        """Extract legal arguments"""
        # Store the entire argument section
        self.graph['legal_arguments'].append({
            'argument': analysis[:1000],  # First 1000 chars
            'source_query': finding.get('query'),
            'citations': finding.get('citations', []),
            'timestamp': finding.get('timestamp')
        })
    
    def _extract_timeline(self, analysis: str, finding: Dict):
        """Extract timeline"""
        self.graph['timelines'].append({
            'timeline': analysis[:2000],  # First 2000 chars
            'source_query': finding.get('query'),
            'timestamp': finding.get('timestamp')
        })
    
    def _extract_settlement(self, analysis: str, finding: Dict):
        """Extract settlement analysis"""
        self.graph['settlement_analysis'].append({
            'analysis': analysis[:1500],
            'source_query': finding.get('query'),
            'timestamp': finding.get('timestamp')
        })
    
    def get_relevant_findings(self, query: str) -> List[str]:
        """
        Get prior findings relevant to current query
        
        Args:
            query: Current query
            
        Returns:
            List of relevant prior findings
        """
        relevant = []
        query_lower = query.lower()
        
        # Check for smoking guns
        if any(word in query_lower for word in ['smoking gun', 'evidence', 'proof']):
            for gun in self.graph['smoking_guns'][-5:]:  # Last 5
                relevant.append(f"Prior smoking gun: {gun.get('title')}")
        
        # Check for contradictions
        if 'contradict' in query_lower or 'inconsisten' in query_lower:
            for contra in self.graph['contradictions'][-5:]:
                relevant.append(f"Prior contradiction: {contra.get('title')}")
        
        # Check for timeline
        if 'timeline' in query_lower or 'when' in query_lower:
            for timeline in self.graph['timelines'][-2:]:
                relevant.append(f"Prior timeline analysis available from query: {timeline.get('source_query')}")
        
        # Check for cross-exam
        if 'cross' in query_lower or 'question' in query_lower:
            for xexam in self.graph['cross_exam_questions'][-3:]:
                relevant.append(f"Prior cross-exam questions for: {xexam.get('source_query')}")
        
        return relevant
    
    def get_stats(self) -> Dict:
        """Get knowledge graph statistics"""
        return {
            'total_queries': len(self.graph.get('query_history', [])),
            'smoking_guns': len(self.graph.get('smoking_guns', [])),
            'contradictions': len(self.graph.get('contradictions', [])),
            'evidence_chains': len(self.graph.get('evidence_chains', [])),
            'cross_exam_sets': len(self.graph.get('cross_exam_questions', [])),
            'legal_arguments': len(self.graph.get('legal_arguments', [])),
            'timelines': len(self.graph.get('timelines', [])),
            'settlement_analyses': len(self.graph.get('settlement_analysis', []))
        }
    
    def export_summary(self, output_path: Path):
        """
        Export knowledge graph summary to markdown
        
        Args:
            output_path: Path to save summary
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# Knowledge Graph Summary\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Query history
                f.write(f"## Query History ({len(self.graph['query_history'])} queries)\n\n")
                for i, query in enumerate(self.graph['query_history'][-20:], 1):
                    f.write(f"{i}. **{query.get('query')}**\n")
                    f.write(f"   - Type: {query.get('prompt_type')}\n")
                    f.write(f"   - Time: {query.get('timestamp')}\n\n")
                
                # Smoking guns
                f.write(f"\n## Smoking Guns ({len(self.graph['smoking_guns'])})\n\n")
                for i, gun in enumerate(self.graph['smoking_guns'], 1):
                    f.write(f"### {i}. {gun.get('title')}\n")
                    f.write(f"Source: {gun.get('source_query')}\n\n")
                
                # Contradictions
                f.write(f"\n## Contradictions ({len(self.graph['contradictions'])})\n\n")
                for i, contra in enumerate(self.graph['contradictions'], 1):
                    f.write(f"### {i}. {contra.get('title')}\n")
                    f.write(f"Source: {contra.get('source_query')}\n\n")
                
                # Evidence chains
                f.write(f"\n## Evidence Chains ({len(self.graph['evidence_chains'])})\n\n")
                for i, chain in enumerate(self.graph['evidence_chains'], 1):
                    f.write(f"### Chain {i}\n")
                    for step in chain.get('chain', []):
                        f.write(f"- {step}\n")
                    f.write(f"\nSource: {chain.get('source_query')}\n\n")
            
            logger.info(f"📄 Knowledge graph summary exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to export summary: {e}")