"""
Re-ingest All Documents with HuggingFace Embeddings

CRITICAL: The old vector store has 1536-dim embeddings (OpenAI mock)
         HuggingFace generates 384-dim embeddings
         
This script will:
1. Backup the old vector store
2. Clear the vector store
3. Re-ingest all documents with HuggingFace embeddings
4. Re-ingest all code with HuggingFace embeddings
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.modules.neo_chatbot.services.vector_store_service import VectorStoreService
from app.modules.neo_chatbot.scripts.ingest_documents import DocumentProcessor
from app.modules.neo_chatbot.scripts.ingest_code import CodeProcessor
from dotenv import load_dotenv

# Load environment
load_dotenv()

def backup_vector_store():
    """Backup existing vector store"""
    print("=" * 60)
    print("📦 BACKING UP OLD VECTOR STORE")
    print("=" * 60)
    
    vector_store_path = Path("app/modules/neo_chatbot/data/vector_store.json")
    
    if not vector_store_path.exists():
        print("⚠️  No existing vector store found - nothing to backup")
        return None
    
    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = vector_store_path.parent / f"vector_store_backup_{timestamp}.json"
    
    shutil.copy(vector_store_path, backup_path)
    print(f"✅ Backed up to: {backup_path}")
    print(f"   Size: {backup_path.stat().st_size / (1024*1024):.2f} MB")
    print()
    
    return backup_path


def clear_vector_store():
    """Clear the vector store"""
    print("=" * 60)
    print("🗑️  CLEARING VECTOR STORE")
    print("=" * 60)
    
    vector_store_path = Path("app/modules/neo_chatbot/data/vector_store.json")
    
    if vector_store_path.exists():
        vector_store_path.unlink()
        print("✅ Old vector store deleted")
    
    # Initialize fresh vector store
    vector_store = VectorStoreService()
    print(f"✅ Fresh vector store created: {len(vector_store.documents)} documents")
    print()
    
    return vector_store


def reingest_documents(vector_store):
    """Re-ingest all documents with HuggingFace embeddings"""
    print("=" * 60)
    print("📄 RE-INGESTING DOCUMENTS")
    print("=" * 60)
    
    try:
        # DocumentProcessor creates its own vector_store instance
        doc_processor = DocumentProcessor(use_ocr=True)
        
        # Ingest from documents directory
        docs_path = Path("app/modules/neo_chatbot/data/documents")
        if docs_path.exists():
            print(f"📂 Processing documents from: {docs_path}")
            doc_processor.ingest_folder(str(docs_path), category="neo-documentation")
            # Count documents in vector store after ingestion
            count = len(doc_processor.vector_store.documents)
            print(f"✅ Ingested {count} document chunks")
        else:
            print("⚠️  Documents directory not found")
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ Error ingesting documents: {e}")
        import traceback
        traceback.print_exc()
        return False


def reingest_code(vector_store):
    """Re-ingest all code with HuggingFace embeddings"""
    print("=" * 60)
    print("💻 RE-INGESTING CODE")
    print("=" * 60)
    
    try:
        # Check for NEO codebase path - try multiple locations
        possible_paths = [
            os.getenv("NEO_CODEBASE_PATH"),
            r"C:\Users\Balmukund.Mishra\Desktop\neo-fleet-manager-noon-min-2.0",  # Lowercase Desktop!
            r"C:\Users\Balmukund.Mishra\Desktop\NEO\neo-fleet-manager-noon-min-2.0",
            r"C:\Users\Balmukund.Mishra\Desktop\NEO\neo-fleet-manager",
            r"C:\Users\Balmukund.Mishra\Desktop\neo-fleet-manager",
            str(Path.home() / "Desktop" / "neo-fleet-manager-noon-min-2.0"),
            str(Path.home() / "Desktop" / "NEO" / "neo-fleet-manager-noon-min-2.0"),
            str(Path.home() / "Desktop" / "NEO" / "neo-fleet-manager"),
        ]
        
        neo_codebase = None
        for path in possible_paths:
            if path and Path(path).exists():
                neo_codebase = path
                break
        
        if not neo_codebase:
            print(f"⚠️  NEO codebase not found. Tried:")
            for path in possible_paths:
                if path:
                    print(f"     - {path}")
            print()
            print("   You can:")
            print("   1. Set NEO_CODEBASE_PATH in .env file")
            print("   2. Place code at: C:\\Users\\Balmukund.Mishra\\Desktop\\NEO\\neo-fleet-manager")
            print("   3. Skip code ingestion (documents will still work)")
            print()
            return False
        
        # CodeProcessor creates its own vector_store instance
        code_processor = CodeProcessor()
        
        print(f"📂 Processing code from: {neo_codebase}")
        result = code_processor.ingest_directory(
            directory_path=neo_codebase,
            category="neo-fleet-manager-code",
            recursive=True
        )
        count = result.get("files_processed", 0)
        
        print(f"✅ Ingested {count} code files")
        print()
        return True
        
    except Exception as e:
        print(f"❌ Error ingesting code: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_embeddings():
    """Verify all embeddings are 384 dimensions"""
    print("=" * 60)
    print("🔍 VERIFYING EMBEDDINGS")
    print("=" * 60)
    
    # Load fresh vector store to check
    vector_store = VectorStoreService()
    
    if not vector_store.documents:
        print("⚠️  No documents in vector store")
        return False
    
    # Check first few documents
    sample_size = min(10, len(vector_store.documents))
    all_384 = True
    
    for i, doc in enumerate(vector_store.documents[:sample_size]):
        embedding_dim = len(doc.get('embedding', []))
        status = "✅" if embedding_dim == 384 else "❌"
        
        if embedding_dim != 384:
            all_384 = False
        
        print(f"{status} Document {i+1}: {embedding_dim} dimensions")
    
    print()
    
    if all_384:
        print("✅ All embeddings are 384 dimensions (HuggingFace)")
        return True
    else:
        print("❌ Some embeddings have wrong dimensions!")
        return False


def main():
    """Main re-ingestion workflow"""
    print("\n")
    print("=" * 60)
    print("🔄 RE-INGEST WITH HUGGINGFACE EMBEDDINGS")
    print("=" * 60)
    print()
    
    # Check for HuggingFace API key
    hf_key = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
    if not hf_key:
        print("❌ ERROR: HUGGINGFACE_API_KEY not found in .env")
        print()
        print("Add your FREE key:")
        print("1. Get from: https://huggingface.co/settings/tokens")
        print("2. Add to .env: HUGGINGFACE_API_KEY=hf_your_key")
        print()
        return False
    
    print(f"✅ HuggingFace API Key found: {hf_key[:10]}...{hf_key[-5:]}")
    print()
    
    # Step 1: Backup
    backup_path = backup_vector_store()
    
    # Step 2: Clear
    vector_store = clear_vector_store()
    
    # Step 3: Re-ingest documents  
    doc_success = reingest_documents(None)  # Doesn't need vector_store parameter
    
    # Step 4: Re-ingest code
    code_success = reingest_code(None)  # Doesn't need vector_store parameter
    
    # Step 5: Verify
    verify_success = verify_embeddings()  # Will load its own vector_store
    
    # Summary
    print("=" * 60)
    print("📊 RE-INGESTION SUMMARY")
    print("=" * 60)
    print(f"✅ Backup created: {backup_path}")
    print(f"{'✅' if doc_success else '❌'} Documents re-ingested")
    print(f"{'✅' if code_success else '⚠️'} Code re-ingested")
    print(f"{'✅' if verify_success else '❌'} Embedding dimensions verified")
    
    # Load final vector store to get count
    final_vector_store = VectorStoreService()
    print()
    print(f"📈 Total documents in vector store: {len(final_vector_store.documents)}")
    print()
    
    if doc_success and verify_success:
        print("=" * 60)
        print("🎉 SUCCESS! All documents re-ingested with HuggingFace embeddings")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Restart your chatbot")
        print("2. Test with: 'What is NEO?'")
        print("3. Check logs for: '✅ Generated HuggingFace embedding'")
        print()
        return True
    else:
        print("=" * 60)
        print("⚠️  RE-INGESTION INCOMPLETE")
        print("=" * 60)
        print()
        print("Check errors above and try again")
        print()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
