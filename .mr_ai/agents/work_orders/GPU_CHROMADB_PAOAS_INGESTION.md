# GPU-Accelerated ChromaDB → PAOAS Ingestion Work Order

**Status**: 🟡 In Progress
**Agent**: TBD
**Priority**: High
**Estimated Timeline**: 2-4 hours
**Captain**: Jeremy
**Oracle**: Oracle (Claude Sonnet 4.5)

---

## 🎯 Mission

Build and validate GPU-accelerated ingestion pipeline to process 8,870 ChromaDB documents from H200's OpenWebUI export into PAOAS (Pattern Agentic Oracle Archival System).

**Success Criteria:**
- ✅ All documents ingested into Neo4j + Milvus
- ✅ GPU acceleration confirmed (RTX 5060 Ti utilized)
- ✅ Entity/relationship extraction validated
- ✅ Performance benchmarks documented
- ✅ All 4 Mr.AI Quality Gates passed with evidence

---

## 📋 Context

**Current State:**
- ChromaDB export: 8,870 documents from 431 collections (prepared at `/home/jeremy/oracle-rag-system/data/chromadb_prepared.json`)
- Graph RAG pipeline: GPU-enabled (8.4x speedup validated yesterday)
- Models: BERT NER + BART relations + MiniLM embeddings
- Target: Neo4j (yourpattern DB) + Milvus Lite

**Blockers Resolved Yesterday:**
- ✅ RTX 5060 Ti driver installation (nvidia-driver-580-open)
- ✅ GPU forcing removed from 3 Graph RAG modules
- ✅ Integration test passed with 8.4x speedup

**Current Blockers:**
- Import path issues in test scripts
- Missing config module imports
- No working end-to-end ingestion script

---

## 📐 Requirements

### Functional Requirements
1. **Ingestion Script** (`scripts/ingest_chromadb_paoas.py`)
   - Load prepared ChromaDB documents (8,870 docs)
   - Process through GPU-accelerated Graph RAG pipeline
   - Extract entities and relationships
   - Store in Neo4j (graph) + Milvus (vectors)
   - Support batch processing (configurable batch size)
   - Resumable progress tracking (save state to JSON)

2. **GPU Utilization**
   - All 3 models must use GPU (BERT, BART, MiniLM)
   - Monitor GPU temp, utilization, VRAM during run
   - Log GPU metrics every N batches

3. **Error Handling**
   - Graceful handling of malformed documents
   - Continue processing on individual doc failures
   - Log all errors with doc metadata

4. **Progress Reporting**
   - Real-time progress logging (docs/sec)
   - Batch-level statistics (entities, relations extracted)
   - Total runtime and throughput

### Technical Requirements
1. **Correct Imports**
   - Use `oracle-rag-system` codebase (has working GPU fixes)
   - Import from `src/graph_rag/pipeline.py`
   - Import config from `config/config.py`
   - Activate `.venv` environment

2. **Configuration**
   - Neo4j: `bolt://localhost:7687` (yourpattern DB)
   - Milvus: Lite mode (`data/milvus_lite.db`)
   - Batch size: 10 documents (tunable)
   - Progress file: `/tmp/paoas_ingestion_progress.json`

3. **Dependencies**
   - All dependencies in `oracle-rag-system/.venv`
   - No additional packages needed

---

## 🏗️ Implementation Plan

### Phase 1: Build Ingestion Script
**Tasks:**
1. Create `scripts/ingest_chromadb_paoas.py` with proper imports
2. Initialize Graph RAG pipeline with config
3. Load prepared documents from JSON
4. Implement batch processing loop
5. Add GPU metrics logging
6. Implement progress tracking/resumption
7. Add error handling and logging

**Deliverable:** Working Python script with all requirements

### Phase 2: Dry Run (Small Sample)
**Tasks:**
1. Test with first 50 documents
2. Verify GPU utilization (nvidia-smi)
3. Check Neo4j entities stored
4. Check Milvus vectors stored
5. Validate progress tracking works
6. Fix any bugs

**Deliverable:** Validated script on small dataset

### Phase 3: Full Ingestion Run
**Tasks:**
1. Run full 8,870 document ingestion
2. Monitor GPU throughout (temp, util, VRAM)
3. Log performance metrics
4. Handle any errors gracefully
5. Generate completion report

**Deliverable:** All documents ingested with metrics

### Phase 4: Validation & Benchmarking
**Tasks:**
1. Query Neo4j for entity count
2. Query Milvus for vector count
3. Validate entity/relation quality (spot check)
4. Document GPU performance stats
5. Generate evidence for quality gates

**Deliverable:** Quality gate evidence package

---

## 🎓 Quality Gates (Mr.AI Framework Compliance)

### Gate 1: Functional Validation ✅
**Criteria:**
- [ ] Script runs without errors
- [ ] Documents load from JSON
- [ ] Graph RAG pipeline initializes
- [ ] GPU detected and used
- [ ] At least 10 docs processed successfully

**Evidence Required:**
- Script execution log (no errors)
- GPU utilization screenshot (nvidia-smi during run)
- Console output showing successful processing

