"""
Intelligent Full Document & Code Ingestion
Checks existing vector store and only adds missing documents and code files
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.modules.neo_chatbot.scripts.ingest_documents import DocumentProcessor
from app.modules.neo_chatbot.scripts.ingest_code import CodeProcessor
from app.modules.neo_chatbot.services.vector_store_service import VectorStoreService

# Import configuration (with fallback if not found)
try:
    from ingestion_config import (
        NEO_CODEBASE_PATH,
        ADDITIONAL_CODE_REPOS,
        DOCUMENT_CATEGORIES,
        CODE_CATEGORY,
        ENABLE_CODE_INGESTION
    )
except ImportError:
    # Fallback to defaults if config file doesn't exist
    NEO_CODEBASE_PATH = r"C:\Users\Balmukund.Mishra\Desktop\neo-fleet-manager-noon-min-2.0"
    ADDITIONAL_CODE_REPOS = []
    DOCUMENT_CATEGORIES = {
        "proposals/type-1": "proposals_sorting_conveyor",
        "proposals/type-2": "proposals_warehouse_automation",
        "proposals/type-3": "proposals_specialized_systems",
        "support": "technical_support",
        ".": "general_documentation"
    }
    CODE_CATEGORY = "neo-fleet-manager-code"
    ENABLE_CODE_INGESTION = True

def main():
    print("\n" + "="*80)
    print("📚 INTELLIGENT FULL DOCUMENT & CODE INGESTION")
    print("   (Only ingests items not already in vector store)")
    print("="*80)
    
    # Initialize services
    doc_processor = DocumentProcessor()
    code_processor = CodeProcessor()
    vs = VectorStoreService()
    
    # Get existing documents
    existing_files = set()
    for doc in vs.documents:
        filename = doc.get('metadata', {}).get('filename', '')
        if filename:
            existing_files.add(filename)
    
    print(f"\n📊 Current Vector Store Status:")
    print(f"   Total document chunks: {len(vs.documents)}")
    print(f"   Unique files ingested: {len(existing_files)}")
    
    if existing_files:
        print(f"\n   Recently ingested files:")
        for i, filename in enumerate(sorted(existing_files)[-10:], 1):
            print(f"      {i}. {filename}")
        if len(existing_files) > 10:
            print(f"      ... and {len(existing_files) - 10} more")
    
    # Base documents folder
    docs_base = Path("app/modules/neo_chatbot/data/documents")
    
    # Categories to process (from config)
    categories = DOCUMENT_CATEGORIES
    
    total_found = 0
    total_new = 0
    total_skipped = 0
    total_failed = 0
    failed_files = []
    
    for folder, category in categories.items():
        folder_path = docs_base / folder if folder != "." else docs_base
        
        if not folder_path.exists():
            print(f"\n⚠️  Folder not found: {folder_path}")
            continue
        
        print(f"\n{'='*80}")
        print(f"📁 Processing: {folder if folder != '.' else 'root documents folder'}")
        print(f"   Category: {category}")
        print(f"   Path: {folder_path}")
        print(f"{'='*80}\n")
        
        # Find all PDFs (non-recursive for root, recursive for subfolders)
        if folder == ".":
            pdf_files = [f for f in folder_path.glob("*.pdf") if f.is_file()]
        else:
            pdf_files = list(folder_path.glob("*.pdf"))
        
        total_found += len(pdf_files)
        
        if not pdf_files:
            print("   No PDF files found in this folder")
            continue
        
        print(f"Found {len(pdf_files)} PDF files\n")
        
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"[{i}/{len(pdf_files)}] {pdf_file.name}")
            
            # Check if already ingested
            if pdf_file.name in existing_files:
                print(f"   ⏭️  Already ingested - skipping")
                total_skipped += 1
                continue
            
            # Ingest new document
            try:
                result = doc_processor.ingest_pdf(str(pdf_file), category)
                
                if result.get("status") == "success":
                    total_new += 1
                    chunks = result.get('chunks', 0)
                    chars = result.get('total_characters', 0)
                    print(f"   ✅ Success: {chunks} chunks ({chars:,} characters)")
                else:
                    total_failed += 1
                    error_msg = result.get('message', 'Unknown error')
                    print(f"   ❌ Failed: {error_msg}")
                    failed_files.append({
                        'file': pdf_file.name,
                        'error': error_msg,
                        'path': str(pdf_file)
                    })
                    
            except Exception as e:
                total_failed += 1
                error_str = str(e)[:200]
                print(f"   ❌ Error: {error_str}")
                failed_files.append({
                    'file': pdf_file.name,
                    'error': error_str,
                    'path': str(pdf_file)
                })
    
    # ========================================================================
    # CODE INGESTION SECTION
    # ========================================================================
    
    print("\n" + "="*80)
    print("💻 CODE INGESTION")
    print("="*80)
    
    if not ENABLE_CODE_INGESTION:
        print("\n⏭️  Code ingestion disabled in config")
        print("   To enable: Set ENABLE_CODE_INGESTION = True in ingestion_config.py")
        code_stats = {'total_files': 0, 'new_files': 0, 'skipped': 0, 'failed': 0}
    else:
        # NEO Fleet Manager codebase path (from config)
        neo_codebase_path = Path(NEO_CODEBASE_PATH) if NEO_CODEBASE_PATH else None
    
        code_stats = {
            'total_files': 0,
            'new_files': 0,
            'skipped': 0,
            'failed': 0
        }
        
        if neo_codebase_path and neo_codebase_path.exists():
            print(f"\n📂 Checking NEO Fleet Manager codebase...")
            print(f"   Path: {neo_codebase_path}")
            
            # Get list of already ingested code files
            existing_code_files = set()
            for doc in vs.documents:
                metadata = doc.get('metadata', {})
                if metadata.get('type') == 'code':
                    filename = metadata.get('filename', '')
                    if filename:
                        existing_code_files.add(filename)
            
            print(f"\n   Already ingested code files: {len(existing_code_files)}")
            
            # Get all code files
            all_code_files = []
            for ext in code_processor.CODE_EXTENSIONS.keys():
                all_code_files.extend(neo_codebase_path.glob(f"**/*{ext}"))
            
            # Filter out skipped paths
            code_files = [f for f in all_code_files if not code_processor.should_skip(f)]
            
            print(f"   Total code files found: {len(code_files)}")
            
            # Count new files
            new_code_files = [f for f in code_files if f.name not in existing_code_files]
            
            print(f"   New files to ingest: {len(new_code_files)}")
            
            if new_code_files:
                print(f"\n   Starting code ingestion...")
                
                # Ingest new code files
                for i, code_file in enumerate(new_code_files, 1):
                    if i % 10 == 0:  # Progress update every 10 files
                        print(f"   Progress: {i}/{len(new_code_files)} files...")
                    
                    result = code_processor.ingest_code_file(str(code_file), CODE_CATEGORY)
                    
                    code_stats['total_files'] += 1
                    
                    if result.get('status') == 'success':
                        code_stats['new_files'] += 1
                    elif result.get('status') == 'skipped':
                        code_stats['skipped'] += 1
                    else:
                        code_stats['failed'] += 1
                
                print(f"\n   ✅ Code ingestion complete!")
                print(f"      New files: {code_stats['new_files']}")
                print(f"      Skipped: {code_stats['skipped']}")
                print(f"      Failed: {code_stats['failed']}")
            else:
                print(f"\n   ⏭️  All code files already ingested - skipping")
                code_stats['skipped'] = len(code_files)
        else:
            print(f"\n⚠️  NEO Fleet Manager codebase not found at:")
            print(f"   {neo_codebase_path if neo_codebase_path else 'Not configured'}")
            print(f"\n   To enable code ingestion:")
            print(f"   1. Edit ingestion_config.py and set NEO_CODEBASE_PATH")
            print(f"   2. Or run: python ingest_neo_code.py")
    
    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    
    print("\n" + "="*80)
    print("📊 FINAL INGESTION SUMMARY")
    print("="*80)
    
    print(f"\n📄 DOCUMENTS (PDFs):")
    print(f"   Total found: {total_found}")
    print(f"   ✅ Newly ingested: {total_new}")
    print(f"   ⏭️  Skipped (already exists): {total_skipped}")
    print(f"   ❌ Failed: {total_failed}")
    
    print(f"\n💻 CODE FILES:")
    print(f"   Total found: {code_stats['total_files'] + code_stats['skipped']}")
    print(f"   ✅ Newly ingested: {code_stats['new_files']}")
    print(f"   ⏭️  Skipped (already exists): {code_stats['skipped']}")
    print(f"   ❌ Failed: {code_stats['failed']}")
    
    print(f"\n📊 OVERALL:")
    total_items = total_found + code_stats['total_files'] + code_stats['skipped']
    total_ingested = total_new + code_stats['new_files']
    total_all_skipped = total_skipped + code_stats['skipped']
    total_all_failed = total_failed + code_stats['failed']
    
    print(f"   Total items found: {total_items}")
    print(f"   ✅ Newly ingested: {total_ingested}")
    print(f"   ⏭️  Skipped: {total_all_skipped}")
    print(f"   ❌ Failed: {total_all_failed}")
    
    if failed_files:
        print(f"\n⚠️  Failed Files ({len(failed_files)}):")
        for i, fail_info in enumerate(failed_files, 1):
            print(f"\n   {i}. {fail_info['file']}")
            print(f"      Error: {fail_info['error']}")
            print(f"      Path: {fail_info['path']}")
    
    # Updated vector store stats
    print(f"\n{'='*80}")
    print("📊 UPDATED VECTOR STORE STATISTICS")
    print("="*80)
    
    vs_updated = VectorStoreService()
    print(f"\nTotal document chunks: {len(vs_updated.documents)}")
    
    # Count unique files
    unique_files = set()
    for doc in vs_updated.documents:
        filename = doc.get('metadata', {}).get('filename', '')
        if filename:
            unique_files.add(filename)
    
    print(f"Unique files: {len(unique_files)}")
    
    # Get stats by category
    stats = vs_updated.get_statistics()
    print(f"\nDocuments by category:")
    for cat, count in sorted(stats.get('categories', {}).items()):
        print(f"   {cat}: {count}")
    
    print("\n" + "="*80)
    print("\n✅ Ingestion complete!")
    
    if total_new > 0 or code_stats['new_files'] > 0:
        print(f"\n💡 You can now query the chatbot about:")
        if total_new > 0:
            print(f"   📄 Documents: 'What proposals do we have for warehouse automation?'")
        if code_stats['new_files'] > 0:
            print(f"   💻 Code: 'Show me the WarehouseController implementation'")
            print(f"          'How is bin allocation coded?'")
    
    if total_all_failed > 0:
        print(f"\n⚠️  Note: {total_all_failed} items failed to ingest")
        print(f"   Documents failed: {total_failed}")
        print(f"   Code files failed: {code_stats['failed']}")
        print(f"   Check the error messages above for details")
        print(f"   You can try re-running just those files individually")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
