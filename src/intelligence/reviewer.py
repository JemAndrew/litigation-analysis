#!/usr/bin/env python3
"""
Folder 69 Document Reviewer
Provides detailed explanations for every document score

Features:
- Document summaries
- Detailed scoring with explanations
- Litigation value assessment
- Tactical recommendations
- Excel export with all details
- Pre-ingestion validation
- Cost estimation
- Checkpoint recovery

British English throughout
"""

import sys
from pathlib import Path

# Add src to path for imports
import sys
from pathlib import Path
src_dir = Path(__file__).parent.parent if "src" in str(Path(__file__).parent) else Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
    sys.path.insert(0, str(src_dir.parent))

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import os
import pandas as pd
import re
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from anthropic import Anthropic
from src.intelligence.vector_store import VectorStore
from src.intelligence.knowledge_graph import CumulativeKnowledgeGraph
from src.prompts.analysis_prompt import AnalysisPrompts


@dataclass
class DocumentScore:
    """Complete document analysis with detailed explanations"""
    # Identity
    doc_id: str
    filename: str
    document_name: str = ""
    date: str = ""
    pages: str = ""
    
    # Summary
    document_summary: str = ""
    
    # Scores (0-10)
    smoking_gun_score: float = 0.0
    concealment_score: float = 0.0
    contradiction_score: float = 0.0
    overall_value: float = 0.0
    category: str = "MEDIUM"
    
    # Detailed Explanations (WHY each score)
    smoking_gun_explanation: str = ""
    concealment_explanation: str = ""
    contradiction_explanation: str = ""
    overall_ranking_explanation: str = ""
    critical_factors: List[str] = field(default_factory=list)
    
    # Litigation Intelligence
    litigation_value: str = ""
    proves_establishes: List[str] = field(default_factory=list)
    destroys_opponent: List[str] = field(default_factory=list)
    strengthens_position: List[str] = field(default_factory=list)
    
    # Tactical Recommendations
    opening_use: str = ""
    cross_exam_questions: List[str] = field(default_factory=list)
    closing_use: str = ""
    settlement_impact: str = ""
    
    # Evidence
    key_quotes: List[str] = field(default_factory=list)
    related_documents: List[str] = field(default_factory=list)
    evidence_chain: str = ""
    
    # Metadata
    analysis_timestamp: str = ""
    cost_gbp: float = 0.0


