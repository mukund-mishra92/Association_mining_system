import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
    DB_NAME = os.getenv("DB_NAME", "neo")
    
    # Source tables (where to read data from)
    ORDER_TABLE = os.getenv("ORDER_TABLE", "wms_to_wcs_order_line_request_data")
    SKU_MASTER_TABLE = os.getenv("SKU_MASTER_TABLE", "sku_master")
    
    # Output table (where to write recommendations)
    RECOMMENDATIONS_TABLE = os.getenv("RECOMMENDATIONS_TABLE", "sku_recommendations")
    
    # Mining Configuration - Optimized for large datasets
    MIN_SUPPORT = float(os.getenv("MIN_SUPPORT", "0.45"))  # High support for performance with large datasets
    MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.4"))
    MIN_LIFT = float(os.getenv("MIN_LIFT", "1.0"))
    MAX_RECOMMENDATIONS = int(os.getenv("MAX_RECOMMENDATIONS", "3"))
    
    # Item filtering to improve performance and quality
    MAX_ITEMS = int(os.getenv("MAX_ITEMS", "500"))  # Maximum items to process (top N most frequent)
    MIN_ITEM_FREQUENCY = int(os.getenv("MIN_ITEM_FREQUENCY", "3"))  # Minimum orders an item must appear in
    
    # Time-based weighting
    DECAY_RATE = float(os.getenv("DECAY_RATE", "0.05"))
    
    # Enhanced time-based modeling settings
    DEFAULT_TIME_WEIGHTING_METHOD = os.getenv("DEFAULT_TIME_WEIGHTING_METHOD", "exponential_decay")
    DEFAULT_TIME_SEGMENTATION = os.getenv("DEFAULT_TIME_SEGMENTATION", "weekly")
    USE_ENHANCED_MINING = os.getenv("USE_ENHANCED_MINING", "true").lower() == "true"
    
    # Temporal scoring weights
    TEMPORAL_CONFIDENCE_WEIGHT = float(os.getenv("TEMPORAL_CONFIDENCE_WEIGHT", "0.25"))
    TEMPORAL_LIFT_WEIGHT = float(os.getenv("TEMPORAL_LIFT_WEIGHT", "0.25"))
    TEMPORAL_SUPPORT_WEIGHT = float(os.getenv("TEMPORAL_SUPPORT_WEIGHT", "0.15"))
    TEMPORAL_STABILITY_WEIGHT = float(os.getenv("TEMPORAL_STABILITY_WEIGHT", "0.20"))
    TEMPORAL_TREND_WEIGHT = float(os.getenv("TEMPORAL_TREND_WEIGHT", "0.15"))
    
    # API Configuration
    API_TITLE = "Association Rule Mining API"
    API_VERSION = "1.0.0"
    API_DESCRIPTION = "Production-ready association rule mining system with temporal analysis"
    
    # Local LLM Configuration (Fallback when Groq API fails)
    LOCAL_LLM_ENABLED = os.getenv("LOCAL_LLM_ENABLED", "true").lower() == "true"
    LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "phi-2-2.7b")  # Options: tinyllama-1.1b, phi-2-2.7b, mistral-7b-instruct
    LOCAL_LLM_MAX_TOKENS = int(os.getenv("LOCAL_LLM_MAX_TOKENS", "500"))
    LOCAL_LLM_TEMPERATURE = float(os.getenv("LOCAL_LLM_TEMPERATURE", "0.3"))
    
    # Agentic AI Configuration (Multi-Agent System with LangGraph)
    AGENTIC_MODE_ENABLED = os.getenv("AGENTIC_MODE_ENABLED", "true").lower() == "true"
    AGENTIC_VERIFICATION_THRESHOLD = int(os.getenv("AGENTIC_VERIFICATION_THRESHOLD", "100"))

config = Config()