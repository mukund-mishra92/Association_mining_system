"""
Ingest NEO Fleet Manager C# Codebase
Wrapper script to embed C# code from the fleet manager repository
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


def main():
    """Ingest NEO Fleet Manager C# codebase"""
    
    # Path to NEO Fleet Manager codebase
    neo_codebase_path = r"C:\Users\Balmukund.Mishra\Desktop\neo-fleet-manager-noon-min-2.0"
    
    logger.info("\n" + "="*80)
    logger.info("🚀 NEO FLEET MANAGER CODE INGESTION")
    logger.info("="*80)
    logger.info(f"\n📂 Source: {neo_codebase_path}")
    
    # Check if path exists
    if not Path(neo_codebase_path).exists():
        logger.error(f"\n❌ ERROR: Path not found!")
        logger.error(f"   {neo_codebase_path}")
        logger.error(f"\n💡 Please verify the path and try again")
        return
    
    # Initialize processor
    logger.info(f"\n🔧 Initializing Code Processor...")
    processor = CodeProcessor()
    
    # Ingest the directory
    logger.info(f"\n📥 Starting ingestion...")
    logger.info(f"   This may take several minutes for large codebases\n")
    
    results = processor.ingest_directory(
        directory_path=neo_codebase_path,
        category="neo-fleet-manager-code",
        recursive=True
    )
    
    # Display results
    if results["successful"] > 0:
        logger.info("\n" + "="*80)
        logger.info("✅ INGESTION COMPLETE!")
        logger.info("="*80)
        logger.info(f"\n📊 Results:")
        logger.info(f"   • {results['successful']} files embedded successfully")
        logger.info(f"   • {results['total_chunks']} code chunks created")
        logger.info(f"   • {results['skipped']} files skipped")
        logger.info(f"   • {results['failed']} files failed")
        
        logger.info(f"\n📚 Languages processed:")
        for lang, count in results["by_language"].items():
            logger.info(f"   • {lang}: {count} files")
        
        logger.info(f"\n💡 You can now ask questions about:")
        logger.info(f"   • Classes, methods, and functions in the codebase")
        logger.info(f"   • How specific features are implemented")
        logger.info(f"   • Code patterns and best practices")
        logger.info(f"   • System architecture and design")
        
        logger.info(f"\n🔍 Example queries:")
        logger.info(f"   - 'Show me the warehouse controller implementation'")
        logger.info(f"   - 'How is the bin allocation logic handled?'")
        logger.info(f"   - 'What methods are available in the InventoryService?'")
        logger.info(f"   - 'Explain the data models for fleet management'")
        
        logger.info("\n" + "="*80 + "\n")
    else:
        logger.warning("\n⚠️ No files were successfully ingested")
        logger.warning("Check the logs above for details")


if __name__ == "__main__":
    main()
