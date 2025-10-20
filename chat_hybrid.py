#!/usr/bin/env python3
"""
Litigation AI - Hybrid Interactive Chat
Foundation + Interactive Forensics Architecture

British English throughout
"""

import os
import sys
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

from src.core.case_manager import CaseManager
from src.intelligence.vector_store import VectorStore
from src.intelligence.query_engine import QueryEngine, SimpleKnowledgeGraph


class HybridLitigationChat:
    """
    Hybrid architecture chat interface:
    - Foundation: One-time document ingestion + case basics
    - Interactive: On-demand forensic queries with cumulative learning
    """
    
    def __init__(self):
        self.cases_root = project_root / "cases"
        self.case_manager = CaseManager(self.cases_root)
        self.vector_store = None
        self.query_engine = None
        self.knowledge_graph = None
        
        print("=" * 70)
        print("LITIGATION AI - HYBRID FORENSICS SYSTEM")
        print("=" * 70)
        print("\nArchitecture: Foundation + Interactive Queries")
        print("Cost: £20-30 setup, then £0.05-0.50 per query\n")
    
    def start(self):
        """Main entry point"""
        
        # Check API key
        if not os.getenv('ANTHROPIC_API_KEY'):
            print("\n❌ ERROR: ANTHROPIC_API_KEY not set!")
            print("Set it with:")
            print("  Windows: $env:ANTHROPIC_API_KEY='your-key'")
            print("  Linux/Mac: export ANTHROPIC_API_KEY='your-key'")
            return
        
        # Select or create case
        if not self.case_manager.active_case_id:
            self._case_selection()
        
        if not self.case_manager.active_case_id:
            print("No case selected. Exiting.")
            return
        
        # Load case infrastructure
        self._load_case_infrastructure()
        
        print(f"\n✅ Ready! Type '/help' for commands or ask questions naturally.\n")
        print("Example queries:")
        print("  • Find evidence PH concealed liabilities")
        print("  • Build timeline of key events")
        print("  • Find contradictions in CFO testimony")
        print("  • Draft argument on Warranty 12.3 breach")
        print("  • Analyse settlement position\n")
        
        # Main loop
        while True:
            try:
                user_input = input("You: ").strip()
                
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
                self._print_session_stats()
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
                import traceback
                traceback.print_exc()
    
    def _case_selection(self):
        """Interactive case selection or creation"""
        
        cases = self.case_manager.list_cases()
        
        if not cases:
            print("\nNo cases found. Let's create your first case.\n")
            self._create_new_case()
            return
        
        print("\n📁 Available cases:")
        for i, case in enumerate(cases, 1):
            status = "✅" if case.get('ingestion_complete', False) else "⏳"
            doc_count = case.get('document_count', 0)
            
            print(f"  {i}. {status} {case['case_name']}")
            print(f"      {case['claimant']} v {case['respondent']}")
            print(f"      Documents: {doc_count} | Last: {case.get('last_accessed', 'Never')[:10]}")
        
        print(f"\n  {len(cases)+1}. ➕ Create new case")
        
        try:
            choice = int(input("\nSelect case (number): "))
            
            if 1 <= choice <= len(cases):
                case_id = cases[choice-1]['case_id']
                self.case_manager.switch_case(case_id)
            elif choice == len(cases) + 1:
                self._create_new_case()
            else:
                print("Invalid choice")
                
        except ValueError:
            print("Invalid input")
    
    def _create_new_case(self):
        """Create new case interactively"""
        
        print("\n" + "="*70)
        print("CREATE NEW CASE")
        print("="*70)
        
        print("\nExample: Lismore v Process Holdings")
        case_name = input("\nCase name: ").strip()
        
        print("\nExample: lismore_v_ph (lowercase, underscores)")
        case_id = input("Case ID: ").strip()
        
        claimant = input("Claimant name: ").strip()
        respondent = input("Respondent name: ").strip()
        
        print("\nTribunal options: LCIA, ICC, ICSID, HKIAC, SIAC")
        tribunal = input("Tribunal (default: LCIA): ").strip() or "LCIA"
        
        print("\nKey allegations (brief summary):")
        allegations = input("  ").strip()
        
        # Create case
        case_dir = self.case_manager.create_case(
            case_id=case_id,
            case_name=case_name,
            claimant=claimant,
            respondent=respondent,
            tribunal=tribunal,
            allegations=allegations
        )
        
        self.case_manager.switch_case(case_id)
        
        print(f"\n✅ Case created!")
        print(f"\n📂 Next steps:")
        print(f"   1. Add documents to: {case_dir / 'documents'}")
        print(f"   2. Run /ingest to load into vector store")
        print(f"   3. Start querying!\n")
        
        input("Press Enter to continue...")
    
    def _load_case_infrastructure(self):
        """Load vector store, query engine, knowledge graph for active case"""
        
        case_dir = self.case_manager.get_active_case()
        case_metadata = self.case_manager.cases_index['cases'][self.case_manager.active_case_id]
        
        print(f"\n🔧 Loading case infrastructure...")
        
        # Load vector store
        print("   • Loading vector store...")
        self.vector_store = VectorStore(case_dir=case_dir)
        
        # Load knowledge graph
        print("   • Initialising knowledge graph...")
        self.knowledge_graph = SimpleKnowledgeGraph(case_dir=case_dir)
        
        # Create query engine
        print("   • Creating query engine...")
        self.query_engine = QueryEngine(
            vector_store=self.vector_store,
            case_metadata=case_metadata,
            knowledge_graph=self.knowledge_graph
        )
        
        print("   ✅ Infrastructure ready")
        
        # Show case stats
        stats = self.vector_store.get_stats()
        kg_stats = self.knowledge_graph.get_stats()
        
        print(f"\n📊 Case Status:")
        print(f"   • Documents: {stats.get('total_documents', 0):,}")
        print(f"   • Chunks: {stats.get('total_chunks', 0):,}")
        print(f"   • Knowledge findings: {kg_stats.get('total_findings', 0)}")
    
    def _handle_query(self, query: str):
        """Handle natural language query"""
        
        # Check if documents ingested
        stats = self.vector_store.get_stats()
        if stats.get('total_chunks', 0) == 0:
            print("\n⚠️  No documents ingested yet. Run /ingest first!\n")
            return
        
        # Estimate cost
        estimated_cost = 0.30
        print(f"\n💰 Estimated cost: £{estimated_cost:.2f}")
        
        # Process query
        print("🔍 Searching documents...")
        result = self.query_engine.query(query, use_extended_thinking=True)
        
        # Display response
        print("\n" + "="*70)
        print("AI ANALYSIS:")
        print("="*70 + "\n")
        print(result['response'])
        print("\n" + "="*70)
        
        # Show metadata
        print(f"\n📊 Query Metadata:")
        print(f"   • Prompt type: {result['prompt_type']}")
        print(f"   • Documents retrieved: {len(result['retrieved_docs'])}")
        print(f"   • Citations found: {len(result['citations'])}")
        print(f"   • Cost: £{result['cost_gbp']:.4f}")
        
        if result['citation_validation']['invalid_citations']:
            print(f"   ⚠️  Possible hallucinations: {result['citation_validation']['invalid_citations']}")
        
        print()
    
    def _handle_command(self, command: str):
        """Handle chat commands"""
        
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        
        if cmd == '/help':
            print("""
COMMANDS:
  /help            Show this message
  /cases           List all cases
  /switch          Switch to different case
  /new             Create new case
  /status          Show case statistics
  /ingest          Ingest documents (one-time setup)
  /docs            List documents
  /kg              Show knowledge graph findings
  /cost            Show cost statistics
  /quit            Exit

EXAMPLE QUERIES:
  • Find smoking guns in late disclosure
  • Build timeline of concealment
  • Find contradictions in CFO testimony
  • Draft argument on Warranty 12.3 breach
  • Generate cross-exam questions for [name]
  • Analyse settlement position
            """)
        
        elif cmd == '/cases':
            cases = self.case_manager.list_cases()
            print("\n📁 All Cases:")
            for case in cases:
                status = "✅" if case.get('ingestion_complete', False) else "⏳"
                print(f"\n  {status} {case['case_name']}")
                print(f"     {case['claimant']} v {case['respondent']}")
                print(f"     Documents: {case.get('document_count', 0)}")
            print()
        
        elif cmd == '/switch':
            self._case_selection()
            if self.case_manager.active_case_id:
                self._load_case_infrastructure()
        
        elif cmd == '/new':
            self._create_new_case()
            self._load_case_infrastructure()
        
        elif cmd == '/status':
            case_id = self.case_manager.active_case_id
            case = self.case_manager.cases_index['cases'][case_id]
            stats = self.vector_store.get_stats()
            kg_stats = self.knowledge_graph.get_stats()
            query_stats = self.query_engine.get_stats()
            
            print(f"\n📊 CASE STATUS: {case['case_name']}")
            print(f"\n   Case Details:")
            print(f"   • Claimant: {case['claimant']}")
            print(f"   • Respondent: {case['respondent']}")
            print(f"   • Documents: {stats.get('total_documents', 0):,}")
            print(f"   • Chunks: {stats.get('total_chunks', 0):,}")
            print(f"   • Queries run: {query_stats['total_queries']}")
            print(f"   • Total cost: £{query_stats['total_cost_gbp']:.2f}")
            print()
        
        elif cmd == '/ingest':
            case_dir = self.case_manager.get_active_case()
            docs_dir = case_dir / "documents"
            
            doc_files = list(docs_dir.rglob('*.pdf')) + list(docs_dir.rglob('*.docx'))
            
            if not doc_files:
                print(f"\n⚠️  No documents found in {docs_dir}\n")
                return
            
            print(f"\n📄 Found {len(doc_files)} documents")
            confirm = input("\nProceed with ingestion? (y/n): ")
            if confirm.lower() != 'y':
                return
            
            print("\n🔄 Ingesting documents...")
            stats = self.vector_store.ingest_documents(docs_dir)
            
            self.case_manager.update_metadata(
                self.case_manager.active_case_id,
                {
                    'document_count': stats['total_documents'],
                    'ingestion_complete': True
                }
            )
            
            print(f"\n✅ Ingestion complete!")
            print(f"   • Documents: {stats['total_documents']:,}")
            print(f"   • Chunks: {stats['total_chunks']:,}\n")
        
        elif cmd == '/docs':
            case_dir = self.case_manager.get_active_case()
            docs_dir = case_dir / "documents"
            
            print(f"\n📂 Documents in: {docs_dir}\n")
            
            for file in sorted(docs_dir.rglob('*')):
                if file.is_file() and file.suffix.lower() in ['.pdf', '.docx', '.doc']:
                    print(f"   • {file.name}")
            print()
        
        elif cmd == '/kg':
            stats = self.knowledge_graph.get_stats()
            print(f"\n💡 KNOWLEDGE GRAPH: {stats['total_findings']} findings\n")
            
            for finding_type, count in stats.get('by_type', {}).items():
                print(f"   {finding_type.upper()}: {count}")
            print()
        
        elif cmd == '/cost':
            query_stats = self.query_engine.get_stats()
            
            print(f"\n💰 COST STATISTICS\n")
            print(f"   • Queries: {query_stats['total_queries']}")
            print(f"   • Total: £{query_stats['total_cost_gbp']:.2f}")
            print(f"   • Average: £{query_stats['avg_cost_per_query']:.4f}\n")
        
        elif cmd == '/quit':
            self._print_session_stats()
            sys.exit(0)
        
        else:
            print(f"\n❌ Unknown command: {cmd}\n")
    
    def _print_session_stats(self):
        """Print session statistics on exit"""
        if self.query_engine:
            stats = self.query_engine.get_stats()
            print(f"\n📊 Session Summary:")
            print(f"   • Queries: {stats['total_queries']}")
            print(f"   • Total cost: £{stats['total_cost_gbp']:.2f}")


if __name__ == '__main__':
    chat = HybridLitigationChat()
    chat.start()