class Folder69Reviewer:
    """
    Complete folder 69 reviewer with detailed explanations
    """
    
    def __init__(self,
                 case_dir: Path,
                 folder_69_path: Path,
                 matched_excel_path: Optional[Path] = None,
                 claimant: str = "Lismore Limited",
                 respondent: str = "Process Holdings plc"):
        """
        Initialise reviewer
        
        Args:
            case_dir: Path to case directory
            folder_69_path: Path to Folder 69 documents
            matched_excel_path: Optional Excel with Doc ID metadata
            claimant: Claimant name
            respondent: Respondent name
        """
        self.case_dir = Path(case_dir)
        self.folder_69_path = Path(folder_69_path)
        self.matched_excel_path = Path(matched_excel_path) if matched_excel_path else None
        
        self.claimant = claimant
        self.respondent = respondent
        
        # Results directory
        self.results_dir = self.case_dir / "analysis" / "folder_69_review"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialise components
        print("🔧 Initialising reviewer...")
        
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set! Set it in .env file or environment.")
        
        self.claude = Anthropic(api_key=api_key)
        self.prompts = AnalysisPrompts()
        
        # Vector store
        print("📚 Loading vector store...")
        self.vector_store = VectorStore(
            case_dir=self.case_dir,
            cohere_api_key=os.getenv('COHERE_API_KEY')
        )
        
        # Knowledge graph
        print("🧠 Loading knowledge graph...")
        self.knowledge_graph = CumulativeKnowledgeGraph(self.case_dir)
        
        # Document metadata from Excel
        self.doc_metadata = {}
        if self.matched_excel_path and self.matched_excel_path.exists():
            self._load_doc_metadata()
        
        # Statistics
        self.total_cost_gbp = 0.0
        self.documents_analysed = 0
        self.document_scores: List[DocumentScore] = []
        
        print("✅ Reviewer ready!\n")
    
    def _load_doc_metadata(self):
        """Load document metadata from matched Excel"""
        try:
            df = pd.read_excel(self.matched_excel_path)
            print(f"📄 Loading metadata from: {self.matched_excel_path.name}")
            
            for _, row in df.iterrows():
                doc_id = str(row.get('Doc ID', '')).strip()
                if doc_id and doc_id != '':
                    self.doc_metadata[doc_id] = {
                        'document_name': str(row.get('Document Name', '')),
                        'date': str(row.get('Date', '')),
                        'pages': str(row.get('Pages', ''))
                    }
            
            print(f"✅ Loaded metadata for {len(self.doc_metadata)} documents\n")
            
        except Exception as e:
            print(f"⚠️  Could not load metadata Excel: {e}")
            print("   Continuing without metadata...\n")
    
    def validate_documents(self) -> Tuple[int, int, List[str]]:
        """
        Validate documents before ingestion
        
        Returns:
            Tuple of (valid_count, invalid_count, invalid_files)
        """
        return self.vector_store.validate_documents(self.folder_69_path)
    
    def estimate_costs(self) -> Dict:
        """
        Estimate complete analysis costs
        
        Returns:
            Cost breakdown dictionary
        """
        # Count documents
        pdf_files = list(self.folder_69_path.rglob('*.pdf'))
        docx_files = list(self.folder_69_path.rglob('*.docx'))
        doc_count = len(pdf_files) + len(docx_files)
        
        # Ingestion cost
        ingestion_estimate = self.vector_store.estimate_ingestion_cost(doc_count)
        
        # Analysis cost (£0.35 per document with extended thinking)
        analysis_cost_per_doc = 0.35
        total_analysis_cost = doc_count * analysis_cost_per_doc
        analysis_time_mins = (doc_count * 90) / 60  # 90 seconds per doc
        
        # Total
        total_cost = ingestion_estimate['estimated_cost_gbp'] + total_analysis_cost
        total_time_mins = ingestion_estimate['estimated_time_minutes'] + analysis_time_mins
        
        return {
            'documents': doc_count,
            'ingestion': {
                'cost_gbp': ingestion_estimate['estimated_cost_gbp'],
                'time_minutes': ingestion_estimate['estimated_time_minutes'],
                'chunks': ingestion_estimate['estimated_chunks']
            },
            'analysis': {
                'cost_gbp': total_analysis_cost,
                'time_minutes': round(analysis_time_mins, 1),
                'cost_per_doc': analysis_cost_per_doc
            },
            'total': {
                'cost_gbp': round(total_cost, 2),
                'time_minutes': round(total_time_mins, 1),
                'time_hours': round(total_time_mins / 60, 1)
            }
        }
    
    def ingest_documents(self):
        """Ingest Folder 69 documents into vector store"""
        print(f"{'='*70}")
        print("DOCUMENT INGESTION")
        print(f"{'='*70}\n")
        
        stats = self.vector_store.get_stats()
        if stats.get('total_documents', 0) > 0:
            print(f"⚠️  Vector store already has {stats['total_documents']} documents")
            proceed = input("Re-ingest all documents? (y/n): ")
            if proceed.lower() != 'y':
                print("Using existing vector store")
                return stats
        
        print(f"📂 Ingesting from: {self.folder_69_path}")
        
        # Show cost estimate
        estimate = self.estimate_costs()
        print(f"\n💰 Estimated ingestion:")
        print(f"   Time: {estimate['ingestion']['time_minutes']:.1f} minutes")
        print(f"   Chunks: {estimate['ingestion']['chunks']:,}")
        
        proceed = input("\nProceed with ingestion? (y/n): ")
        if proceed.lower() != 'y':
            print("Cancelled.")
            return None
        
        stats = self.vector_store.ingest_documents(self.folder_69_path, resume=True)
        
        print(f"\n✅ Ingestion complete!")
        print(f"   Documents: {stats['total_documents']:,}")
        print(f"   Chunks: {stats['total_chunks']:,}\n")
        
        return stats
    
    def analyse_single_document(self,
                                doc_id: str,
                                doc_chunks: List[Dict]) -> DocumentScore:
        """
        Analyse one document with detailed explanations
        
        Args:
            doc_id: Document identifier
            doc_chunks: Retrieved chunks from this document
            
        Returns:
            DocumentScore with all details
        """
        # Get metadata
        metadata = self.doc_metadata.get(doc_id, {})
        document_name = metadata.get('document_name', 'Unknown')
        date = metadata.get('date', 'Unknown')
        
        # Build content from top chunks
        content = "\n\n---\n\n".join([
            f"[Chunk {i+1}]\n{chunk['text']}"
            for i, chunk in enumerate(doc_chunks[:5])  # Top 5 chunks
        ])
        
        # Generate analysis prompt
        prompt = self.prompts.detailed_document_analysis(
            doc_id=doc_id,
            document_name=document_name,
            date=date,
            content=content,
            claimant=self.claimant,
            respondent=self.respondent
        )
        
        try:
            # Call Claude with extended thinking
            response = self.claude.messages.create(
                model='claude-sonnet-4-20250514',
                max_tokens=12000,
                thinking={'type': 'enabled', 'budget_tokens': 8000},
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            # Extract analysis
            analysis = ""
            for block in response.content:
                if block.type == 'text':
                    analysis += block.text
            
            # Calculate cost
            cost_usd = (response.usage.input_tokens * 0.000003) + \
                      (response.usage.output_tokens * 0.000015)
            cost_gbp = cost_usd * 1.27
            self.total_cost_gbp += cost_gbp
            
            # Parse structured analysis
            score = self._parse_analysis(doc_id, analysis, metadata, cost_gbp)
            
            # Store in knowledge graph
            self.knowledge_graph.add_finding({
                'query': f'Document analysis: {doc_id}',
                'prompt_type': 'document_analysis',
                'analysis': analysis,
                'citations': [doc_id],
                'timestamp': datetime.now().isoformat()
            })
            
            return score
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            # Return minimal score on error
            return DocumentScore(
                doc_id=doc_id,
                filename=doc_chunks[0]['metadata'].get('filename', '') if doc_chunks else '',
                document_name=document_name,
                document_summary=f"Error during analysis: {str(e)}"
            )
    
    def _parse_analysis(self,
                       doc_id: str,
                       analysis: str,
                       metadata: Dict,
                       cost_gbp: float) -> DocumentScore:
        """Parse Claude's structured analysis into DocumentScore"""
        
        # Extract scores using regex
        smoking_match = re.search(r'SMOKING GUN SCORE:\s*(\d+(?:\.\d+)?)/10', analysis, re.IGNORECASE)
        smoking_score = float(smoking_match.group(1)) if smoking_match else 0.0
        
        conceal_match = re.search(r'CONCEALMENT SCORE:\s*(\d+(?:\.\d+)?)/10', analysis, re.IGNORECASE)
        conceal_score = float(conceal_match.group(1)) if conceal_match else 0.0
        
        contra_match = re.search(r'CONTRADICTION SCORE:\s*(\d+(?:\.\d+)?)/10', analysis, re.IGNORECASE)
        contra_score = float(contra_match.group(1)) if contra_match else 0.0
        
        overall_match = re.search(r'OVERALL RANKING:\s*(\d+(?:\.\d+)?)/10', analysis, re.IGNORECASE)
        overall_score = float(overall_match.group(1)) if overall_match else 0.0
        
        # Extract category
        category_match = re.search(r'CATEGORY:\s*\[?(CRITICAL|HIGH|MEDIUM|LOW)\]?', analysis, re.IGNORECASE)
        category = category_match.group(1).upper() if category_match else "MEDIUM"
        
        # Extract sections
        def extract_section(start_marker, end_marker=None):
            """Extract text between markers"""
            if end_marker:
                pattern = f"{start_marker}(.*?){end_marker}"
            else:
                pattern = f"{start_marker}(.*?)(?:═{{30,}}|━{{30,}}|$)"
            
            match = re.search(pattern, analysis, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else ""
        
        # Extract all sections
        doc_summary = extract_section(r"1\.\s*DOCUMENT SUMMARY", r"═{30,}")
        smoking_explanation = extract_section(r"SMOKING GUN SCORE.*?SCORE EXPLANATION:", r"═{30,}")
        conceal_explanation = extract_section(r"CONCEALMENT SCORE.*?SCORE EXPLANATION:", r"═{30,}")
        contra_explanation = extract_section(r"CONTRADICTION SCORE.*?SCORE EXPLANATION:", r"═{30,}")
        overall_explanation = extract_section(r"OVERALL RANKING.*?OVERALL EXPLANATION:", r"═{30,}")
        litigation_value = extract_section(r"6\.\s*LITIGATION VALUE", r"═{30,}")
        tactical_section = extract_section(r"7\.\s*RECOMMENDED TACTICAL USE", r"═{30,}")
        related_docs = extract_section(r"8\.\s*RELATED DOCUMENTS", r"━{30,}")
        
        # Extract key quotes
        key_quotes = re.findall(r'"([^"]{20,})"', analysis)
        
        # Extract cross-exam questions
        cross_exam = re.findall(r'Q\d*[:.]\s*"([^"]+)"', tactical_section)
        
        # Extract critical factors
        factors_match = re.findall(r'\d+\.\s*\[([^\]]+)\]', overall_explanation)
        
        return DocumentScore(
            doc_id=doc_id,
            filename=doc_id,
            document_name=metadata.get('document_name', ''),
            date=metadata.get('date', ''),
            pages=metadata.get('pages', ''),
            document_summary=doc_summary[:500],
            smoking_gun_score=smoking_score,
            concealment_score=conceal_score,
            contradiction_score=contra_score,
            overall_value=overall_score,
            category=category,
            smoking_gun_explanation=smoking_explanation[:1000],
            concealment_explanation=conceal_explanation[:1000],
            contradiction_explanation=contra_explanation[:1000],
            overall_ranking_explanation=overall_explanation[:1000],
            critical_factors=factors_match[:3],
            litigation_value=litigation_value[:1000],
            cross_exam_questions=cross_exam[:5],
            key_quotes=key_quotes[:5],
            related_documents=[related_docs] if related_docs else [],
            analysis_timestamp=datetime.now().isoformat(),
            cost_gbp=cost_gbp
        )
    
    def analyse_all_documents(self, sample_size: Optional[int] = None):
        """
        Analyse all documents in Folder 69 with detailed explanations
        
        Args:
            sample_size: If provided, only analyse N documents (for testing)
        """
        print(f"{'='*70}")
        print("DOCUMENT ANALYSIS")
        print(f"{'='*70}\n")
        
        stats = self.vector_store.get_stats()
        total_docs = stats.get('total_documents', 0)
        
        if total_docs == 0:
            print("❌ No documents in vector store!")
            print("💡 Run ingest_documents() first\n")
            return
        
        print(f"📚 Documents available: {total_docs:,}")
        
        if sample_size:
            print(f"🧪 SAMPLE MODE: Analysing {sample_size} documents for testing")
            total_docs = min(sample_size, total_docs)
        
        # Show cost estimate
        cost_estimate = total_docs * 0.35
        time_estimate = (total_docs * 90) / 60
        
        print(f"\n💰 Estimated cost: £{cost_estimate:.2f}")
        print(f"⏱️  Estimated time: {time_estimate:.1f} minutes ({time_estimate/60:.1f} hours)")
        
        proceed = input("\nProceed with analysis? (y/n): ")
        if proceed.lower() != 'y':
            print("Cancelled.")
            return
        
        # Get unique document IDs from vector store
        print("\n🔍 Identifying unique documents...")
        
        # Query broadly to get all documents
        sample_results = self.vector_store.search(
            query="document",
            n_results=min(2000, stats.get('total_chunks', 2000)),
            use_reranker=False
        )
        
        # Extract unique document IDs
        doc_ids_found = set()
        for result in sample_results:
            filename = result['metadata'].get('filename', '')
            if filename:
                # Extract doc ID (remove extension)
                doc_id = filename.rsplit('.', 1)[0]
                doc_ids_found.add(doc_id)
        
        doc_ids_list = sorted(list(doc_ids_found))[:total_docs]
        
        print(f"✅ Found {len(doc_ids_list)} unique documents to analyse\n")
        
        # Analyse each document
        print(f"{'='*70}")
        print("ANALYSING DOCUMENTS WITH DETAILED EXPLANATIONS")
        print(f"{'='*70}\n")
        
        for i, doc_id in enumerate(tqdm(doc_ids_list, desc="Analysing"), 1):
            # Get all chunks for this document using optimised search
            doc_chunks = self.vector_store.find_document_by_id(doc_id)
            
            if not doc_chunks:
                # Fallback to regular search
                doc_results = self.vector_store.search(
                    query=doc_id,
                    n_results=15,
                    use_reranker=False
                )
                doc_chunks = [r for r in doc_results if doc_id in r['metadata'].get('filename', '')]
            
            if not doc_chunks:
                continue
            
            # Analyse with full explanations
            score = self.analyse_single_document(doc_id, doc_chunks)
            self.document_scores.append(score)
            self.documents_analysed += 1
            
            # Show progress every 10 docs
            if i % 10 == 0:
                print(f"\n💰 Cost so far: £{self.total_cost_gbp:.2f}")
        
        # Sort by overall value
        self.document_scores.sort(key=lambda x: x.overall_value, reverse=True)
        
        print(f"\n{'='*70}")
        print("✅ ANALYSIS COMPLETE")
        print(f"{'='*70}")
        print(f"\nDocuments analysed: {self.documents_analysed}")
        print(f"Total cost: £{self.total_cost_gbp:.2f}\n")
    
    def export_detailed_excel(self) -> Path:
        """Export complete analysis to Excel with all explanations"""
        
        print(f"{'='*70}")
        print("EXPORTING DETAILED EXCEL")
        print(f"{'='*70}\n")
        
        if not self.document_scores:
            print("❌ No scores to export!")
            return None
        
        # Prepare data for Excel
        excel_data = []
        
        for i, score in enumerate(self.document_scores, 1):
            excel_data.append({
                'Rank': i,
                'Doc_ID': score.doc_id,
                'Document_Name': score.document_name,
                'Date': score.date,
                'Pages': score.pages,
                'Document_Summary': score.document_summary,
                'Overall_Value': f"{score.overall_value:.1f}",
                'Category': score.category,
                'Smoking_Gun_Score': f"{score.smoking_gun_score:.1f}",
                'Concealment_Score': f"{score.concealment_score:.1f}",
                'Contradiction_Score': f"{score.contradiction_score:.1f}",
                'Smoking_Gun_Explanation': score.smoking_gun_explanation,
                'Concealment_Explanation': score.concealment_explanation,
                'Contradiction_Explanation': score.contradiction_explanation,
                'Overall_Ranking_Explanation': score.overall_ranking_explanation,
                'Critical_Factors': '\n'.join(score.critical_factors),
                'Litigation_Value': score.litigation_value,
                'Cross_Exam_Questions': '\n'.join(score.cross_exam_questions),
                'Key_Quotes': '\n'.join([f'"{q}"' for q in score.key_quotes]),
                'Related_Documents': '\n'.join(score.related_documents),
                'Analysis_Cost_GBP': f"£{score.cost_gbp:.4f}",
                'Analysis_Timestamp': score.analysis_timestamp
            })
        
        df = pd.DataFrame(excel_data)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.results_dir / f"Folder_69_Analysis_{timestamp}.xlsx"
        
        print(f"💾 Saving to: {output_file.name}")
        
        # Export with formatting
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Analysis', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['Analysis']
            
            # Define formats
            header_fmt = workbook.add_format({
                'bold': True,
                'bg_color': '#4472C4',
                'font_color': 'white',
                'border': 1,
                'text_wrap': True,
                'valign': 'vcenter'
            })
            
            critical_fmt = workbook.add_format({'bg_color': '#FF0000', 'font_color': 'white', 'bold': True})
            high_fmt = workbook.add_format({'bg_color': '#FFC000'})
            medium_fmt = workbook.add_format({'bg_color': '#FFFF00'})
            low_fmt = workbook.add_format({'bg_color': '#92D050'})
            
            wrap_fmt = workbook.add_format({'text_wrap': True, 'valign': 'top'})
            
            # Apply header format
            for col_num, value in enumerate(df.columns):
                worksheet.write(0, col_num, value, header_fmt)
            
            # Set column widths
            column_widths = {
                'Rank': 6, 'Doc_ID': 15, 'Document_Name': 45, 'Date': 12, 'Pages': 8,
                'Document_Summary': 70, 'Overall_Value': 12, 'Category': 12,
                'Smoking_Gun_Score': 15, 'Concealment_Score': 15, 'Contradiction_Score': 15,
                'Smoking_Gun_Explanation': 80, 'Concealment_Explanation': 80,
                'Contradiction_Explanation': 80, 'Overall_Ranking_Explanation': 80,
                'Critical_Factors': 60, 'Litigation_Value': 80, 'Cross_Exam_Questions': 70,
                'Key_Quotes': 70, 'Related_Documents': 40, 'Analysis_Cost_GBP': 15,
                'Analysis_Timestamp': 20
            }
            
            for col_num, col_name in enumerate(df.columns):
                width = column_widths.get(col_name, 20)
                worksheet.set_column(col_num, col_num, width)
            
            # Apply category colours
            cat_col = df.columns.get_loc('Category')
            for row_num, cat in enumerate(df['Category'], start=1):
                fmt = {'CRITICAL': critical_fmt, 'HIGH': high_fmt, 'MEDIUM': medium_fmt, 'LOW': low_fmt}.get(cat, medium_fmt)
                worksheet.write(row_num, cat_col, cat, fmt)
            
            # Wrap text in explanation columns
            wrap_columns = [
                'Document_Summary', 'Smoking_Gun_Explanation', 'Concealment_Explanation',
                'Contradiction_Explanation', 'Overall_Ranking_Explanation', 'Critical_Factors',
                'Litigation_Value', 'Cross_Exam_Questions', 'Key_Quotes', 'Related_Documents'
            ]
            
            for col_name in wrap_columns:
                if col_name in df.columns:
                    col_num = df.columns.get_loc(col_name)
                    for row_num in range(1, len(df) + 1):
                        cell_value = df.iloc[row_num - 1][col_name]
                        worksheet.write(row_num, col_num, cell_value, wrap_fmt)
        
        print(f"✅ Excel file created!\n")
        
        # Summary statistics
        critical_count = len([s for s in self.document_scores if s.category == 'CRITICAL'])
        high_count = len([s for s in self.document_scores if s.category == 'HIGH'])
        medium_count = len([s for s in self.document_scores if s.category == 'MEDIUM'])
        low_count = len([s for s in self.document_scores if s.category == 'LOW'])
        
        print(f"📈 Summary Statistics:")
        print(f"   CRITICAL: {critical_count} ({critical_count/len(df)*100:.1f}%)")
        print(f"   HIGH: {high_count} ({high_count/len(df)*100:.1f}%)")
        print(f"   MEDIUM: {medium_count} ({medium_count/len(df)*100:.1f}%)")
        print(f"   LOW: {low_count} ({low_count/len(df)*100:.1f}%)\n")
        
        return output_file
    
    def generate_executive_summary(self) -> str:
        """Generate executive summary for legal team"""
        
        if not self.document_scores:
            return "No documents analysed yet."
        
        print(f"{'='*70}")
        print("GENERATING EXECUTIVE SUMMARY")
        print(f"{'='*70}\n")
        
        # Get top documents
        critical_docs = [s for s in self.document_scores if s.category == 'CRITICAL']
        high_docs = [s for s in self.document_scores if s.category == 'HIGH']
        
        # Build context for summary
        summary_context = f"""
FOLDER 69 LATE DISCLOSURE REVIEW - EXECUTIVE SUMMARY

Total Documents Analysed: {len(self.document_scores):,}
Analysis Cost: £{self.total_cost_gbp:.2f}

CRITICAL DOCUMENTS: {len(critical_docs)}
HIGH-VALUE DOCUMENTS: {len(high_docs)}

TOP 10 MOST CRITICAL DOCUMENTS:
"""
        
        for i, doc in enumerate(critical_docs[:10], 1):
            summary_context += f"\n{i}. {doc.document_name or doc.doc_id}"
            summary_context += f"\n   Score: {doc.overall_value:.1f}/10"
            summary_context += f"\n   Summary: {doc.document_summary[:200]}..."
            summary_context += f"\n   Key Quote: {doc.key_quotes[0] if doc.key_quotes else 'N/A'}"
            summary_context += "\n"
        
        # Generate summary with Claude
        prompt = f"""You are a senior litigation partner. Generate an executive summary.

{summary_context}

Provide:

1. WAS FOLDER 69 DISCLOSURE WORTH FIGHTING FOR?
   - Overall assessment (High Value / Medium Value / Low Value)
   - Key smoking guns discovered
   - Strategic impact on case

2. TOP 5 CRITICAL FINDINGS
   - Most important discoveries
   - How they help {self.claimant}'s case

3. RECOMMENDED NEXT STEPS
   - Immediate actions for legal team
   - Documents requiring deep review
   - Litigation strategy adjustments

4. SETTLEMENT IMPACT
   - How this affects leverage
   - Recommended settlement approach

British English. Be concise but specific. 2-3 pages max."""
        
        try:
            response = self.claude.messages.create(
                model='claude-sonnet-4-20250514',
                max_tokens=8000,
                thinking={'type': 'enabled', 'budget_tokens': 5000},
                messages=[{'role': 'user', 'content': prompt}]
            )
            
            summary = ""
            for block in response.content:
                if block.type == 'text':
                    summary += block.text
            
            # Save summary
            summary_file = self.results_dir / f"Executive_Summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"# Folder 69 Late Disclosure Review\n\n")
                f.write(f"**Date**: {datetime.now().strftime('%d %B %Y')}\n")
                f.write(f"**Total Cost**: £{self.total_cost_gbp:.2f}\n\n")
                f.write("---\n\n")
                f.write(summary)
            
            print(f"✅ Executive summary saved: {summary_file.name}\n")
            
            return summary
            
        except Exception as e:
            print(f"❌ Error generating summary: {e}")
            return "Error generating summary"
    
    def run_complete_review(self, sample_size: Optional[int] = None):
        """
        Run complete review pipeline
        
        Args:
            sample_size: If provided, only analyse N documents (for testing)
        """
        print("\n" + "="*70)
        print("FOLDER 69 COMPLETE REVIEW")
        print("="*70)
        print("\nThis system provides:")
        print("  ✓ Document validation")
        print("  ✓ Cost estimation")
        print("  ✓ Checkpoint recovery")
        print("  ✓ Detailed scoring with explanations")
        print("  ✓ Litigation recommendations")
        print("  ✓ Complete Excel export\n")
        
        # Step 0: Cost estimation
        print("━"*70)
        print("STEP 0: COST ESTIMATION")
        print("━"*70 + "\n")
        
        estimate = self.estimate_costs()
        print(f"📊 Complete Analysis Estimate:")
        print(f"   Documents: {estimate['documents']:,}")
        print(f"   Total cost: £{estimate['total']['cost_gbp']:.2f}")
        print(f"   Total time: {estimate['total']['time_hours']:.1f} hours")
        print(f"\n   Breakdown:")
        print(f"     Ingestion: £{estimate['ingestion']['cost_gbp']:.2f} ({estimate['ingestion']['time_minutes']:.0f} mins)")
        print(f"     Analysis: £{estimate['analysis']['cost_gbp']:.2f} ({estimate['analysis']['time_minutes']:.0f} mins)")
        
        proceed = input("\nProceed? (y/n): ")
        if proceed.lower() != 'y':
            print("Cancelled.")
            return
        
        # Step 1: Validation
        print("\n" + "━"*70)
        print("STEP 1: DOCUMENT VALIDATION")
        print("━"*70 + "\n")
        
        valid, invalid, invalid_files = self.validate_documents()
        
        if invalid > 10:
            print(f"\n⚠️  {invalid} invalid files found. Review and fix before proceeding.")
            return
        
        # Step 2: Ingest documents
        print("\n" + "━"*70)
        print("STEP 2: DOCUMENT INGESTION")
        print("━"*70 + "\n")
        self.ingest_documents()
        
        # Step 3: Analyse all documents
        print("\n" + "━"*70)
        print("STEP 3: DETAILED DOCUMENT ANALYSIS")
        print("━"*70 + "\n")
        self.analyse_all_documents(sample_size=sample_size)
        
        # Step 4: Export to Excel
        print("\n" + "━"*70)
        print("STEP 4: EXCEL EXPORT")
        print("━"*70 + "\n")
        excel_file = self.export_detailed_excel()
        
        # Step 5: Executive summary
        print("\n" + "━"*70)
        print("STEP 5: EXECUTIVE SUMMARY")
        print("━"*70 + "\n")
        summary = self.generate_executive_summary()
        
        # Final output
        print("\n" + "="*70)
        print("✅ COMPLETE REVIEW FINISHED")
        print("="*70)
        print(f"\n📊 Results:")
        print(f"   Documents analysed: {self.documents_analysed}")
        print(f"   Total cost: £{self.total_cost_gbp:.2f}")
        print(f"\n📂 Output files:")
        print(f"   Excel: {excel_file}")
        print(f"   Summary: {self.results_dir}/Executive_Summary_*.md")
        print(f"\n💡 Next Steps:")
        print("   1. Open Excel file and filter by Category=CRITICAL")
        print("   2. Read detailed explanations for top documents")
        print("   3. Review executive summary")
        print("   4. Use litigation recommendations in your strategy\n")