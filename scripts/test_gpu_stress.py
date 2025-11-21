#!/usr/bin/env python3
"""Quick GPU stress test - load models and process a few docs"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import json
import torch
from graph_rag.pipeline import GraphRAGPipeline
import config.config as config

print("=" * 70)
print("GPU STRESS TEST - Loading Models")
print("=" * 70)

# Check CUDA
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")

# Initialize pipeline (this loads all 3 models to GPU)
print("\nInitializing Graph RAG pipeline...")
pipeline = GraphRAGPipeline(
    neo4j_config=config.NEO4J_CONFIG,
    milvus_config=config.MILVUS_CONFIG,
    collection_config=config.MILVUS_COLLECTIONS['graph_entities'],
    graph_rag_config=config.GRAPH_RAG_CONFIG
)
print("✅ Pipeline initialized")

# Load a few docs
print("\nLoading sample documents...")
with open("/home/jeremy/oracle-rag-system/data/chromadb_prepared.json") as f:
    docs = json.load(f)

print(f"Total docs available: {len(docs):,}")

# Process first 20 docs
print("\nProcessing first 20 documents with GPU...")
for i, doc in enumerate(docs[:20], 1):
    result = pipeline.process_text(doc['text'], doc['metadata'])
    print(f"  Doc {i}/20: {result.get('entities_count', 0)} entities, "
          f"{result.get('relations_count', 0)} relations")

print("\n✅ GPU stress test complete!")
print("Check nvtop/nvidia-smi for GPU utilization")
