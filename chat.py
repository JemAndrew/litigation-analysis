#!/usr/bin/env python3
"""
Litigation AI - Hybrid Interactive Chat
Foundation + Interactive Forensics Architecture

MAIN ENTRY POINT for multi-case litigation analysis

British English throughout.
"""

import os
import sys
from pathlib import Path
import logging
from datetime import datetime

# Setup paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Imports
from src.core.case_manager import CaseManager
from src.intelligence.vector_store import IntelligentVectorStore
from src.intelligence.query_engine import QueryEngine
from src.intelligence.knowledge_graph import CumulativeKnowledgeGraph
from anthropic import Anthropic


class LitigationAI:
    """
    Hybrid litigation AI system
    
    Phase 1: Foundation (one-time setup)
    Phase 2: Interactive forensics (ongoing queries)
    """
    
    def __init__(self):
        """Initialise litigation AI system"""
        self.cases_root = project_root / "cases"
        self.case_manager = CaseManager(self.cases_root)
        
        # Components (initialised per case)
        self.vector_store = None
        self.query_engine = None
        self.knowledge_graph = None
        self.claude_client = None
        
        # State
        self.active_case_dir = None
        self.case_metadata = None
        
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║             LITIGATION AI - HYBRID FORENSIC SYSTEM                   ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
        print("\n✨ Foundation + Interactive Forensics Architecture")
        print("💡 Type '/help' for commands\n")
    
    def start(self):
        """Start interactive chat"""
        
        # Check API key
        if not os.getenv('ANTHROPIC_API_KEY'):
            print("\n❌ ERROR: ANTHROPIC_API_KEY not set!")
            print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
            return
        
        # Initialize Claude client
        self.claude_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        # Select or create case
        if not self.case_manager.active_case_id:
            self._case_selection()
        
        if not self.case_manager.active_case_id:
            print("No case selected. Exiting.")
            return
        
        # Load case
        self._load_active_case()
        
        print(f"\n✅ Ready! Case: {self.case_metadata['case_name']}")
        print(f"💬 Ask questions or use commands (e.g., '/help')\n")
        
        # Main loop
        while True:
            try:
                user_input = input("\n📝 You: ").strip()
                
                if not user_input:
                    continue
                
                # Commands
                if user_input.startswith('/'):
                    self._handle_command(user_input)
                    continue
                
                # Natural language queries
                self._handle_query(user_input)
            
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                self._show_session_summary()
                break
            except Exception as e:
                logger.error(f"Error: {e}", exc_info=True)
                print(f"\n❌ Error: {e}")
    
    def _load_active_case(self):
        """Load active case components"""
        self.active_case_dir = self.case_manager.get_active_case()
        self.case_metadata = self.case_manager.cases_index['cases'][self.case_manager.active_case_id]
        
        print(f"\n🔧 Loading case: {self.case_metadata['case_name']}...")
        
        # Initialize vector store
        print("📚 Loading vector store...")
        self.vector_store = IntelligentVectorStore(
            case_dir=self.active_case_dir,
            cohere_api_key=os.getenv('COHERE_API_KEY')  # Optional
        )
        
        # Initialize knowledge graph
        print("🧠 Loading knowledge graph...")
        self.knowledge_graph = CumulativeKnowledgeGraph(self.active_case_dir)
        
        # Initialize query engine
        print("🔍 Initializing query engine...")
        self.query_engine = QueryEngine(
            vector_store=self.vector_store,
            claude_client=self.claude_client,
            case_context=self.case_metadata,
            knowledge_graph=self.knowledge_graph
        )
        
        print("✅ Case loaded successfully!")
        
        # Show stats
        vs_stats = self.vector_store.get_stats()
        kg_stats = self.knowledge_graph.get_stats()
        
        print(f"\n📊 Case Statistics:")
        print(f"   Documents indexed: {vs_stats.get('total_documents', 0)}")
        print(f"   Document chunks: {vs_stats.get('total_chunks', 0)}")
        print(f"   Prior queries: {kg_stats.get('total_queries', 0)}")
        print(f"   Smoking guns found: {kg_stats.get('smoking_guns', 0)}")
        print(f"   Contradictions found: {kg_stats.get('contradictions', 0)}")
    
    def _case_selection(self):
        """Interactive case selection"""
        cases = self.case_manager.list_cases()
        
        if not cases:
            print("\n📁 No cases found. Let's create one.\n")
            self._create_new_case()
            return
        
        print("\n📁 Available cases:")
        for i, case in enumerate(cases, 1):
            status = "✅" if case['ingestion_complete'] else "⏳"
            print(f"  {i}. {status} {case['case_name']}")
            print(f"      {case['claimant']} v {case['respondent']}")
            print(f"      Docs: {case['document_count']} | Last accessed: {case.get('last_accessed', 'Never')[:10]}")
        
        print(f"  {len(cases)+1}. 🆕 Create new case")
        
        try:
            choice = int(input("\n🔢 Select case: "))
            
            if 1 <= choice <= len(cases):
                case_id = cases[choice-1]['case_id']
                self.case_manager.switch_case(case_id)
            elif choice == len(cases) + 1:
                self._create_new_case()
        except:
            print("❌ Invalid choice")
    
    def _create_new_case(self):
        """Create new case interactively"""
        print("\n" + "="*70)
        print("CREATE NEW CASE")
        print("="*70)
        
        case_name = input("\n📋 Case name (e.g., 'Lismore v Process Holdings'): ").strip()
        case_id = input("🔑 Case ID (e.g., 'lismore_v_ph'): ").strip()
        claimant = input("👤 Claimant name: ").strip()
        respondent = input("🎯 Respondent name: ").strip()
        tribunal = input("🏛️  Tribunal (default: LCIA): ").strip() or "LCIA"
        
        # Get allegations
        print("\n📝 Key allegations (one per line, empty line to finish):")
        allegations = []
        while True:
            allegation = input("   - ").strip()
            if not allegation:
                break
            allegations.append(allegation)
        
        allegations_text = "\n".join([f"- {a}" for a in allegations]) if allegations else "Not specified"
        
        # Create case
        case_dir = self.case_manager.create_case(
            case_id=case_id,
            case_name=case_name,
            claimant=claimant,
            respondent=respondent,
            tribunal=tribunal
        )
        
        # Update metadata with allegations
        self.case_manager.update_metadata(case_id, {
            'allegations': allegations_text
        })
        
        self.case_manager.switch_case(case_id)
        
        print(f"\n✅ Case created!")
        print(f"\n📂 Add documents to: {case_dir / 'documents'}")
        print(f"💡 Then run: /ingest\n")
        
        input("Press Enter to continue...")
    
    def _handle_query(self, query: str):
        """Handle natural language query"""
        
        # Check if documents ingested
        if self.vector_store.get_stats().get('total_chunks', 0) == 0:
            print("\n⚠️  No documents ingested yet!")
            print("💡 Run '/ingest' first to load documents into vector store.")
            return
        
        print(f"\n🔍 Analysing... (this may take 30-60 seconds)")
        print(f"🧠 Using extended thinking for deep analysis...")
        
        try:
            # Execute query
            result = self.query_engine.query(
                query=query,
                use_extended_thinking=True,
                n_results=15
            )
            
            # Display result
            print(f"\n{'='*70}")
            print(f"🤖 ANALYSIS")
            print(f"{'='*70}\n")
            print(result.analysis)
            print(f"\n{'='*70}")
            
            # Show metadata
            print(f"\n📊 Query Statistics:")
            print(f"   Cost: £{result.cost_gbp:.4f}")
            print(f"   Documents retrieved: {len(result.retrieved_docs)}")
            print(f"   Citations validated: {len(result.citations)}")
            print(f"   Extended thinking: {'Yes' if result.thinking_used else 'No'}")
            
            # Show session stats
            stats = self.query_engine.get_stats()
            print(f"\n💰 Session Statistics:")
            print(f"   Total queries: {stats['total_queries']}")
            print(f"   Total cost: £{stats['total_cost_gbp']:.2f}")
            print(f"   Avg cost/query: £{stats['avg_cost_per_query']:.4f}")
            
        except Exception as e:
            logger.error(f"Query error: {e}", exc_info=True)
            print(f"\n❌ Query failed: {e}")
    
    def _handle_command(self, command: str):
        """Handle chat commands"""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd == '/help':
            self._show_help()
        
        elif cmd == '/cases':
            self._list_cases()
        
        elif cmd == '/switch':
            self._case_selection()
            if self.case_manager.active_case_id:
                self._load_active_case()
        
        elif cmd == '/new':
            self._create_new_case()
        
        elif cmd == '/ingest':
            self._ingest_documents()
        
        elif cmd == '/status':
            self._show_status()
        
        elif cmd == '/stats':
            self._show_stats()
        
        elif cmd == '/export':
            self._export_knowledge_graph()
        
        elif cmd == '/cost':
            self._show_costs()
        
        elif cmd == '/quit' or cmd == '/exit':
            print("\n👋 Goodbye!")
            self._show_session_summary()
            sys.exit(0)
        
        else:
            print(f"❌ Unknown command: {cmd}")
            print("💡 Type '/help' for available commands")
    
    def _show_help(self):
        """Show help message"""
        print("""
╔══════════════════════════════════════════════════════════════════════╗
║                         COMMANDS                                     ║
╚══════════════════════════════════════════════════════════════════════╝

📁 CASE MANAGEMENT:
   /cases          List all cases
   /switch         Switch to different case
   /new            Create new case
   /status         Show current case status

📚 DOCUMENT MANAGEMENT:
   /ingest         Ingest documents into vector store
   /stats          Show detailed statistics

💰 COST TRACKING:
   /cost           Show cost breakdown

📊 EXPORT:
   /export         Export knowledge graph summary

🔧 SYSTEM:
   /help           Show this message
   /quit           Exit (or Ctrl+C)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💬 NATURAL LANGUAGE QUERIES (Examples):

   Find smoking guns in late disclosure documents
   Build timeline of key events
   Find contradictions between witness statements and emails
   Generate cross-examination questions for [witness name]
   Draft argument on breach of warranty 12.3
   Analyse settlement leverage

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 The system automatically:
   ✓ Expands your query for better retrieval
   ✓ Routes to appropriate prompt type
   ✓ Uses extended thinking for deep analysis
   ✓ Validates all document citations
   ✓ Stores findings in knowledge graph
   ✓ Tracks costs per query
        """)
    
    def _list_cases(self):
        """List all cases"""
        cases = self.case_manager.list_cases()
        
        print(f"\n📁 All Cases ({len(cases)}):")
        for i, case in enumerate(cases, 1):
            status = "✅" if case['ingestion_complete'] else "⏳"
            active = "👉" if case['case_id'] == self.case_manager.active_case_id else "  "
            
            print(f"\n{active} {i}. {status} {case['case_name']}")
            print(f"      ID: {case['case_id']}")
            print(f"      {case['claimant']} v {case['respondent']}")
            print(f"      Tribunal: {case['tribunal']}")
            print(f"      Documents: {case['document_count']}")
            print(f"      Created: {case.get('created_date', 'Unknown')[:10]}")
    
    def _ingest_documents(self):
        """Ingest documents into vector store"""
        print(f"\n📂 Ingesting documents from: {self.active_case_dir / 'documents'}")
        print("⏱️  This may take 10-30 minutes depending on document count...")
        print("💡 Legal-BERT is processing documents with semantic understanding\n")
        
        try:
            documents_dir = self.active_case_dir / "documents"
            
            if not documents_dir.exists() or not any(documents_dir.rglob('*')):
                print("❌ No documents found!")
                print(f"💡 Add documents to: {documents_dir}")
                return
            
            # Ingest
            stats = self.vector_store.ingest_documents(documents_dir)
            
            # Update metadata
            self.case_manager.update_metadata(
                self.case_manager.active_case_id,
                {
                    'document_count': stats['total_documents'],
                    'ingestion_complete': True,
                    'ingestion_date': datetime.now().isoformat()
                }
            )
            
            print(f"\n✅ Ingestion complete!")
            print(f"   Documents: {stats['total_documents']:,}")
            print(f"   Chunks: {stats['total_chunks']:,}")
            print(f"\n💡 You can now ask questions about the documents!")
            
        except Exception as e:
            logger.error(f"Ingestion error: {e}", exc_info=True)
            print(f"\n❌ Ingestion failed: {e}")
    
    def _show_status(self):
        """Show current case status"""
        if not self.case_metadata:
            print("❌ No case loaded")
            return
        
        print(f"\n╔══════════════════════════════════════════════════════════════════════╗")
        print(f"║                      CASE STATUS                                     ║")
        print(f"╚══════════════════════════════════════════════════════════════════════╝")
        print(f"\n📋 Case: {self.case_metadata['case_name']}")
        print(f"🔑 ID: {self.case_metadata['case_id']}")
        print(f"👤 Claimant: {self.case_metadata['claimant']}")
        print(f"🎯 Respondent: {self.case_metadata['respondent']}")
        print(f"🏛️  Tribunal: {self.case_metadata['tribunal']}")
        print(f"\n📂 Documents: {self.case_metadata['document_count']}")
        
        ingestion_status = "✅ Complete" if self.case_metadata['ingestion_complete'] else "⏳ Pending"
        print(f"📚 Ingestion: {ingestion_status}")
        
        if self.case_metadata.get('ingestion_date'):
            print(f"📅 Ingested: {self.case_metadata['ingestion_date'][:10]}")
        
        print(f"\n📝 Key Allegations:")
        print(f"{self.case_metadata.get('allegations', 'Not specified')}")
    
    def _show_stats(self):
        """Show detailed statistics"""
        print(f"\n╔══════════════════════════════════════════════════════════════════════╗")
        print(f"║                    DETAILED STATISTICS                               ║")
        print(f"╚══════════════════════════════════════════════════════════════════════╝")
        
        # Vector store stats
        if self.vector_store:
            vs_stats = self.vector_store.get_stats()
            print(f"\n📚 Vector Store:")
            print(f"   Documents: {vs_stats.get('total_documents', 0):,}")
            print(f"   Chunks: {vs_stats.get('total_chunks', 0):,}")
            print(f"   ChromaDB entries: {vs_stats.get('chroma_count', 0):,}")
            print(f"   BM25 index size: {vs_stats.get('bm25_count', 0):,}")
        
        # Knowledge graph stats
        if self.knowledge_graph:
            kg_stats = self.knowledge_graph.get_stats()
            print(f"\n🧠 Knowledge Graph:")
            print(f"   Total queries: {kg_stats.get('total_queries', 0)}")
            print(f"   Smoking guns: {kg_stats.get('smoking_guns', 0)}")
            print(f"   Contradictions: {kg_stats.get('contradictions', 0)}")
            print(f"   Evidence chains: {kg_stats.get('evidence_chains', 0)}")
            print(f"   Cross-exam sets: {kg_stats.get('cross_exam_sets', 0)}")
            print(f"   Legal arguments: {kg_stats.get('legal_arguments', 0)}")
            print(f"   Timelines: {kg_stats.get('timelines', 0)}")
        
        # Query engine stats
        if self.query_engine:
            qe_stats = self.query_engine.get_stats()
            print(f"\n🔍 Query Engine:")
            print(f"   Total queries: {qe_stats.get('total_queries', 0)}")
            print(f"   Total cost: £{qe_stats.get('total_cost_gbp', 0):.2f}")
            print(f"   Avg cost/query: £{qe_stats.get('avg_cost_per_query', 0):.4f}")
    
    def _show_costs(self):
        """Show cost breakdown"""
        if not self.query_engine:
            print("❌ No query engine loaded")
            return
        
        stats = self.query_engine.get_stats()
        
        print(f"\n╔══════════════════════════════════════════════════════════════════════╗")
        print(f"║                      COST ANALYSIS                                   ║")
        print(f"╚══════════════════════════════════════════════════════════════════════╝")
        print(f"\n💰 Session Costs:")
        print(f"   Total queries: {stats['total_queries']}")
        print(f"   Total cost: £{stats['total_cost_gbp']:.2f}")
        print(f"   Average per query: £{stats['avg_cost_per_query']:.4f}")
        
        # Projections
        if stats['total_queries'] > 0:
            print(f"\n📊 Projections:")
            print(f"   Cost for 50 queries: £{stats['avg_cost_per_query'] * 50:.2f}")
            print(f"   Cost for 100 queries: £{stats['avg_cost_per_query'] * 100:.2f}")
            
            print(f"\n💡 Comparison:")
            print(f"   Harvey AI (1 month): ~£800-1,000")
            print(f"   Your system (100 queries): ~£{stats['avg_cost_per_query'] * 100:.2f}")
            print(f"   Savings: ~£{800 - (stats['avg_cost_per_query'] * 100):.2f} ({((800 - stats['avg_cost_per_query'] * 100) / 800 * 100):.0f}%)")
    
    def _export_knowledge_graph(self):
        """Export knowledge graph summary"""
        if not self.knowledge_graph:
            print("❌ No knowledge graph loaded")
            return
        
        output_path = self.active_case_dir / "analysis" / f"knowledge_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            self.knowledge_graph.export_summary(output_path)
            print(f"\n✅ Knowledge graph exported to:")
            print(f"   {output_path}")
        except Exception as e:
            print(f"\n❌ Export failed: {e}")
    
    def _show_session_summary(self):
        """Show session summary on exit"""
        if self.query_engine:
            stats = self.query_engine.get_stats()
            print(f"\n📊 Session Summary:")
            print(f"   Queries: {stats['total_queries']}")
            print(f"   Cost: £{stats['total_cost_gbp']:.2f}")


def main():
    """Main entry point"""
    try:
        app = LitigationAI()
        app.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()