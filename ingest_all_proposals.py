"""
Batch Ingest All Proposal Documents
Processes all proposal types (type-1, type-2, type-3) into the knowledge base
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.modules.neo_chatbot.scripts.ingest_documents import DocumentProcessor

def main():
    """Ingest all proposal documents"""
    print("\n" + "="*80)
    print("📚 BATCH INGESTION: ALL PROPOSAL DOCUMENTS")
    print("="*80)
    
    # Initialize processor
    processor = DocumentProcessor()
    
    # Define proposal folders and their categories
    proposals_base = Path("app/modules/neo_chatbot/data/documents/proposals")
    
    proposal_types = {
        "type-1": "proposals_sorting_conveyor",  # Sorting & Conveyor Systems
        "type-2": "proposals_warehouse_automation",  # Warehouse Automation (Decathlon, Trent)
        "type-3": "proposals_specialized_systems"  # Specialized Systems (Amazon, Flipkart, DHL, etc.)
    }
    
    total_success = 0
    total_failed = 0
    total_chunks = 0
    
    for folder_name, category in proposal_types.items():
        folder_path = proposals_base / folder_name
        
        if not folder_path.exists():
            print(f"\n⚠️  Folder not found: {folder_path}")
            continue
        
        print(f"\n{'='*80}")
        print(f"📁 Processing: {folder_name.upper()}")
        print(f"   Category: {category}")
        print(f"   Path: {folder_path}")
        print(f"{'='*80}\n")
        
        # Get PDF files
        pdf_files = list(folder_path.glob("*.pdf"))
        print(f"Found {len(pdf_files)} PDF files\n")
        
        # Process each PDF
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
            
            try:
                result = processor.ingest_pdf(str(pdf_file), category)
                
                if result.get("success"):
                    total_success += 1
                    total_chunks += result.get("chunks", 0)
                    print(f"   ✅ Success: {result.get('chunks', 0)} chunks")
                else:
                    total_failed += 1
                    print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                total_failed += 1
                print(f"   ❌ Error: {str(e)[:100]}")
        
        print(f"\n{'-'*80}")
        print(f"Completed {folder_name}: {len([f for f in pdf_files if f])} documents processed")
        print(f"{'-'*80}\n")
    
    # Final summary
    print("\n" + "="*80)
    print("📊 FINAL INGESTION SUMMARY")
    print("="*80)
    print(f"\n✅ Successfully ingested: {total_success} documents")
    print(f"❌ Failed: {total_failed} documents")
    print(f"📦 Total chunks created: {total_chunks}")
    print(f"\n{'='*80}")
    
    # Check vector store stats
    try:
        from app.modules.neo_chatbot.services.vector_store_service import VectorStoreService
        vs = VectorStoreService()
        stats = vs.get_stats()
        print(f"\n📊 Vector Store Statistics:")
        print(f"   Total documents: {stats.get('total_documents', 'N/A')}")
        print(f"   Total categories: {len(stats.get('by_category', {}))}")
        print(f"\n   Documents by category:")
        for cat, count in stats.get('by_category', {}).items():
            print(f"      {cat}: {count}")
    except Exception as e:
        print(f"\n⚠️  Could not retrieve vector store stats: {e}")
    
    print("\n" + "="*80)
    print("✅ BATCH INGESTION COMPLETE")
    print("="*80)
    print("\nYou can now query proposals using the Knowledge Base chatbot!")
    print("Example questions:")
    print("  - 'Show me proposals for Flipkart'")
    print("  - 'What are the CBS system options we offered to Delhivery?'")
    print("  - 'List all SWEDI sorter proposals'")
    print("  - 'What was the proposal for Amazon ISK3 Bhiwandi?'")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
