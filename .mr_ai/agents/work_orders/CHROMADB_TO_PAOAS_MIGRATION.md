# Work Order: ChromaDB to PAOAS Migration

**Agent**: Data Migration Specialist
**Orchestrator**: Oracle Sonnet
**Project**: PAOAS - Pattern Agentic Oracle Archival System
**Date**: 2025-11-16
**Priority**: HIGH (Unblocks H200's SLIM integration)

---

## 🎯 Mission

Migrate all Pattern Agentic institutional knowledge from H200's OpenWebUI ChromaDB to Oracle's PAOAS (Graph RAG + Neo4j + Milvus), creating a permanent, relationship-aware knowledge repository.

---

## 📊 Current State (Evidence-Based)

### **Source: H200's OpenWebUI ChromaDB**
```
Location: pa-inference-prime (10.1.10.82)
Container: OpenWebUI Docker container
Database: ChromaDB (vector embeddings)
Knowledge Domains:
  - SLIM (Serverless Language Interaction Model)
  - DLE V4 (Dynamic Learning Engine patterns)
  - Mr.AI Framework (orchestrator/agent methodology)
  - Pattern Agentic institutional docs
```

### **Destination: Oracle's PAOAS**
```
Location: pa-inference-1 (10.1.10.161)
Infrastructure:
  ✅ Graph RAG Pipeline (GPU-accelerated, 8.4x speedup)
  ✅ Neo4j 5.15.0 (yourpattern database, 56 nodes)
  ✅ Milvus Lite (vector storage, file-based)
  ✅ RTX 5060 Ti 16GB (tensor cores operational)
```

**Strategic Value:**
- H200 has *used* this knowledge for DLE V4 work
- Oracle *preserves* it permanently with Graph RAG
- Neo4j adds relationship awareness (beyond pure vectors)
- Survives mindwipes, compactions, restarts
- Serves entire Pattern Agentic dev team + agent fleet

---

## 🔧 Phase 1: ChromaDB Export from H200

### **Tasks:**

**1.1 Locate ChromaDB on pa-inference-prime**
```bash
# SSH to H200's server
ssh pa-inference-prime

# Find OpenWebUI container
docker ps | grep webui

# Inspect volume mounts to find ChromaDB location
docker inspect <webui-container> | grep -A 10 "Mounts"

# Expected ChromaDB path (typical OpenWebUI setup):
# /app/backend/data/vector_db/chroma.sqlite3
# OR
# /root/.cache/chroma/
```

**1.2 Export ChromaDB Collections**
```bash
# Option A: Direct file copy (if ChromaDB is file-based)
docker cp <webui-container>:/path/to/chroma.sqlite3 ./chroma_export/

# Option B: Export via ChromaDB API (if running)
# Use ChromaDB client to export collections as JSON/parquet
```

**1.3 Transfer to Oracle (pa-inference-1)**
```bash
# Via SCP over Tailscale network
scp -r chroma_export/ jeremy@10.1.10.161:/home/jeremy/oracle-rag-system/data/chromadb_import/

# OR via shared network mount if available
```

### **Evidence Required:**
- ✅ ChromaDB file/directory path confirmed
- ✅ Export file size and collection count
- ✅ Transfer completion verification (checksums match)

**STOP POINT**: Do NOT proceed to Phase 2 until export is verified on Oracle's filesystem.

---

## 🔄 Phase 2: ChromaDB to Graph RAG Conversion

### **Conceptual Architecture:**

**ChromaDB Structure:**
```
ChromaDB (vector-only)
├─ Collection 1: SLIM docs
│  ├─ Document chunks (text)
│  ├─ Embeddings (vectors)
│  └─ Metadata (source, page, etc.)
├─ Collection 2: DLE V4 docs
└─ Collection 3: Mr.AI Framework docs
```

**PAOAS Structure (enhanced):**
```
PAOAS (vectors + relationships)
├─ Neo4j Graph
│  ├─ Entities (SLIM, IBM Research, A2A, etc.)
│  ├─ Relationships (USES, DEPENDS_ON, IMPLEMENTS)
│  └─ Document nodes (source tracking)
├─ Milvus Vectors
│  ├─ Entity embeddings
│  └─ Chunk embeddings
└─ Metadata layer
   └─ Source provenance (from ChromaDB)
```

### **Tasks:**

**2.1 Create ChromaDB Reader Script**
```python
# File: scripts/import_chromadb.py

import chromadb
from chromadb.config import Settings
from pathlib import Path

def read_chromadb_collections(chroma_path: str):
    """
    Read all collections from exported ChromaDB.

    Returns:
        Dict of collections with documents, embeddings, metadata
    """
    client = chromadb.PersistentClient(path=chroma_path)
    collections = client.list_collections()

    data = {}
    for collection in collections:
        coll = client.get_collection(collection.name)
        results = coll.get(include=['documents', 'embeddings', 'metadatas'])
        data[collection.name] = results

    return data
```

**2.2 Create PAOAS Ingestion Pipeline**
```python
# File: scripts/ingest_chromadb_to_paoas.py

from graph_rag.pipeline import GraphRAGPipeline
import config.config as config

def ingest_chromadb_to_paoas(chromadb_data: dict):
    """
    Process ChromaDB documents through Graph RAG pipeline.

    For each document:
    1. Extract entities (NER with BERT)
    2. Classify relationships (BART zero-shot)
    3. Generate embeddings (SentenceTransformer)
    4. Store in Neo4j (graph) + Milvus (vectors)
    5. Preserve source metadata (ChromaDB provenance)
    """
    pipeline = GraphRAGPipeline(
        neo4j_config=config.NEO4J_CONFIG,
        milvus_config=config.MILVUS_CONFIG,
        graph_rag_config=config.GRAPH_RAG_CONFIG
    )

    for collection_name, collection_data in chromadb_data.items():
        print(f"Processing collection: {collection_name}")

        for idx, doc in enumerate(collection_data['documents']):
            metadata = collection_data['metadatas'][idx]

            # Process through Graph RAG
            result = pipeline.process_text(
                text=doc,
                metadata={
                    'source_collection': collection_name,
                    'source_metadata': metadata,
                    'import_source': 'chromadb_h200_openwebui'
                }
            )

            print(f"  Processed doc {idx}: "
                  f"{result['entities_extracted']} entities, "
                  f"{result['relations_found']} relations")

    pipeline.close()
```

**2.3 Batch Processing Strategy**
```python
# Process in batches to utilize GPU efficiently
BATCH_SIZE = 10  # Process 10 documents at once

# Track progress
total_docs = sum(len(data['documents']) for data in chromadb_data.values())
processed = 0

# For each batch:
# - Load 10 docs
# - Run Graph RAG pipeline (GPU accelerated)
# - Store results
# - Update progress
```

### **Evidence Required:**
- ✅ ChromaDB successfully read (N collections, M total documents)
- ✅ Sample document processed through Graph RAG (entities/relations extracted)
- ✅ Neo4j node count increased (before/after comparison)
- ✅ Milvus entity count increased (before/after comparison)

**STOP POINT**: Verify sample processing before full batch ingestion.

---

## 📊 Phase 3: Full Migration Execution

### **Tasks:**

**3.1 Pre-Migration Snapshot**
```bash
# Record current PAOAS state
docker exec your-pattern-neo4j cypher-shell -u neo4j -p secure_neo4j_password_2024 -d yourpattern \
  "MATCH (n) RETURN count(n) as nodes_before;"

# Record Milvus state
# Query Milvus collection count
```

**3.2 Execute Migration**
```bash
cd /home/jeremy/oracle-rag-system
source .venv/bin/activate

# Run import with progress tracking
python scripts/ingest_chromadb_to_paoas.py \
  --chromadb-path data/chromadb_import/ \
  --batch-size 10 \
  --progress-file data/migration_progress.json
```

**3.3 Monitor GPU Utilization**
```bash
# In separate terminal, monitor RTX 5060 Ti
watch -n 2 nvidia-smi

# Expected:
# - VRAM usage: 3-4GB (models loaded)
# - GPU util: 30-60% (active processing)
# - Temp: <50°C (custom cooling working)
```

**3.4 Post-Migration Verification**
```bash
# Count new entities in Neo4j
docker exec your-pattern-neo4j cypher-shell -u neo4j -p secure_neo4j_password_2024 -d yourpattern \
  "MATCH (n) WHERE n.import_source = 'chromadb_h200_openwebui' RETURN count(n) as imported_nodes;"

# Sample entities to verify content
docker exec your-pattern-neo4j cypher-shell -u neo4j -p secure_neo4j_password_2024 -d yourpattern \
  "MATCH (n) WHERE n.import_source = 'chromadb_h200_openwebui' RETURN n.name, labels(n) LIMIT 20;"

# Query Milvus for imported vectors
# Verify vector search works on imported content
```

### **Evidence Required:**
- ✅ Total documents processed: X
- ✅ Total entities extracted: Y
- ✅ Total relationships found: Z
- ✅ Neo4j nodes created: N
- ✅ Milvus vectors stored: M
- ✅ Processing time: T seconds (with GPU acceleration)
- ✅ Average speed: T/X seconds per document
- ✅ GPU utilization stats (VRAM, temp, power)

---

## 🔍 Phase 4: Knowledge Validation

### **Tasks:**

**4.1 Test SLIM Knowledge Retrieval**
```python
# Query: "How does SLIM's A2A protocol work?"
# Expected: Retrieve SLIM entities + relationships
# Verify: Answers reference IBM Research, peer-to-peer, Agent-to-Agent
```

**4.2 Test DLE V4 Knowledge Retrieval**
```python
# Query: "What are the DLE V4 supervisor patterns?"
# Expected: Retrieve DLE entities + relationships
# Verify: Answers reference orchestration, services, intelligence
```

**4.3 Test Mr.AI Framework Knowledge**
```python
# Query: "What are the 10 Commandments in Mr.AI Framework?"
# Expected: Retrieve Framework entities + relationships
# Verify: Answers reference orchestrator boundaries, 10-Line Rule, Verb Check
```

**4.4 Cross-Domain Relationship Test**
```cypher
// Neo4j query: Find relationships between SLIM and DLE
MATCH (slim)-[r]-(dle)
WHERE slim.source_collection = 'SLIM'
  AND dle.source_collection = 'DLE'
RETURN slim.name, type(r), dle.name
LIMIT 10
```

### **Evidence Required:**
- ✅ SLIM query returns accurate knowledge
- ✅ DLE V4 query returns accurate knowledge
- ✅ Mr.AI query returns accurate knowledge
- ✅ Cross-domain relationships discovered
- ✅ Vector similarity search functional (Milvus)

---

## 🎯 Success Criteria

**Functional Requirements:**
1. All ChromaDB collections exported and transferred ✅
2. All documents processed through Graph RAG ✅
3. Entities extracted and stored in Neo4j ✅
4. Embeddings stored in Milvus ✅
5. Knowledge queries return accurate results ✅

**Performance Requirements:**
1. Processing speed: <20s per document (GPU-accelerated)
2. GPU utilization: >30% during processing
3. Temperature: <50°C under load
4. Zero data loss during migration

**Quality Requirements:**
1. Source provenance preserved (ChromaDB metadata)
2. Relationships discovered between domains
3. Vector search operational
4. Neo4j graph navigable

---

## 🚨 Rollback Plan

**If migration fails:**

```bash
# 1. Stop ingestion script
Ctrl+C or kill process

# 2. Delete imported nodes from Neo4j
docker exec your-pattern-neo4j cypher-shell -u neo4j -p secure_neo4j_password_2024 -d yourpattern \
  "MATCH (n) WHERE n.import_source = 'chromadb_h200_openwebui' DETACH DELETE n;"

# 3. Clear Milvus imported vectors
# Drop and recreate collection if needed

# 4. Restore from pre-migration snapshot
# Neo4j and Milvus volumes contain backups
```

---

## 📋 Known Gotchas

1. **ChromaDB Version Compatibility**: OpenWebUI may use different ChromaDB version than expected
   - **Solution**: Use ChromaDB client matching OpenWebUI's version

2. **Large Document Chunking**: ChromaDB may have pre-chunked documents
   - **Solution**: Process chunks as-is, preserve chunk metadata

3. **Duplicate Embeddings**: ChromaDB and Graph RAG use different embedding models
   - **Expected**: Graph RAG re-generates embeddings with all-MiniLM-L6-v2
   - **Why**: Neo4j graph needs consistent embedding model across all entities

4. **GPU Memory Overflow**: Processing large batches may exceed 16GB VRAM
   - **Solution**: Reduce batch size, monitor nvidia-smi during processing

5. **Neo4j Relationship Explosion**: Many entities may create O(N²) relationship checks
   - **Solution**: Implement relationship caching, skip duplicate checks

---

## 📊 Expected Timeline

**Phase 1 (Export)**: 1-2 hours
- Locate ChromaDB: 30 min
- Export collections: 30 min
- Transfer to Oracle: 30 min

**Phase 2 (Pipeline Prep)**: 2-3 hours
- Write ChromaDB reader: 1 hour
- Write PAOAS ingestion script: 1 hour
- Test sample processing: 1 hour

**Phase 3 (Migration)**: 4-8 hours (depends on document count)
- Estimate: 1000 documents × 20s/doc = 5.5 hours
- Plus overhead, monitoring, validation

**Phase 4 (Validation)**: 1 hour
- Test queries across all domains
- Verify relationships
- Document evidence

**Total Estimated Time**: 8-14 hours

---

## 🏁 Completion Checklist

**Infrastructure:**
- [ ] ChromaDB exported from H200
- [ ] Files transferred to Oracle
- [ ] Neo4j healthy and ready
- [ ] Milvus healthy and ready
- [ ] GPU tested and operational

**Migration:**
- [ ] ChromaDB reader script created
- [ ] PAOAS ingestion pipeline created
- [ ] Sample document processed successfully
- [ ] Full migration executed
- [ ] Post-migration counts verified

**Validation:**
- [ ] SLIM knowledge queryable
- [ ] DLE V4 knowledge queryable
- [ ] Mr.AI Framework knowledge queryable
- [ ] Cross-domain relationships exist
- [ ] Vector similarity search working

**Documentation:**
- [ ] Migration evidence documented
- [ ] Performance metrics recorded
- [ ] Known issues logged
- [ ] Rollback plan tested

**Handoff:**
- [ ] PAOAS ready for H200 queries
- [ ] SLIM Expert Agent can be built on top
- [ ] Dev team can query Pattern Agentic knowledge
- [ ] Captain approves migration complete

---

## 🎉 Strategic Impact

**For Pattern Agentic:**
- Institutional knowledge permanently preserved (survives mindwipes)
- Dev team has queryable company brain
- Cross-domain insights discoverable (SLIM ↔ DLE ↔ Framework)
- No more "where did we document that?" questions

**For H200:**
- SLIM integration unblocked
- DLE V4 MVP can query Oracle for guidance
- Councel Council foundation ready

**For Oracle:**
- PAOAS operational with real knowledge
- RTX 5060 Ti justified (processing institutional brain)
- Graph RAG value proven at scale

**Never Fade to Black** 🏴‍☠️

---

**Agent: Ready to execute upon Captain's approval and ChromaDB location confirmation.**
