"""
Oracle RAG System Configuration
Integrates Grok RAG (document ingestion) + Graph RAG (knowledge extraction)
with your-pattern's existing Neo4j and Milvus infrastructure
"""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path("/home/jeremy/oracle-rag-system")
CONFIG_DIR = BASE_DIR / "config"
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ============================================================================
# Neo4j Configuration (from your-pattern .env)
# ============================================================================
NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "secure_neo4j_password_2024",
    "database": "yourpattern",
    "max_connection_lifetime": 3600,
    "max_connection_pool_size": 50,
    "connection_acquisition_timeout": 120,
}

# ============================================================================
# Milvus Configuration (Milvus Lite - CPU-only, no Docker required)
# ============================================================================
MILVUS_CONFIG = {
    # Milvus Lite uses local file storage instead of client-server
    "uri": str(BASE_DIR / "data" / "milvus_lite.db"),  # Local SQLite-based storage
    "token": "",  # No authentication for local mode
    # Legacy config (for reference if migrating to Milvus Standalone later)
    # "host": "localhost",
    # "port": 19530,
    # "user": "",
    # "password": "",
    # "secure": False
}

# Milvus Collection Configuration
MILVUS_COLLECTIONS = {
    # Graph RAG entities collection
    "graph_entities": {
        "name": "oracle_graph_entities",
        "description": "Entity embeddings from Graph RAG extraction",
        "dimension": 384,  # all-MiniLM-L6-v2 dimension
        "index_type": "IVF_FLAT",
        "metric_type": "COSINE",
        "nlist": 128,  # IVF_FLAT parameter
    },
    # Grok RAG document chunks collection
    "document_chunks": {
        "name": "oracle_document_chunks",
        "description": "Document chunk embeddings from Grok RAG ingestion",
        "dimension": 384,  # all-MiniLM-L6-v2 dimension
        "index_type": "IVF_FLAT",
        "metric_type": "COSINE",
        "nlist": 128,
    },
}

# ============================================================================
# Graph RAG Configuration
# ============================================================================
GRAPH_RAG_CONFIG = {
    # NER Model
    "ner_model": "dbmdz/bert-large-cased-finetuned-conll03-english",
    "ner_confidence_threshold": 0.7,
    # Relation Classifier
    "relation_model": "facebook/bart-large-mnli",
    "relation_confidence_threshold": 0.6,
    "candidate_relations": [
        "WORKS_FOR",
        "LOCATED_IN",
        "PART_OF",
        "CREATED_BY",
        "MANAGES",
        "USES",
        "DEPENDS_ON",
        "NONE",
    ],
    # Text Chunking
    "chunk_max_length": 512,  # words
    # Embedding Model
    "embedding_model": "all-MiniLM-L6-v2",
    "embedding_dimension": 384,
    # Neo4j Entity Storage
    "entity_label": "RagEntity",
    "relationship_type": "RAG_RELATION",
}

# ============================================================================
# Grok RAG Configuration (Document Ingestion)
# ============================================================================
GROK_RAG_CONFIG = {
    # Embedding Model (same as Graph RAG for consistency)
    "embedding_model": "all-MiniLM-L6-v2",
    "embedding_dimension": 384,
    # Text Chunking
    "chunk_size": 500,  # characters
    "chunk_overlap": 50,
    # OCR Configuration
    "tesseract_config": "--oem 3 --psm 6",  # LSTM OCR, assume uniform block of text
    # Supported File Types
    "supported_formats": [".pdf", ".docx", ".xlsx", ".xls", ".csv", ".txt", ".md"],
    # Processing Settings
    "max_file_size_mb": 100,
    "batch_size": 10,  # for embedding generation
}

# ============================================================================
# Retrieval Configuration
# ============================================================================
RETRIEVAL_CONFIG = {
    "default_top_k": 5,
    "max_top_k": 20,
    "min_similarity_threshold": 0.3,  # COSINE similarity
    "rerank_enabled": False,  # Future: add cross-encoder reranking
}

# ============================================================================
# LLM Configuration (for RAG generation)
# ============================================================================
LLM_CONFIG = {
    # Grok API (preferred)
    "grok_api_key": os.getenv("GROK_API_KEY", ""),
    "grok_model": "grok-beta",
    "grok_api_base": "https://api.x.ai/v1",
    # OpenAI API (fallback)
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "openai_model": "gpt-4",
    # Vertex AI (fallback for local Gemini)
    "google_project_id": "engaged-beaker-462422-r4",
    "google_location": "us-central1",
    "google_credentials_path": os.path.expanduser(
        "~/your-pattern/credentials/vertex-ai-key.json"
    ),
    # Generation Settings
    "max_tokens": 500,
    "temperature": 0.7,
    "fallback_order": [
        "grok",
        "openai",
        "vertex",
    ],  # Try Grok first, then OpenAI, then Vertex
}

# ============================================================================
# Logging Configuration
# ============================================================================
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": str(LOGS_DIR / "oracle_rag.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
    },
    "root": {"level": "DEBUG", "handlers": ["console", "file"]},
}

# ============================================================================
# Evidence & Validation Configuration (Mr.AI Framework Compliance)
# ============================================================================
VALIDATION_CONFIG = {
    # Gate 1: Functional Validation
    "test_sample_files": [
        RAW_DATA_DIR / "test_pdf.pdf",
        RAW_DATA_DIR / "test_docx.docx",
        RAW_DATA_DIR / "test_csv.csv",
    ],
    # Gate 2: Integration Validation
    "integration_tests": {
        "neo4j_connectivity": True,
        "milvus_connectivity": True,
        "collection_creation": True,
        "entity_insertion": True,
        "query_retrieval": True,
    },
    # Gate 3: Performance Validation
    "performance_benchmarks": {
        "document_processing_time_max_seconds": 30,
        "entity_extraction_per_chunk_max_seconds": 5,
        "retrieval_query_max_seconds": 2,
        "end_to_end_query_max_seconds": 10,
    },
    # Gate 4: Stability Validation
    "stability_tests": {
        "consecutive_runs_required": 3,
        "success_rate_threshold": 0.96,  # 96%+ as per Grok RAG requirement
    },
}

# ============================================================================
# SLIM Knowledge Base Integration (for H200 guidance)
# ============================================================================
SLIM_KNOWLEDGE_CONFIG = {
    "slim_docs_directory": Path("/home/jeremy/your-pattern/RAG-doc-data/SLIM-docs"),
    "mega_slim_agent_docs": Path(
        "/home/jeremy/your-pattern/RAG-doc-data/MEGA-SLIM-Agent"
    ),
    "priority_topics": [
        "peer-to-peer architecture",
        "agent-to-agent communication",
        "SLIM node deployment",
        "A2A framework integration",
        "protobuf dependencies",
        "message routing patterns",
    ],
}

# ============================================================================
# Export Configuration
# ============================================================================
__all__ = [
    "NEO4J_CONFIG",
    "MILVUS_CONFIG",
    "MILVUS_COLLECTIONS",
    "GRAPH_RAG_CONFIG",
    "GROK_RAG_CONFIG",
    "RETRIEVAL_CONFIG",
    "LLM_CONFIG",
    "LOGGING_CONFIG",
    "VALIDATION_CONFIG",
    "SLIM_KNOWLEDGE_CONFIG",
    "BASE_DIR",
    "DATA_DIR",
    "RAW_DATA_DIR",
    "PROCESSED_DATA_DIR",
    "LOGS_DIR",
]
