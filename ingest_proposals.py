"""
Ingest all proposal documents into the Knowledge Base
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.modules.neo_chatbot.services.document_processor import DocumentProcessor

def main():
    print("\n" + "="*70)
    print("📄 Proposal Documents Ingestion")
    print("="*70)
    
    # Initialize processor
    print("\n1. Initializing document processor...")
    processor = DocumentProcessor()
    
    # Count current documents
    try:
        initial_count = processor.vector_store.collection.count()
        print(f"   Current documents in vector store: {initial_count}")
    except Exception as e:
        print(f"   Error checking count: {e}")
        initial_count = 0
    
    # Proposals directory
    proposals_dir = Path(__file__).parent / "app" / "modules" / "neo_chatbot" / "data" / "documents" / "proposals"
    
    # Count PDFs to process
    type1_pdfs = list((proposals_dir / "type-1").glob("*.pdf"))
    type2_pdfs = list((proposals_dir / "type-2").glob("*.pdf"))
    type3_pdfs = list((proposals_dir / "type-3").glob("*.pdf"))
    
    total_pdfs = len(type1_pdfs) + len(type2_pdfs) + len(type3_pdfs)
    
    print(f"\n2. PDFs found:")
    print(f"   Type-1 (AMR Proposals): {len(type1_pdfs)} files")
    print(f"   Type-2 (ASRS Proposals): {len(type2_pdfs)} files")
    print(f"   Type-3 (Other Proposals): {len(type3_pdfs)} files")
    print(f"   Total: {total_pdfs} files")
    
    if total_pdfs == 0:
        print("\n❌ No PDF files found!")
        return
    
    print(f"\n3. Starting ingestion...")
    print(f"   This will take approximately {total_pdfs * 2} seconds")
    
    # Process each folder
    success = 0
    failed = 0
    failed_files = []
    
    for folder_name, pdf_list in [
        ("Type-1 (AMR)", type1_pdfs), 
        ("Type-2 (ASRS)", type2_pdfs), 
        ("Type-3 (Other)", type3_pdfs)
    ]:
        if len(pdf_list) == 0:
            continue
            
        print(f"\n{'='*70}")
        print(f"Processing {folder_name}: {len(pdf_list)} files")
        print(f"{'='*70}")
        
        for i, pdf_path in enumerate(pdf_list, 1):
            try:
                print(f"  [{i}/{len(pdf_list)}] {pdf_path.name[:50]}... ", end="", flush=True)
                processor.process_document(str(pdf_path))
                success += 1
                print("✅")
            except Exception as e:
                failed += 1
                failed_files.append((pdf_path.name, str(e)))
                print(f"❌ {str(e)[:50]}")
    
    # Final summary
    print(f"\n{'='*70}")
    print("📊 INGESTION COMPLETE")
    print(f"{'='*70}")
    print(f"\nResults:")
    print(f"  ✅ Successfully processed: {success}/{total_pdfs}")
    print(f"  ❌ Failed: {failed}")
    
    if failed > 0:
        print(f"\nFailed files:")
        for fname, error in failed_files[:10]:  # Show first 10
            print(f"  - {fname}: {error[:100]}")
        if len(failed_files) > 10:
            print(f"  ... and {len(failed_files) - 10} more")
    
    # Final count
    try:
        final_count = processor.vector_store.collection.count()
        new_docs = final_count - initial_count
        print(f"\nVector Store Status:")
        print(f"  Initial documents: {initial_count}")
        print(f"  Final documents: {final_count}")
        print(f"  New documents added: {new_docs}")
    except Exception as e:
        print(f"\n❌ Error getting final count: {e}")
    
    print(f"\n{'='*70}")
    print("✅ Done! You can now ask questions about these proposals in the chatbot.")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