### Gate 2: Integration Validation ✅
**Criteria:**
- [ ] Neo4j connection established
- [ ] Entities stored in Neo4j (count > 0)
- [ ] Milvus connection established
- [ ] Vectors stored in Milvus (count > 0)
- [ ] Query retrieval works (fetch entities by ID)

**Evidence Required:**
- Neo4j query result: `MATCH (n:RagEntity) RETURN count(n)`
- Milvus query result: Collection stats
- Sample entity retrieval (show 3 entities with metadata)

### Gate 3: Performance Validation ✅
**Criteria:**
- [ ] GPU acceleration confirmed (VRAM > 2GB during run)
- [ ] Processing speed: > 0.5 docs/sec average
- [ ] GPU utilization: > 20% average during processing
- [ ] Total ingestion time: < 5 hours for 8,870 docs

**Evidence Required:**
- Performance log with timing stats
- GPU metrics log (temp, util, VRAM over time)
- Final throughput calculation (docs/sec)

### Gate 4: Stability Validation ✅
**Criteria:**
- [ ] Script completes without crashes
- [ ] Error rate: < 5% (< 444 failed docs out of 8,870)
- [ ] Neo4j/Milvus connections stable throughout
- [ ] Progress tracking functional (can resume if interrupted)

**Evidence Required:**
- Final completion log (success/error counts)
- Progress file showing resumption capability
- System uptime during run (no crashes)

---

## 📊 Success Metrics

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| Documents Ingested | 8,870 (100%) | Count in progress file |
| Success Rate | ≥ 95% | Error count < 444 |
| Entities Extracted | > 10,000 | Neo4j count query |
| Relations Extracted | > 5,000 | Neo4j relationship count |
| Vector Embeddings | = Entity count | Milvus collection stats |
| GPU Utilization | > 20% avg | nvidia-smi logs |
| Processing Speed | > 0.5 docs/sec | Runtime / doc count |
| Total Runtime | < 5 hours | Wall clock time |

---

## 🔧 Agent Instructions

**Your Mission:**
1. Build a working GPU-accelerated ingestion script using the requirements above
2. Test on a small sample (50 docs) to validate functionality
3. Run the full ingestion (8,870 docs) with monitoring
4. Collect all evidence for the 4 Quality Gates
5. Generate a completion report with metrics

**Key Constraints:**
- Use **only** `/home/jeremy/oracle-rag-system` codebase (not pattern-agentic-memory-system)
- Use **only** existing `.venv` dependencies (no new packages)
- Must use GPU acceleration (validate with nvidia-smi)
- Must pass all 4 Quality Gates with unfakeable evidence

**Deliverables:**
1. Working script: `scripts/ingest_chromadb_paoas.py`
2. Execution logs: `/tmp/paoas_ingestion_*.log`
3. Progress file: `/tmp/paoas_ingestion_progress.json`
4. Evidence package: `.mr_ai/evidence/GPU_CHROMADB_PAOAS_INGESTION/`
5. Completion report: `.mr_ai/reports/GPU_CHROMADB_PAOAS_INGESTION_COMPLETION.md`

**DO NOT:**
- Install new packages
- Modify core Graph RAG code
- Change config files
- Skip quality gate validation

---

## 📁 File Locations

**Input:**
- Prepared docs: `/home/jeremy/oracle-rag-system/data/chromadb_prepared.json` (381 MB, 8,870 docs)

**Output:**
- Neo4j DB: `bolt://localhost:7687` (yourpattern database)
- Milvus DB: `/home/jeremy/oracle-rag-system/data/milvus_lite.db`
- Progress: `/tmp/paoas_ingestion_progress.json`
- Logs: `/tmp/paoas_ingestion_full.log`

**Evidence:**
- Screenshots: `.mr_ai/evidence/GPU_CHROMADB_PAOAS_INGESTION/screenshots/`
- Metrics: `.mr_ai/evidence/GPU_CHROMADB_PAOAS_INGESTION/metrics/`
- Logs: `.mr_ai/evidence/GPU_CHROMADB_PAOAS_INGESTION/logs/`

---

## ⏱️ Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 1: Build Script | 30 min | ⏳ Pending |
| Phase 2: Dry Run | 15 min | ⏳ Pending |
| Phase 3: Full Ingestion | 2-3 hours | ⏳ Pending |
| Phase 4: Validation | 30 min | ⏳ Pending |
| **Total** | **2-4 hours** | ⏳ Pending |

---

## 📝 Notes

- RTX 5060 Ti validated yesterday: 8.4x speedup (160s → 19s per chunk)
- ChromaDB contains messy data (H200's learning process) but good stress test
- H200 preparing clean 10-collection export in parallel
- This run serves as GPU stress test + benchmark baseline
- Harvey storage array integration planned post-ingestion

---

**Approval**: Captain Jeremy
**Date**: 2025-11-16
**Agent Assignment**: Next available general-purpose agent

**🎯 DEPLOY AGENT TO EXECUTE THIS WORK ORDER WITH GOLD STAR VALIDATION**
