"""
Interactive Code Ingestion Tool
Easily ingest code from any directory with guided prompts
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.modules.neo_chatbot.scripts.ingest_code import CodeProcessor
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_user_input(prompt: str, default: str = None) -> str:
    """Get user input with optional default"""
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "
    
    response = input(full_prompt).strip()
    return response if response else default


def confirm_action(prompt: str) -> bool:
    """Ask user for yes/no confirmation"""
    response = input(f"{prompt} (y/n): ").strip().lower()
    return response in ['y', 'yes']


def main():
    """Interactive code ingestion"""
    
    print("\n" + "="*80)
    print("📚 INTERACTIVE CODE INGESTION TOOL")
    print("="*80)
    print("\nThis tool helps you embed code into the NEO Chatbot knowledge base")
    print("\n💡 Supported languages: C#, Python, JavaScript, TypeScript, Java, SQL, etc.")
    print("⏭️  Automatically skips: bin/, obj/, node_modules/, .git/, etc.\n")
    
    # Get source path
    print("="*80)
    print("Step 1: Select Source")
    print("="*80)
    
    default_path = r"C:\Users\Balmukund.Mishra\Desktop\neo-fleet-manager-noon-min-2.0"
    
    print(f"\n📂 Common paths:")
    print(f"   1. NEO Fleet Manager: {default_path}")
    print(f"   2. Current directory: {Path.cwd()}")
    print(f"   3. Custom path\n")
    
    choice = get_user_input("Choose option (1/2/3)", "1")
    
    if choice == "1":
        source_path = default_path
    elif choice == "2":
        source_path = str(Path.cwd())
    else:
        source_path = get_user_input("Enter path to code directory")
    
    # Validate path
    if not Path(source_path).exists():
        print(f"\n❌ ERROR: Path not found!")
        print(f"   {source_path}")
        return
    
    print(f"\n✅ Source: {source_path}")
    
    # Get category
    print("\n" + "="*80)
    print("Step 2: Categorize Code")
    print("="*80)
    
    print(f"\n📁 Categories help organize and filter code in search")
    print(f"   Examples: 'neo-core', 'controllers', 'services', 'utilities'\n")
    
    category = get_user_input("Enter category", "code")
    print(f"✅ Category: {category}")
    
    # Recursive option
    print("\n" + "="*80)
    print("Step 3: Scan Options")
    print("="*80)
    
    print(f"\n🔍 Should we scan subdirectories?")
    print(f"   Yes: Process all files in all subdirectories (recommended)")
    print(f"   No: Only files in the specified directory\n")
    
    recursive = confirm_action("Scan subdirectories?")
    print(f"✅ Recursive: {'Yes' if recursive else 'No'}")
    
    # Preview
    print("\n" + "="*80)
    print("Step 4: Review & Confirm")
    print("="*80)
    
    print(f"\n📋 Configuration:")
    print(f"   Source: {source_path}")
    print(f"   Category: {category}")
    print(f"   Recursive: {'Yes' if recursive else 'No'}")
    print(f"\n⏱️  Expected time: 5-10 minutes for large codebases")
    print(f"📦 Result: Code chunks embedded in vector store")
    print(f"🔍 Usage: Ask questions about classes, methods, implementations\n")
    
    if not confirm_action("Start ingestion?"):
        print("\n❌ Cancelled by user")
        return
    
    # Start ingestion
    print("\n" + "="*80)
    print("Step 5: Ingestion")
    print("="*80 + "\n")
    
    logger.info("🔧 Initializing Code Processor...")
    processor = CodeProcessor()
    
    logger.info("📥 Starting ingestion...\n")
    
    results = processor.ingest_directory(
        directory_path=source_path,
        category=category,
        recursive=recursive
    )
    
    # Display results
    if results["successful"] > 0:
        print("\n" + "="*80)
        print("✅ SUCCESS!")
        print("="*80)
        
        print(f"\n📊 Results:")
        print(f"   • {results['successful']} files embedded")
        print(f"   • {results['total_chunks']} code chunks created")
        print(f"   • {results['skipped']} files skipped")
        
        if results['failed'] > 0:
            print(f"   ⚠️  {results['failed']} files failed")
        
        print(f"\n📚 Languages:")
        for lang, count in results["by_language"].items():
            print(f"   • {lang}: {count} files")
        
        print(f"\n💡 Try these queries:")
        print(f"   • 'Show me classes in the {category} codebase'")
        print(f"   • 'How is [feature] implemented?'")
        print(f"   • 'What methods are available in [ClassName]?'")
        
        print("\n" + "="*80)
        
        # Ask if user wants to verify
        if confirm_action("\nRun verification check?"):
            print("\n📊 Checking vector store...")
            import subprocess
            subprocess.run([sys.executable, "check_vector_store.py"])
    
    else:
        print("\n" + "="*80)
        print("⚠️  NO FILES INGESTED")
        print("="*80)
        
        print(f"\nPossible reasons:")
        print(f"   1. No supported code files found (.cs, .py, .js, etc.)")
        print(f"   2. All files were filtered out (bin/, obj/, etc.)")
        print(f"   3. Path is incorrect")
        
        print(f"\n💡 Try:")
        print(f"   • Check if code files exist in: {source_path}")
        print(f"   • Enable recursive scan")
        print(f"   • Verify file extensions are supported")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
