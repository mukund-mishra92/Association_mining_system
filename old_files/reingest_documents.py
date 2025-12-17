"""
Re-ingest All Documents with Consistent Embeddings
Fixes the embedding mismatch issue
"""

import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

from app.modules.neo_chatbot.scripts.ingest_documents import DocumentProcessor
from app.modules.neo_chatbot.services.llm_service import LLMService
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Re-ingest all proposal documents"""
    
    print("\n" + "=" * 80)
    print("RE-INGESTING ALL DOCUMENTS WITH CONSISTENT EMBEDDINGS")
    print("=" * 80)
    print("\nThis will:")
    print("1. Delete old vector store (with mismatched embeddings)")
    print("2. Re-ingest all PDFs from app/modules/neo_chatbot/data/documents/")
    print("3. Use consistent embeddings (OpenAI or HuggingFace with retry)")
    print("\n" + "=" * 80)
    
    # Check embedding service
    llm = LLMService()
    
    print("\n🔍 Checking embedding service...")
    if llm.openai_client:
        print("✅ OpenAI embeddings available (RECOMMENDED - most reliable)")
    elif llm.hf_client:
        print("✅ HuggingFace embeddings available (FREE - with retry logic)")
        print("   Note: May be slower due to network timeouts, but will retry")
    else:
        print("⚠️ WARNING: No embedding service configured!")
        print("   Will use MOCK embeddings (POOR search quality)")
        print("\nRecommendation:")
        print("   Add OPENAI_API_KEY to .env for best results")
        print("   OR ensure HuggingFace network access")
        
        response = input("\nContinue with MOCK embeddings? (y/n): ")
        if response.lower() != 'y':
            print("Aborted. Please configure embeddings first.")
            return
    
    # Initialize processor
    processor = DocumentProcessor()
    
    # Path to documents
    docs_path = Path(__file__).parent / "app" / "modules" / "neo_chatbot" / "data" / "documents"
    
    if not docs_path.exists():
        print(f"\n❌ ERROR: Documents directory not found: {docs_path}")
        print("Please ensure documents are in the correct location.")
        return
    
    # Find all PDFs
    pdf_files = list(docs_path.glob("*.pdf"))
    
    if not pdf_files:
        print(f"\n❌ ERROR: No PDF files found in {docs_path}")
        return
    
    print(f"\n📄 Found {len(pdf_files)} PDF files to ingest:")
    for i, pdf in enumerate(pdf_files, 1):
        print(f"   {i}. {pdf.name}")
    
    print("\n" + "=" * 80)
    print("STARTING INGESTION")
    print("=" * 80)
    print("\nThis may take 5-15 minutes depending on:")
    print("- Number of documents")
    print("- Document size")
    print("- Embedding service speed")
    print("- Network connectivity\n")
    
    # Process each document
    total_docs = 0
    total_chunks = 0
    
    for i, pdf_path in enumerate(pdf_files, 1):
        try:
            print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")
            print("-" * 80)
            
            result = processor.ingest_pdf(
                pdf_path=str(pdf_path),
                category="neo-documentation"
            )
            
            if result['success']:
                num_chunks = result.get('chunks_created', 0)
                total_docs += 1
                total_chunks += num_chunks
                print(f"✅ Success: {num_chunks} chunks created")
            else:
                print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            print(f"❌ ERROR processing {pdf_path.name}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("INGESTION COMPLETE!")
    print("=" * 80)
    print(f"\n📊 Summary:")
    print(f"   Total documents processed: {total_docs}/{len(pdf_files)}")
    print(f"   Total chunks created: {total_chunks}")
    print(f"   Average chunks per document: {total_chunks/total_docs if total_docs > 0 else 0:.1f}")
    
    print("\n✅ Vector store updated with consistent embeddings!")
    print("\nNext steps:")
    print("1. Restart chatbot: .\\stop_servers.bat && .\\quick_start.bat")
    print("2. Test search: venv\\Scripts\\python.exe check_vector_store.py")
    print("3. Ask chatbot: 'Explain CBS sorter flow in detail'")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
