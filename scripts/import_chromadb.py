#!/usr/bin/env python3
"""
ChromaDB to PAOAS Import Pipeline

Reads exported ChromaDB collections and prepares them for Graph RAG ingestion.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any
import sys
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle numpy arrays and types."""

    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        return super().default(obj)


def read_chromadb_sqlite(chroma_path: Path) -> Dict[str, Any]:
    """
    Read ChromaDB collections from SQLite export.

    Args:
        chroma_path: Path to ChromaDB directory or sqlite file

    Returns:
        Dictionary of collections with documents, embeddings, metadata
    """
    try:
        import chromadb
        from chromadb.config import Settings

        # Initialize ChromaDB client in read-only mode
        logger.info(f"Opening ChromaDB at: {chroma_path}")

        if chroma_path.is_dir():
            # Directory-based ChromaDB
            client = chromadb.PersistentClient(path=str(chroma_path))
        else:
            # Single SQLite file
            client = chromadb.PersistentClient(path=str(chroma_path.parent))

        collections = client.list_collections()
        logger.info(f"Found {len(collections)} collections")

        data = {}
        total_docs = 0

        for collection in collections:
            coll_name = collection.name
            logger.info(f"Reading collection: {coll_name}")

            coll = client.get_collection(coll_name)

            # Get all documents with metadata and embeddings
            results = coll.get(include=["documents", "embeddings", "metadatas"])

            doc_count = (
                len(results["documents"]) if results["documents"] is not None else 0
            )
            total_docs += doc_count

            data[coll_name] = {
                "documents": results["documents"]
                if results["documents"] is not None
                else [],
                "embeddings": results["embeddings"]
                if results["embeddings"] is not None
                else [],
                "metadatas": results["metadatas"]
                if results["metadatas"] is not None
                else [],
                "count": doc_count,
            }

            logger.info(f"  Loaded {doc_count} documents from {coll_name}")

        logger.info(f"Total documents across all collections: {total_docs}")
        return data

    except ImportError:
        logger.error(
            "chromadb package not installed. Install with: pip install chromadb"
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading ChromaDB: {e}")
        raise


def export_to_json(chromadb_data: Dict[str, Any], output_path: Path):
    """
    Export ChromaDB data to JSON for inspection/backup.

    Args:
        chromadb_data: Dictionary of ChromaDB collections
        output_path: Path to save JSON export
    """
    logger.info(f"Exporting to JSON: {output_path}")

    # Create lightweight export (without embeddings to save space)
    export_data = {}
    for coll_name, coll_data in chromadb_data.items():
        export_data[coll_name] = {
            "count": coll_data["count"],
            "documents": coll_data["documents"],
            "metadatas": coll_data["metadatas"],
            # Embeddings are large - skip in JSON export
            "embeddings_shape": [
                len(coll_data["embeddings"]),
                len(coll_data["embeddings"][0])
                if len(coll_data["embeddings"]) > 0
                else 0,
            ],
        }

    with open(output_path, "w") as f:
        json.dump(export_data, f, indent=2, cls=NumpyEncoder)

    logger.info(
        f"JSON export complete: {output_path.stat().st_size / 1024 / 1024:.2f} MB"
    )


def prepare_for_graph_rag(chromadb_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Prepare ChromaDB documents for Graph RAG pipeline ingestion.

    Args:
        chromadb_data: Dictionary of ChromaDB collections

    Returns:
        List of documents ready for Graph RAG processing
    """
    logger.info("Preparing documents for Graph RAG pipeline...")

    prepared_docs = []

    for coll_name, coll_data in chromadb_data.items():
        for idx in range(coll_data["count"]):
            doc = {
                "text": coll_data["documents"][idx],
                "metadata": {
                    "source_collection": coll_name,
                    "source_index": idx,
                    "import_source": "chromadb_h200_openwebui",
                    **coll_data["metadatas"][idx],  # Preserve original metadata
                },
                # Original embedding (will be replaced by Graph RAG's embedding model)
                "original_embedding": coll_data["embeddings"][idx]
                if len(coll_data["embeddings"]) > 0
                else None,
            }
            prepared_docs.append(doc)

    logger.info(f"Prepared {len(prepared_docs)} documents for Graph RAG")
    return prepared_docs


def main():
    """
    Main execution: Read ChromaDB and prepare for PAOAS ingestion.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Import ChromaDB collections into PAOAS"
    )
    parser.add_argument(
        "--chromadb-path",
        type=Path,
        required=True,
        help="Path to ChromaDB directory or sqlite file",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional: Export to JSON for inspection",
    )
    parser.add_argument(
        "--output-prepared",
        type=Path,
        default=Path("data/chromadb_prepared.json"),
        help="Output path for prepared documents",
    )

    args = parser.parse_args()

    # Validate input path
    if not args.chromadb_path.exists():
        logger.error(f"ChromaDB path not found: {args.chromadb_path}")
        sys.exit(1)

    # Read ChromaDB
    logger.info("=" * 70)
    logger.info("CHROMADB TO PAOAS IMPORT - PHASE 1: EXPORT")
    logger.info("=" * 70)

    chromadb_data = read_chromadb_sqlite(args.chromadb_path)

    # Optional: Export to JSON for inspection
    if args.output_json:
        export_to_json(chromadb_data, args.output_json)

    # Prepare for Graph RAG
    logger.info("")
    logger.info("=" * 70)
    logger.info("CHROMADB TO PAOAS IMPORT - PHASE 2: PREPARATION")
    logger.info("=" * 70)

    prepared_docs = prepare_for_graph_rag(chromadb_data)

    # Save prepared documents
    args.output_prepared.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_prepared, "w") as f:
        json.dump(prepared_docs, f, indent=2, cls=NumpyEncoder)

    logger.info(f"Prepared documents saved to: {args.output_prepared}")

    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Collections processed: {len(chromadb_data)}")
    logger.info(f"Total documents: {len(prepared_docs)}")
    logger.info(f"Output file: {args.output_prepared}")
    logger.info("")
    logger.info("✅ Ready for Graph RAG ingestion!")
    logger.info("   Next: Run scripts/ingest_chromadb_to_paoas.py")


if __name__ == "__main__":
    main()
