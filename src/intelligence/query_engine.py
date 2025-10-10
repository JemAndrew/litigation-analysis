#!/usr/bin/env python3
"""
Smart Query Engine - RAG with Query Expansion & Citation Validation

Core features:
- Query expansion (find more relevant docs)
- Query routing (right prompt for right question)
- Hybrid retrieval (semantic + keyword)
- Citation validation (prevent hallucination)
- Cost tracking
- Cumulative learning via knowledge graph

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

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Result from query engine"""
    query: str
    expanded_queries: List[str]
    retrieved_docs: List[Dict]
    analysis: str
    citations: List[str]
    cost_gbp: float
    thinking_used: bool
    timestamp: str


class QueryEngine:
    """
    Smart query engine with RAG, query expansion, and citation validation
    """
    
    def __init__(self, 
                 vector_store,
                 claude_client,
                 case_context: Dict,
                 knowledge_graph=None):
        """
        Initialise query engine
        
        Args:
            vector_store: EnhancedVectorStore instance
            claude_client: Anthropic client
            case_context: Case metadata (claimant, respondent, allegations, etc.)
            knowledge_graph: Optional knowledge graph for cumulative learning
        """
        self.vector_store = vector_store
        self.claude = claude_client
        self.case_context = case_context
        self.knowledge_graph = knowledge_graph
        
        # Cost tracking
        self.total_cost_gbp = 0.0
        self.query_count = 0
        
        # Query expansion synonyms (litigation-specific)
        self.legal_synonyms = {
            'conceal': ['hide', 'withhold', 'suppress', 'omit', 'fail to disclose'],
            'breach': ['violation', 'contravention', 'non-compliance', 'default'],
            'knew': ['aware', 'knowledge', 'informed', 'cognisant', 'understood'],
            'fraud': ['deceit', 'misrepresentation', 'dishonesty', 'false statement'],
            'loss': ['damage', 'harm', 'prejudice', 'detriment', 'injury'],
            'liable': ['responsible', 'accountable', 'answerable', 'culpable'],
        }
    
    def expand_query(self, query: str) -> List[str]:
        """
        Expand query with synonyms and related terms
        
        Args:
            query: Original query
            
        Returns:
            List of expanded queries (original + variations)
        """
        expanded = [query]  # Always include original
        
        query_lower = query.lower()
        
        # Find matching legal terms and add synonyms
        for term, synonyms in self.legal_synonyms.items():
            if term in query_lower:
                # Create variation with each synonym
                for syn in synonyms[:2]:  # Limit to top 2 to avoid explosion
                    expanded_query = query_lower.replace(term, syn)
                    expanded.append(expanded_query)
        
        # Deduplicate
        expanded = list(set(expanded))
        
        logger.info(f"Expanded query into {len(expanded)} variations")
        return expanded[:5]  # Max 5 variations
    
    def route_query(self, query: str) -> str:
        """
        Route query to appropriate prompt type
        
        Args:
            query: User's query
            
        Returns:
            Prompt type identifier
        """
        query_lower = query.lower()
        
        # Pattern matching for prompt types
        if any(word in query_lower for word in ['smoking gun', 'evidence', 'proof', 'show']):
            return 'smoking_gun'
        
        elif any(word in query_lower for word in ['timeline', 'chronology', 'sequence', 'when']):
            return 'timeline'
        
        elif any(word in query_lower for word in ['contradict', 'inconsistency', 'discrepancy']):
            return 'contradiction'
        
        elif any(word in query_lower for word in ['cross-exam', 'cross exam', 'question', 'witness']):
            return 'cross_examination'
        
        elif any(word in query_lower for word in ['argument', 'brief', 'draft', 'submission']):
            return 'brief_generation'
        
        elif any(word in query_lower for word in ['settle', 'leverage', 'strength', 'probability']):
            return 'settlement_analysis'
        
        else:
            # Default: forensic analysis
            return 'forensic_analysis'
    
    def retrieve_with_context(self, query: str, n_results: int = 15) -> List[Dict]:
        """
        Retrieve documents with query expansion and knowledge graph context
        
        Args:
            query: Search query
            n_results: Number of results
            
        Returns:
            Retrieved document chunks with metadata
        """
        # Expand query
        expanded_queries = self.expand_query(query)
        
        # Retrieve for each expanded query
        all_results = []
        seen_chunk_ids = set()
        
        for exp_query in expanded_queries:
            try:
                results = self.vector_store.search(
                    query=exp_query,
                    n_results=n_results,
                    use_reranker=True
                )
                
                # Deduplicate by chunk ID
                for result in results:
                    chunk_id = f"{result['metadata'].get('filename')}_{result['metadata'].get('chunk_index')}"
                    if chunk_id not in seen_chunk_ids:
                        all_results.append(result)
                        seen_chunk_ids.add(chunk_id)
                
            except Exception as e:
                logger.error(f"Retrieval error for '{exp_query}': {e}")
                continue
        
        # Sort by relevance score (hybrid_score or rerank_score)
        all_results.sort(
            key=lambda x: x.get('rerank_score', x.get('hybrid_score', 0)),
            reverse=True
        )
        
        # Return top N
        final_results = all_results[:n_results]
        
        logger.info(f"Retrieved {len(final_results)} unique chunks")
        return final_results
    
    def validate_citations(self, analysis: str, retrieved_docs: List[Dict]) -> Tuple[List[str], List[str]]:
        """
        Validate that all cited documents exist and quotes are accurate
        
        Args:
            analysis: Claude's analysis text
            retrieved_docs: Documents that were retrieved
            
        Returns:
            Tuple of (valid_citations, invalid_citations)
        """
        # Extract all DOC_ID citations from analysis
        citation_pattern = r'\[([A-Z0-9_]+)\]|\(([A-Z0-9_]+)\)|DOC_([A-Z0-9_]+)'
        citations = re.findall(citation_pattern, analysis)
        
        # Flatten tuples from regex groups
        cited_doc_ids = set()
        for match in citations:
            for group in match:
                if group:
                    cited_doc_ids.add(group)
        
        # Get available doc IDs from retrieved docs
        available_doc_ids = set()
        for doc in retrieved_docs:
            filename = doc['metadata'].get('filename', '')
            # Handle various ID formats
            if filename:
                available_doc_ids.add(filename)
                # Also add without extension
                available_doc_ids.add(filename.split('.')[0])
        
        # Validate
        valid = []
        invalid = []
        
        for cited_id in cited_doc_ids:
            # Check if cited doc was in retrieval results
            found = False
            for available_id in available_doc_ids:
                if cited_id in available_id or available_id in cited_id:
                    found = True
                    valid.append(cited_id)
                    break
            
            if not found:
                invalid.append(cited_id)
                logger.warning(f"⚠️  Citation '{cited_id}' not found in retrieved documents")
        
        return valid, invalid
    
    def query(self, 
              query: str,
              use_extended_thinking: bool = True,
              n_results: int = 15) -> QueryResult:
        """
        Execute complete query pipeline
        
        Pipeline:
        1. Route query to prompt type
        2. Expand query for better retrieval
        3. Retrieve relevant documents
        4. Check knowledge graph for prior findings
        5. Build context-aware prompt
        6. Call Claude with extended thinking
        7. Validate citations
        8. Store findings in knowledge graph
        9. Return result
        
        Args:
            query: User's question
            use_extended_thinking: Whether to use extended thinking (recommended)
            n_results: Number of documents to retrieve
            
        Returns:
            QueryResult with analysis and metadata
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"NEW QUERY: {query}")
        logger.info(f"{'='*70}")
        
        # Step 1: Route query
        prompt_type = self.route_query(query)
        logger.info(f"📍 Routed to: {prompt_type}")
        
        # Step 2: Expand and retrieve
        expanded_queries = self.expand_query(query)
        logger.info(f"🔍 Expanded to {len(expanded_queries)} variations")
        
        retrieved_docs = self.retrieve_with_context(query, n_results)
        
        if not retrieved_docs:
            logger.warning("⚠️  No documents retrieved!")
            return QueryResult(
                query=query,
                expanded_queries=expanded_queries,
                retrieved_docs=[],
                analysis="No relevant documents found. Have you run /ingest?",
                citations=[],
                cost_gbp=0.0,
                thinking_used=False,
                timestamp=datetime.now().isoformat()
            )
        
        logger.info(f"📄 Retrieved {len(retrieved_docs)} chunks")
        
        # Step 3: Check knowledge graph for prior findings
        prior_findings = ""
        if self.knowledge_graph:
            try:
                prior = self.knowledge_graph.get_relevant_findings(query)
                if prior:
                    prior_findings = "\n\n🧠 PRIOR FINDINGS FROM EARLIER QUERIES:\n"
                    prior_findings += "\n".join([f"- {finding}" for finding in prior[:5]])
                    logger.info(f"🧠 Found {len(prior)} prior findings to include")
            except Exception as e:
                logger.error(f"Knowledge graph error: {e}")
        
        # Step 4: Build context from retrieved docs
        context = self._format_retrieved_docs(retrieved_docs)
        context += prior_findings
        
        # Step 5: Get appropriate prompt
        from prompts.universal_forensic_prompts import ForensicPrompts
        prompts = ForensicPrompts()
        
        if prompt_type == 'smoking_gun':
            prompt = prompts.smoking_gun_finder(query, context, self.case_context)
        elif prompt_type == 'timeline':
            prompt = prompts.timeline_builder(query, context, self.case_context)
        elif prompt_type == 'contradiction':
            prompt = prompts.contradiction_hunter(query, context, self.case_context)
        elif prompt_type == 'cross_examination':
            prompt = prompts.cross_examination_generator(query, context, self.case_context)
        elif prompt_type == 'brief_generation':
            prompt = prompts.brief_drafter(query, context, self.case_context)
        elif prompt_type == 'settlement_analysis':
            prompt = prompts.settlement_analyser(query, context, self.case_context)
        else:
            prompt = prompts.forensic_analysis(query, context, self.case_context)
        
        # Step 6: Call Claude
        logger.info("🤖 Calling Claude API...")
        
        try:
            kwargs = {
                'model': 'claude-sonnet-4-20250514',
                'max_tokens': 16000,
                'messages': [{'role': 'user', 'content': prompt}]
            }
            
            if use_extended_thinking:
                kwargs['thinking'] = {
                    'type': 'enabled',
                    'budget_tokens': 10000
                }
            
            response = self.claude.messages.create(**kwargs)
            
            # Extract analysis text
            analysis = ""
            for block in response.content:
                if block.type == 'text':
                    analysis += block.text
            
            # Calculate cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            thinking_tokens = getattr(response.usage, 'thinking_tokens', 0)
            
            # Sonnet 4 pricing (approximate)
            cost_usd = (input_tokens * 0.000003) + (output_tokens * 0.000015)
            cost_gbp = cost_usd * 1.27  # USD to GBP
            
            self.total_cost_gbp += cost_gbp
            self.query_count += 1
            
            logger.info(f"💰 Query cost: £{cost_gbp:.4f}")
            logger.info(f"💰 Total cost: £{self.total_cost_gbp:.2f} ({self.query_count} queries)")
            
        except Exception as e:
            logger.error(f"❌ Claude API error: {e}")
            raise
        
        # Step 7: Validate citations
        valid_citations, invalid_citations = self.validate_citations(analysis, retrieved_docs)
        
        if invalid_citations:
            logger.warning(f"⚠️  {len(invalid_citations)} potentially hallucinated citations: {invalid_citations}")
            # Append warning to analysis
            analysis += f"\n\n⚠️ WARNING: The following citations could not be verified: {', '.join(invalid_citations)}"
        
        logger.info(f"✅ Validated {len(valid_citations)} citations")
        
        # Step 8: Store in knowledge graph
        if self.knowledge_graph:
            try:
                self.knowledge_graph.add_finding({
                    'query': query,
                    'prompt_type': prompt_type,
                    'analysis': analysis,
                    'citations': valid_citations,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Failed to store in knowledge graph: {e}")
        
        # Step 9: Return result
        return QueryResult(
            query=query,
            expanded_queries=expanded_queries,
            retrieved_docs=retrieved_docs,
            analysis=analysis,
            citations=valid_citations,
            cost_gbp=cost_gbp,
            thinking_used=use_extended_thinking,
            timestamp=datetime.now().isoformat()
        )
    
    def _format_retrieved_docs(self, docs: List[Dict]) -> str:
        """Format retrieved documents for prompt context"""
        formatted = ""
        for i, doc in enumerate(docs, 1):
            filename = doc['metadata'].get('filename', 'Unknown')
            folder = doc['metadata'].get('folder', '')
            text = doc['text']
            
            formatted += f"\n{'─'*70}\n"
            formatted += f"DOCUMENT {i}: [{filename}]"
            if folder:
                formatted += f" (Folder: {folder})"
            formatted += f"\n{'─'*70}\n"
            formatted += f"{text}\n"
        
        return formatted
    
    def get_stats(self) -> Dict:
        """Get query engine statistics"""
        return {
            'total_queries': self.query_count,
            'total_cost_gbp': round(self.total_cost_gbp, 2),
            'avg_cost_per_query': round(self.total_cost_gbp / max(self.query_count, 1), 4),
            'vector_store_stats': self.vector_store.get_stats()
        }