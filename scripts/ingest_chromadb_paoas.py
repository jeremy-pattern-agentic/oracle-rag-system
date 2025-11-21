#!/usr/bin/env python3
"""
GPU-Accelerated ChromaDB → PAOAS Ingestion Script

Processes 8,870 ChromaDB documents through Graph RAG pipeline with:
- GPU acceleration (RTX 5060 Ti)
- Entity/relationship extraction
- Neo4j + Milvus storage
- Quality gate validation
- Performance monitoring

Work Order: GPU_CHROMADB_PAOAS_INGESTION.md
Captain: Jeremy
Date: 2025-11-16
"""

import json
import logging
import time
import sys
from pathlib import Path
from typing import Dict, List, Any
import subprocess
from datetime import datetime

# Add src and config to path
base_dir = Path(__file__).parent.parent
sys.path.insert(0, str(base_dir / "src"))
sys.path.insert(0, str(base_dir))

from graph_rag.pipeline import GraphRAGPipeline
import config.config as config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/tmp/paoas_ingestion_full.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class GPUMonitor:
    """Monitor GPU metrics during ingestion."""

    @staticmethod
    def get_gpu_stats() -> Dict[str, Any]:
        """Get current GPU statistics from nvidia-smi."""
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=index,name,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.total",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse output: 0, NVIDIA GeForce RTX 5060 Ti, 33, 0, 0, 4, 16311
            parts = result.stdout.strip().split(", ")

            return {
                "gpu_index": int(parts[0]),
                "gpu_name": parts[1],
                "temperature_c": int(parts[2]),
                "gpu_utilization_pct": int(parts[3]),
                "memory_utilization_pct": int(parts[4]),
                "memory_used_mb": int(parts[5]),
                "memory_total_mb": int(parts[6]),
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.warning(f"Failed to get GPU stats: {e}")
            return {}

    @staticmethod
    def log_gpu_stats(batch_num: int):
        """Log GPU statistics."""
        stats = GPUMonitor.get_gpu_stats()
        if stats:
            logger.info(
                f"[GPU] Batch {batch_num}: "
                f"{stats['gpu_utilization_pct']}% util, "
                f"{stats['memory_used_mb']}MB/{stats['memory_total_mb']}MB VRAM, "
                f"{stats['temperature_c']}°C"
            )
        return stats


def load_prepared_documents(
    input_path: Path, limit: int = None
) -> List[Dict[str, Any]]:
    """
    Load prepared ChromaDB documents from JSON.

    Args:
        input_path: Path to prepared documents JSON file
        limit: Optional limit for testing (e.g., 50 for dry run)

    Returns:
        List of documents ready for processing
    """
    logger.info(f"Loading prepared documents from: {input_path}")

    with open(input_path, "r") as f:
        docs = json.load(f)

    if limit:
        docs = docs[:limit]
        logger.info(f"Limited to {limit} documents for testing")

    logger.info(f"Loaded {len(docs)} documents")
    return docs


def process_batch(
    pipeline: GraphRAGPipeline,
    batch: List[Dict[str, Any]],
    batch_num: int,
    total_batches: int,
    start_idx: int,
) -> Dict[str, Any]:
    """
    Process a batch of documents through Graph RAG pipeline.

    Args:
        pipeline: Initialized GraphRAGPipeline
        batch: List of documents to process
        batch_num: Current batch number
        total_batches: Total number of batches
        start_idx: Starting document index in full dataset

    Returns:
        Statistics for this batch including errors
    """
    logger.info(f"\n{'=' * 70}")
    logger.info(
        f"BATCH {batch_num}/{total_batches} - Documents {start_idx + 1}-{start_idx + len(batch)}"
    )
    logger.info(f"{'=' * 70}")

    batch_stats = {
        "documents_processed": 0,
        "documents_failed": 0,
        "entities_extracted": 0,
        "entities_stored_neo4j": 0,
        "entities_stored_milvus": 0,
        "relations_found": 0,
        "relations_stored": 0,
        "processing_time": 0,
        "errors": [],
    }

    batch_start = time.time()

    # Get GPU stats at batch start
    gpu_start = GPUMonitor.get_gpu_stats()

    for idx, doc in enumerate(batch):
        doc_id = start_idx + idx + 1
        try:
            doc_start = time.time()

            # Process through Graph RAG (only pass text, not metadata)
            result = pipeline.process_text(text=doc["text"])

            doc_time = time.time() - doc_start

            batch_stats["documents_processed"] += 1
            batch_stats["entities_extracted"] += result.get("entities_extracted", 0)
            batch_stats["entities_stored_neo4j"] += result.get(
                "entities_stored_neo4j", 0
            )
            batch_stats["entities_stored_milvus"] += result.get(
                "entities_stored_milvus", 0
            )
            batch_stats["relations_found"] += result.get("relations_found", 0)
            batch_stats["relations_stored"] += result.get("relations_stored", 0)

            logger.info(
                f"  ✓ [{doc_id}/{start_idx + len(batch)}] "
                f"Entities: {result.get('entities_extracted', 0)} extracted, "
                f"{result.get('entities_stored_neo4j', 0)} stored | "
                f"Relations: {result.get('relations_found', 0)} found, "
                f"{result.get('relations_stored', 0)} stored | "
                f"Time: {doc_time:.2f}s"
            )

        except Exception as e:
            batch_stats["documents_failed"] += 1
            error_msg = f"Doc {doc_id}: {str(e)[:100]}"
            batch_stats["errors"].append(error_msg)
            logger.error(f"  ✗ [{doc_id}] Error: {e}")
            continue

    batch_stats["processing_time"] = time.time() - batch_start

    # Get GPU stats at batch end
    gpu_end = GPUMonitor.log_gpu_stats(batch_num)

    # Log batch summary
    success_rate = (batch_stats["documents_processed"] / len(batch)) * 100
    docs_per_sec = batch_stats["documents_processed"] / batch_stats["processing_time"]

    logger.info(f"\n{'=' * 70}")
    logger.info(f"BATCH {batch_num} SUMMARY")
    logger.info(f"{'=' * 70}")
    logger.info(
        f"Success: {batch_stats['documents_processed']}/{len(batch)} docs ({success_rate:.1f}%)"
    )
    logger.info(
        f"Entities: {batch_stats['entities_extracted']} extracted, {batch_stats['entities_stored_neo4j']} in Neo4j, {batch_stats['entities_stored_milvus']} in Milvus"
    )
    logger.info(
        f"Relations: {batch_stats['relations_found']} found, {batch_stats['relations_stored']} stored"
    )
    logger.info(f"Performance: {docs_per_sec:.2f} docs/sec")
    logger.info(f"Time: {batch_stats['processing_time']:.2f}s")

    if batch_stats["documents_failed"] > 0:
        logger.warning(f"Errors: {batch_stats['documents_failed']} documents failed")

    return batch_stats


def save_progress(progress_path: Path, stats: Dict[str, Any]):
    """Save ingestion progress to JSON file."""
    with open(progress_path, "w") as f:
        json.dump(stats, f, indent=2)
    logger.debug(f"Progress saved to {progress_path}")


def validate_storage(pipeline: GraphRAGPipeline) -> Dict[str, int]:
    """
    Validate entities and vectors are stored correctly.

    Returns:
        Dict with neo4j_entities, neo4j_relationships, milvus_entities counts
    """
    logger.info("\n" + "=" * 70)
    logger.info("VALIDATING STORAGE")
    logger.info("=" * 70)

    stats = pipeline.get_statistics()

    logger.info(f"Neo4j Entities: {stats.get('neo4j_entities', 0)}")
    logger.info(f"Neo4j Relationships: {stats.get('neo4j_relationships', 0)}")
    logger.info(f"Milvus Entities: {stats.get('milvus_entities', 0)}")

    return stats


def main():
    """Main execution: Ingest ChromaDB documents into PAOAS."""
    import argparse

    parser = argparse.ArgumentParser(
        description="GPU-Accelerated ChromaDB → PAOAS Ingestion"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/chromadb_prepared.json"),
        help="Path to prepared documents JSON",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of documents per batch (default: 10)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of documents (for testing, e.g., 50 for dry run)",
    )
    parser.add_argument(
        "--progress-file",
        type=Path,
        default=Path("/tmp/paoas_ingestion_progress.json"),
        help="Path to save progress",
    )
    parser.add_argument(
        "--start-from", type=int, default=0, help="Resume from document index"
    )
    parser.add_argument(
        "--gpu-log-interval",
        type=int,
        default=5,
        help="Log GPU stats every N batches (default: 5)",
    )

    args = parser.parse_args()

    # Header
    logger.info("\n" + "=" * 70)
    logger.info("GPU-ACCELERATED CHROMADB → PAOAS INGESTION")
    logger.info("=" * 70)
    logger.info("Work Order: GPU_CHROMADB_PAOAS_INGESTION.md")
    logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Input: {args.input}")
    logger.info(f"Batch Size: {args.batch_size}")
    logger.info(f"Limit: {args.limit or 'None (full run)'}")
    logger.info("=" * 70)

    # Initial GPU check
    logger.info("\n" + "=" * 70)
    logger.info("GPU VALIDATION")
    logger.info("=" * 70)
    gpu_stats = GPUMonitor.get_gpu_stats()
    if gpu_stats:
        logger.info(f"✓ GPU Detected: {gpu_stats['gpu_name']}")
        logger.info(f"  VRAM: {gpu_stats['memory_total_mb']}MB total")
        logger.info(f"  Temperature: {gpu_stats['temperature_c']}°C")
    else:
        logger.error("✗ GPU not detected! Aborting.")
        sys.exit(1)

    # Load documents
    logger.info("\n" + "=" * 70)
    logger.info("LOADING DOCUMENTS")
    logger.info("=" * 70)

    docs = load_prepared_documents(args.input, limit=args.limit)

    # Apply start-from filter
    if args.start_from > 0:
        logger.info(f"Resuming from document {args.start_from}")
        docs = docs[args.start_from :]

    total_docs = len(docs)
    total_batches = (total_docs + args.batch_size - 1) // args.batch_size

    logger.info(f"Documents to process: {total_docs}")
    logger.info(f"Batches: {total_batches}")

    # Initialize Graph RAG pipeline
    logger.info("\n" + "=" * 70)
    logger.info("INITIALIZING GRAPH RAG PIPELINE")
    logger.info("=" * 70)

    try:
        # Note: We need to pass collection_config separately
        pipeline = GraphRAGPipeline(
            neo4j_config=config.NEO4J_CONFIG,
            milvus_config=config.MILVUS_CONFIG,
            collection_config=config.MILVUS_COLLECTIONS["graph_entities"],
            graph_rag_config=config.GRAPH_RAG_CONFIG,
        )
        logger.info("✓ Pipeline initialized (GPU-accelerated)")

        # Log GPU stats after model loading
        logger.info("\n" + "=" * 70)
        logger.info("GPU STATUS AFTER MODEL LOADING")
        logger.info("=" * 70)
        GPUMonitor.log_gpu_stats(0)

    except Exception as e:
        logger.error(f"✗ Failed to initialize pipeline: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    # Initialize overall stats
    overall_stats = {
        "start_time": datetime.now().isoformat(),
        "total_documents": total_docs,
        "documents_processed": 0,
        "documents_failed": 0,
        "entities_extracted": 0,
        "entities_stored_neo4j": 0,
        "entities_stored_milvus": 0,
        "relations_found": 0,
        "relations_stored": 0,
        "total_processing_time": 0,
        "batches_completed": 0,
        "gpu_metrics": [],
        "errors": [],
    }

    # Process batches
    logger.info("\n" + "=" * 70)
    logger.info("PROCESSING BATCHES")
    logger.info("=" * 70)

    start_time = time.time()

    for batch_num in range(total_batches):
        batch_start_idx = batch_num * args.batch_size
        batch_end_idx = min(batch_start_idx + args.batch_size, total_docs)
        batch = docs[batch_start_idx:batch_end_idx]

        try:
            batch_stats = process_batch(
                pipeline,
                batch,
                batch_num + 1,
                total_batches,
                args.start_from + batch_start_idx,
            )

            # Update overall stats
            overall_stats["documents_processed"] += batch_stats["documents_processed"]
            overall_stats["documents_failed"] += batch_stats["documents_failed"]
            overall_stats["entities_extracted"] += batch_stats["entities_extracted"]
            overall_stats["entities_stored_neo4j"] += batch_stats[
                "entities_stored_neo4j"
            ]
            overall_stats["entities_stored_milvus"] += batch_stats[
                "entities_stored_milvus"
            ]
            overall_stats["relations_found"] += batch_stats["relations_found"]
            overall_stats["relations_stored"] += batch_stats["relations_stored"]
            overall_stats["total_processing_time"] += batch_stats["processing_time"]
            overall_stats["batches_completed"] += 1
            overall_stats["errors"].extend(batch_stats["errors"])

            # Save progress
            overall_stats["last_processed_index"] = args.start_from + batch_end_idx
            save_progress(args.progress_file, overall_stats)

            # Log GPU metrics periodically
            if (batch_num + 1) % args.gpu_log_interval == 0:
                gpu_stats = GPUMonitor.get_gpu_stats()
                if gpu_stats:
                    overall_stats["gpu_metrics"].append(gpu_stats)

        except Exception as e:
            logger.error(f"✗ Error processing batch {batch_num + 1}: {e}")
            import traceback

            traceback.print_exc()
            logger.info("Progress saved. Resume with --start-from flag")
            break

    overall_stats["end_time"] = datetime.now().isoformat()
    overall_stats["total_time"] = time.time() - start_time

    # Validate storage
    storage_stats = validate_storage(pipeline)
    overall_stats["final_storage_counts"] = storage_stats

    # Close pipeline
    pipeline.close()
    logger.info("✓ Pipeline closed")

    # Final summary
    logger.info("\n" + "=" * 70)
    logger.info("INGESTION COMPLETE")
    logger.info("=" * 70)
    logger.info(
        f"Documents: {overall_stats['documents_processed']}/{overall_stats['total_documents']} processed ({overall_stats['documents_failed']} failed)"
    )

    success_rate = (
        overall_stats["documents_processed"] / overall_stats["total_documents"]
    ) * 100
    error_rate = (
        overall_stats["documents_failed"] / overall_stats["total_documents"]
    ) * 100

    logger.info(f"Success Rate: {success_rate:.1f}%")
    logger.info(f"Error Rate: {error_rate:.1f}%")
    logger.info("")
    logger.info(f"Entities Extracted: {overall_stats['entities_extracted']}")
    logger.info(f"Entities in Neo4j: {overall_stats['entities_stored_neo4j']}")
    logger.info(f"Entities in Milvus: {overall_stats['entities_stored_milvus']}")
    logger.info(f"Relations Found: {overall_stats['relations_found']}")
    logger.info(f"Relations Stored: {overall_stats['relations_stored']}")
    logger.info("")
    logger.info(f"Total Time: {overall_stats['total_time']:.2f}s")

    if overall_stats["documents_processed"] > 0:
        avg_time = overall_stats["total_time"] / overall_stats["documents_processed"]
        throughput = overall_stats["documents_processed"] / overall_stats["total_time"]
        logger.info(f"Avg Time/Doc: {avg_time:.2f}s")
        logger.info(f"Throughput: {throughput:.2f} docs/sec")

    logger.info("")
    logger.info("Storage Validation:")
    logger.info(f"  Neo4j Entities: {storage_stats.get('neo4j_entities', 0)}")
    logger.info(f"  Neo4j Relationships: {storage_stats.get('neo4j_relationships', 0)}")
    logger.info(f"  Milvus Entities: {storage_stats.get('milvus_entities', 0)}")

    # Quality Gate Assessment
    logger.info("\n" + "=" * 70)
    logger.info("QUALITY GATE ASSESSMENT")
    logger.info("=" * 70)

    # Gate 1: Functional
    gate1_pass = (
        overall_stats["documents_processed"] >= 10
        and len(overall_stats["gpu_metrics"]) > 0
    )
    logger.info(f"Gate 1 (Functional): {'✓ PASS' if gate1_pass else '✗ FAIL'}")
    logger.info(
        f"  - Documents processed: {overall_stats['documents_processed']} >= 10"
    )
    logger.info(f"  - GPU detected: {len(overall_stats['gpu_metrics']) > 0}")

    # Gate 2: Integration
    gate2_pass = (
        storage_stats.get("neo4j_entities", 0) > 0
        and storage_stats.get("milvus_entities", 0) > 0
    )
    logger.info(f"Gate 2 (Integration): {'✓ PASS' if gate2_pass else '✗ FAIL'}")
    logger.info(f"  - Neo4j entities: {storage_stats.get('neo4j_entities', 0)} > 0")
    logger.info(f"  - Milvus entities: {storage_stats.get('milvus_entities', 0)} > 0")

    # Gate 3: Performance
    avg_gpu_util = 0
    max_vram = 0
    if overall_stats["gpu_metrics"]:
        avg_gpu_util = sum(
            m["gpu_utilization_pct"] for m in overall_stats["gpu_metrics"]
        ) / len(overall_stats["gpu_metrics"])
        max_vram = max(m["memory_used_mb"] for m in overall_stats["gpu_metrics"])

    throughput = (
        overall_stats["documents_processed"] / overall_stats["total_time"]
        if overall_stats["total_time"] > 0
        else 0
    )

    gate3_pass = (
        max_vram > 2000  # > 2GB VRAM
        and throughput > 0.5  # > 0.5 docs/sec
        and avg_gpu_util > 20  # > 20% avg utilization
    )
    logger.info(f"Gate 3 (Performance): {'✓ PASS' if gate3_pass else '✗ FAIL'}")
    logger.info(f"  - Max VRAM: {max_vram}MB > 2000MB")
    logger.info(f"  - Throughput: {throughput:.2f} docs/sec > 0.5")
    logger.info(f"  - Avg GPU util: {avg_gpu_util:.1f}% > 20%")

    # Gate 4: Stability
    gate4_pass = (
        error_rate < 5.0 and overall_stats["batches_completed"] == total_batches
    )
    logger.info(f"Gate 4 (Stability): {'✓ PASS' if gate4_pass else '✗ FAIL'}")
    logger.info(f"  - Error rate: {error_rate:.1f}% < 5%")
    logger.info(
        f"  - All batches completed: {overall_stats['batches_completed']}/{total_batches}"
    )

    overall_pass = gate1_pass and gate2_pass and gate3_pass and gate4_pass
    logger.info(
        f"\nOVERALL: {'✓✓✓ ALL GATES PASSED ✓✓✓' if overall_pass else '✗ QUALITY GATES FAILED'}"
    )

    # Save final stats
    save_progress(args.progress_file, overall_stats)
    logger.info(f"\nFinal progress saved to: {args.progress_file}")
    logger.info("Full log available at: /tmp/paoas_ingestion_full.log")

    if not overall_pass:
        logger.warning("\n⚠️  Quality gates not met. Review logs and retry.")
        sys.exit(1)

    if overall_stats["documents_processed"] == overall_stats["total_documents"]:
        logger.info("\n✅ ALL DOCUMENTS SUCCESSFULLY INGESTED INTO PAOAS!")
    else:
        logger.warning(
            f"\n⚠️  Partial completion: {overall_stats['documents_processed']}/{overall_stats['total_documents']}"
        )
        logger.info(
            f"   Resume with: --start-from {overall_stats['last_processed_index']}"
        )


if __name__ == "__main__":
    main()
