# Ingestion Configuration
# Configure paths for document and code ingestion

# NEO Fleet Manager Codebase Path
# Set to None or empty string to skip code ingestion
NEO_CODEBASE_PATH = r"C:\Users\Balmukund.Mishra\Desktop\neo-fleet-manager-noon-min-2.0"

# Additional code repositories (optional)
# Add more repositories to ingest multiple codebases
ADDITIONAL_CODE_REPOS = [
    # Example:
    # {
    #     "path": r"C:\path\to\another\repo",
    #     "category": "other-project-code",
    #     "enabled": True
    # }
]

# Document ingestion settings
DOCUMENT_CATEGORIES = {
    "proposals/type-1": "proposals_sorting_conveyor",
    "proposals/type-2": "proposals_warehouse_automation",
    "proposals/type-3": "proposals_specialized_systems",
    "support": "technical_support",
    ".": "general_documentation"
}

# Code ingestion settings
CODE_CATEGORY = "neo-fleet-manager-code"
ENABLE_CODE_INGESTION = True
SKIP_EXISTING_FILES = True  # Skip already ingested files for faster re-runs
