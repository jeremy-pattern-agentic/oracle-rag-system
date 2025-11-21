#!/usr/bin/env python3
"""
Ingest ChromaDB documents into PAOAS Graph RAG system.

Processes prepared ChromaDB documents through the Graph RAG pipeline,
extracting entities, classifying relationships, and storing in Neo4j + Milvus.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from graph_rag.pipeline import GraphRAGPipeline
import config.config as config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_prepared_documents(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load prepared ChromaDB documents from JSON.

    Args:
        input_path: Path to prepared documents JSON file

    Returns:
        List of documents ready for processing
    """
    logger.info(f"Loading prepared documents from: {input_path}")

    with open(input_path, 'r') as f:
        docs = json.load(f)

    logger.info(f"Loaded {len(docs)} documents")
    return docs


def process_batch(
    pipeline: GraphRAGPipeline,
    batch: List[Dict[str, Any]],
    batch_num: int,
    total_batches: int
) -> Dict[str, int]:
    """
    Process a batch of documents through Graph RAG pipeline.

    Args:
        pipeline: Initialized GraphRAGPipeline
        batch: List of documents to process
        batch_num: Current batch number
        total_batches: Total number of batches

    Returns:
        Statistics for this batch
    """
    logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} documents)")

    batch_stats = {
        'documents_processed': 0,
        'entities_extracted': 0,
        'relations_found': 0,
        'processing_time': 0
    }

    batch_start = time.time()

    for idx, doc in enumerate(batch):
        try:
            doc_start = time.time()

            # Process through Graph RAG
            result = pipeline.process_text(
                text=doc['text'],
                metadata=doc['metadata']
            )

            doc_time = time.time() - doc_start

            batch_stats['documents_processed'] += 1
            batch_stats['entities_extracted'] += result.get('entities_extracted', 0)
            batch_stats['relations_found'] += result.get('relations_found', 0)

            logger.info(
                f"  [{idx+1}/{len(batch)}] Processed: "
                f"{result.get('entities_extracted', 0)} entities, "
                f"{result.get('relations_found', 0)} relations "
                f"({doc_time:.2f}s)"
            )

        except Exception as e:
            logger.error(f"Error processing document {idx}: {e}")
            continue

    batch_stats['processing_time'] = time.time() - batch_start

    logger.info(
        f"Batch {batch_num} complete: "
        f"{batch_stats['entities_extracted']} entities, "
        f"{batch_stats['relations_found']} relations "
        f"({batch_stats['processing_time']:.2f}s)"
    )

    return batch_stats


def save_progress(progress_path: Path, stats: Dict[str, Any]):
    """
    Save migration progress to JSON file.

    Args:
        progress_path: Path to progress file
        stats: Current migration statistics
    """
    with open(progress_path, 'w') as f:
        json.dump(stats, f, indent=2)


def main():
    """
    Main execution: Ingest ChromaDB documents into PAOAS.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Ingest ChromaDB documents into PAOAS Graph RAG'
    )
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('data/chromadb_prepared.json'),
        help='Path to prepared documents JSON'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=10,
        help='Number of documents to process per batch (default: 10)'
    )
    parser.add_argument(
        '--progress-file',
        type=Path,
        default=Path('data/migration_progress.json'),
        help='Path to save progress (default: data/migration_progress.json)'
    )
    parser.add_argument(
        '--start-from',
        type=int,
        default=0,
        help='Start from document index (for resuming)'
    )

    args = parser.parse_args()

    # Load prepared documents
    logger.info("=" * 70)
    logger.info("CHROMADB TO PAOAS INGESTION")
    logger.info("=" * 70)

    docs = load_prepared_documents(args.input)

    # Apply start-from filter
    if args.start_from > 0:
        logger.info(f"Resuming from document {args.start_from}")
        docs = docs[args.start_from:]

    total_docs = len(docs)
    total_batches = (total_docs + args.batch_size - 1) // args.batch_size

    logger.info(f"Total documents to process: {total_docs}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Total batches: {total_batches}")
    logger.info("")

    # Initialize Graph RAG pipeline
    logger.info("Initializing Graph RAG pipeline...")
    try:
        pipeline = GraphRAGPipeline(
            neo4j_config=config.NEO4J_CONFIG,
            milvus_config=config.MILVUS_CONFIG,
            graph_rag_config=config.GRAPH_RAG_CONFIG
        )
        logger.info("✅ Pipeline initialized (GPU-accelerated)")
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")
        sys.exit(1)

    # Process in batches
    logger.info("")
    logger.info("=" * 70)
    logger.info("PROCESSING BATCHES")
    logger.info("=" * 70)

    overall_stats = {
        'total_documents': total_docs,
        'documents_processed': 0,
        'entities_extracted': 0,
        'relations_found': 0,
        'total_processing_time': 0,
        'batches_completed': 0
    }

    start_time = time.time()

    for batch_num in range(total_batches):
        batch_start_idx = batch_num * args.batch_size
        batch_end_idx = min(batch_start_idx + args.batch_size, total_docs)
        batch = docs[batch_start_idx:batch_end_idx]

        try:
            batch_stats = process_batch(pipeline, batch, batch_num + 1, total_batches)

            # Update overall stats
            overall_stats['documents_processed'] += batch_stats['documents_processed']
            overall_stats['entities_extracted'] += batch_stats['entities_extracted']
            overall_stats['relations_found'] += batch_stats['relations_found']
            overall_stats['total_processing_time'] += batch_stats['processing_time']
            overall_stats['batches_completed'] += 1

            # Save progress
            overall_stats['last_processed_index'] = args.start_from + batch_end_idx
            save_progress(args.progress_file, overall_stats)

        except Exception as e:
            logger.error(f"Error processing batch {batch_num + 1}: {e}")
            logger.info("Progress saved. You can resume with --start-from flag")
            break

    overall_stats['total_time'] = time.time() - start_time

    # Close pipeline
    pipeline.close()

    # Final summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("MIGRATION COMPLETE")
    logger.info("=" * 70)
    logger.info(f"Documents processed:    {overall_stats['documents_processed']}/{overall_stats['total_documents']}")
    logger.info(f"Entities extracted:     {overall_stats['entities_extracted']}")
    logger.info(f"Relations found:        {overall_stats['relations_found']}")
    logger.info(f"Total processing time:  {overall_stats['total_time']:.2f}s")
    logger.info(f"Avg time per document:  {overall_stats['total_time']/overall_stats['documents_processed']:.2f}s")
    logger.info("")

    if overall_stats['documents_processed'] == overall_stats['total_documents']:
        logger.info("✅ All documents successfully ingested into PAOAS!")
    else:
        logger.warning(f"⚠️  Partial completion: {overall_stats['documents_processed']}/{overall_stats['total_documents']}")
        logger.info(f"   Resume with: --start-from {overall_stats['last_processed_index']}")

    # Save final stats
    save_progress(args.progress_file, overall_stats)


if __name__ == '__main__':
    main()
