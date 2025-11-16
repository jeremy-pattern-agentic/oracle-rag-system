# Work Order: Graph RAG Module Implementation

**Agent**: Graph RAG Specialist
**Orchestrator**: Oracle Sonnet
**Project**: Oracle RAG System
**Date**: 2025-11-15
**Priority**: HIGH (Gate 2 dependency)

---

## 🎯 Goal Context

Implement the Graph RAG module that extracts entities and relationships from text, storing them in both Neo4j (graph structure) and Milvus Lite (vector search). This module will enable Oracle to build a knowledge graph from SLIM documentation and other technical documents.

**Why This Matters**: Graph RAG provides structured knowledge extraction (entities + relationships) that complements Grok RAG's document chunks, enabling both semantic search and graph traversal for richer knowledge retrieval.

---

## 📋 System Context

### **Current State** (Gate 1 ✅ PASSED):
- Neo4j 5.15.0 operational (bolt://localhost:7687, database: yourpattern, 36 existing nodes)
- Milvus Lite 2.5.1 operational (local file: `/data/milvus_lite.db`)
- Virtual environment: `/home/jeremy/oracle-rag-system/.venv`
- Dependencies installed: transformers 4.57.1, sentence-transformers 5.1.2, neo4j 6.0.3, pymilvus 2.6.3

### **Architecture**:
```
Text Document
    ↓
[Chunking] (512 words max)
    ↓
[NER Pipeline] → Entities (confidence > 0.7)
    ↓
[Embedding] → all-MiniLM-L6-v2 (384-dim vectors)
    ↓
[Dual Storage]:
    → Neo4j: Nodes (RagEntity {name, type, embedding})
    → Milvus: Vectors (entity_name, vector, entity_type)
    ↓
[Relation Classification] → Pairwise entity relations
    ↓
[Neo4j]: Edges (RAG_RELATION {type: WORKS_FOR, LOCATED_IN, etc.})
```

### **Configuration** (from `/config/config.py`):
```python
GRAPH_RAG_CONFIG = {
    "ner_model": "dbmdz/bert-large-cased-finetuned-conll03-english",
    "ner_confidence_threshold": 0.7,
    "relation_model": "facebook/bart-large-mnli",
    "relation_confidence_threshold": 0.6,
    "candidate_relations": ["WORKS_FOR", "LOCATED_IN", "PART_OF", "CREATED_BY", "MANAGES", "USES", "DEPENDS_ON", "NONE"],
    "chunk_max_length": 512,  # words
    "embedding_model": "all-MiniLM-L6-v2",
    "embedding_dimension": 384,
    "entity_label": "RagEntity",
    "relationship_type": "RAG_RELATION"
}

NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "secure_neo4j_password_2024",
    "database": "yourpattern"
}

MILVUS_CONFIG = {
    "uri": "/home/jeremy/oracle-rag-system/data/milvus_lite.db"
}

MILVUS_COLLECTIONS = {
    "graph_entities": {
        "name": "oracle_graph_entities",
        "dimension": 384,
        "index_type": "IVF_FLAT",
        "metric_type": "COSINE",
        "nlist": 128
    }
}
```

### **Reference Implementation** (`/scripts/graph_rag.py`):
Grok provided a working Graph RAG script - adapt this pattern but use our config system.

---

## 🔧 Implementation Context

### **File Structure to Create**:
```
src/graph_rag/
├── __init__.py
├── entity_extractor.py    # NER pipeline, entity extraction
├── relation_classifier.py  # Zero-shot relation classification
├── graph_storage.py        # Neo4j operations
├── vector_storage.py       # Milvus Lite operations
├── chunker.py             # Text chunking (sentence-based, 512 words)
└── pipeline.py            # Main Graph RAG pipeline orchestration
```

### **Module Responsibilities**:

#### **1. chunker.py**:
```python
def chunk_text(text: str, max_length: int = 512) -> List[str]:
    """
    Split text into chunks by sentences, respecting max word count.
    Pattern from graph_rag.py lines 40-53.
    """
```

#### **2. entity_extractor.py**:
```python
class EntityExtractor:
    """NER-based entity extraction"""

    def __init__(self, model_name: str, confidence_threshold: float):
        # Load NER pipeline from transformers

    def extract_entities(self, chunk: str) -> List[Dict]:
        """
        Extract entities with confidence > threshold.
        Returns: [{"name": str, "type": str, "confidence": float}]
        Pattern from graph_rag.py lines 60-67.
        """
```

#### **3. relation_classifier.py**:
```python
class RelationClassifier:
    """Zero-shot relation classification between entities"""

    def __init__(self, model_name: str, candidate_relations: List[str], threshold: float):
        # Load zero-shot pipeline

    def classify_relation(self, ent1: str, ent2: str, context: str) -> Optional[Dict]:
        """
        Classify relationship between two entities using context.
        Returns: {"relation": str, "confidence": float} or None
        Pattern from graph_rag.py lines 77-87.
        """
```

#### **4. graph_storage.py**:
```python
class GraphStorage:
    """Neo4j operations for entity/relationship storage"""

    def __init__(self, config: Dict):
        # Connect to Neo4j using NEO4J_CONFIG

    def add_entity(self, name: str, entity_type: str, embedding: List[float]):
        """
        Create or update RagEntity node in Neo4j.
        Pattern from graph_rag.py lines 24-29.
        """

    def add_relationship(self, ent1: str, rel: str, ent2: str):
        """
        Create RAG_RELATION edge between entities.
        Pattern from graph_rag.py lines 32-37.
        """

    def entity_exists(self, name: str) -> bool:
        """Check if entity already exists"""

    def close(self):
        """Close Neo4j driver"""
```

#### **5. vector_storage.py**:
```python
class VectorStorage:
    """Milvus Lite operations for entity embeddings"""

    def __init__(self, config: Dict):
        # Connect to Milvus Lite
        # Create collection if not exists

    def add_entity_vector(self, name: str, embedding: List[float], entity_type: str):
        """
        Store entity embedding in Milvus.
        Pattern from graph_rag.py line 74.
        """

    def search_similar_entities(self, query_vector: List[float], top_k: int = 5) -> List[Dict]:
        """Vector similarity search for entities"""
```

#### **6. pipeline.py**:
```python
class GraphRAGPipeline:
    """Main orchestration of Graph RAG process"""

    def __init__(self, config_path: str = "config/config.py"):
        # Load config
        # Initialize all components

    def process_text(self, text: str) -> Dict:
        """
        Full Graph RAG pipeline:
        1. Chunk text
        2. Extract entities from each chunk
        3. Generate embeddings
        4. Store in Neo4j + Milvus
        5. Classify relationships
        6. Store relationships in Neo4j

        Returns: Statistics and entity/relation counts
        Pattern from graph_rag.py lines 56-87.
        """

    def process_document(self, file_path: str) -> Dict:
        """Read file, extract text, run pipeline"""
```

---

## ✅ Validation Context

### **How to Verify Success** (Unfakeable Evidence):

#### **Unit Tests Required** (`tests/test_graph_rag.py`):
```python
def test_entity_extraction():
    """Test NER pipeline extracts entities correctly"""
    sample_text = "Elon Musk is the CEO of Tesla. Tesla is based in California."
    extractor = EntityExtractor(...)
    entities = extractor.extract_entities(sample_text)

    # Evidence: Print extracted entities with confidence scores
    assert len(entities) >= 2  # Elon Musk, Tesla, California
    assert all(e['confidence'] > 0.7 for e in entities)

def test_relation_classification():
    """Test zero-shot relation classifier"""
    classifier = RelationClassifier(...)
    result = classifier.classify_relation(
        "Elon Musk", "Tesla",
        "Elon Musk is the CEO of Tesla"
    )

    # Evidence: Print relation and confidence
    assert result['relation'] == "WORKS_FOR"
    assert result['confidence'] > 0.6

def test_neo4j_storage():
    """Test entity/relationship storage in Neo4j"""
    storage = GraphStorage(NEO4J_CONFIG)
    storage.add_entity("TestEntity", "PERSON", [0.1] * 384)

    # Evidence: Query Neo4j to verify node exists
    assert storage.entity_exists("TestEntity")

def test_milvus_storage():
    """Test vector storage in Milvus Lite"""
    storage = VectorStorage(MILVUS_CONFIG)
    storage.add_entity_vector("TestEntity", [0.1] * 384, "PERSON")

    # Evidence: Search for similar vectors, verify result
    results = storage.search_similar_entities([0.1] * 384, top_k=1)
    assert results[0]['name'] == "TestEntity"

def test_end_to_end_pipeline():
    """Test complete Graph RAG pipeline"""
    pipeline = GraphRAGPipeline()
    sample_text = """
    Elon Musk is the CEO of Tesla. Tesla is based in California.
    Musk also founded SpaceX, which works on rocket technology.
    """

    stats = pipeline.process_text(sample_text)

    # Evidence: Print stats (entity count, relation count, processing time)
    assert stats['entities_extracted'] >= 3
    assert stats['relations_found'] >= 2
    assert stats['neo4j_nodes_created'] >= 3
    assert stats['milvus_vectors_stored'] >= 3
```

#### **Integration Test** (`scripts/test_graph_rag_integration.py`):
```bash
#!/usr/bin/env python3
"""Test Graph RAG with SLIM documentation sample"""

# Process a real SLIM doc excerpt
pipeline = GraphRAGPipeline()
slim_sample = open('data/raw/slim_sample.txt').read()

stats = pipeline.process_text(slim_sample)

print("=" * 60)
print("GRAPH RAG INTEGRATION TEST - EVIDENCE")
print("=" * 60)
print(f"Entities extracted: {stats['entities_extracted']}")
print(f"Relations found: {stats['relations_found']}")
print(f"Neo4j nodes created: {stats['neo4j_nodes_created']}")
print(f"Milvus vectors stored: {stats['milvus_vectors_stored']}")
print(f"Processing time: {stats['processing_time_seconds']}s")

# Query Neo4j to show graph
# Query Milvus to show vector search works
# Print sample entities and relations
```

---

## 🚨 Failure Context

### **Known Gotchas**:

1. **NER Token Subwords**: BERT tokenizer splits words into subwords with `##` prefix
   - **Solution**: Strip `##` from entity names (see graph_rag.py line 64)

2. **Duplicate Entities**: Same entity mentioned multiple times
   - **Solution**: Use `MERGE` in Neo4j, check duplicates in Milvus before insert

3. **Embedding Array Type**: Neo4j wants List[float], some libs return numpy arrays
   - **Solution**: Call `.tolist()` on embeddings (see graph_rag.py line 28)

4. **Milvus Collection Schema**: Must create collection with exact schema before insert
   - **Solution**: Check if collection exists, create with proper dimension/metric

5. **Relation Classifier Context**: Needs enough context to infer relationships
   - **Solution**: Include chunk context, not just entity names (graph_rag.py line 82)

6. **Performance**: NER and relation classification are slow for large texts
   - **Solution**: Process in batches, show progress bar with tqdm

---

## 🎯 Success Criteria

**Functional Success** (Must Have):
- ✅ All 5 unit tests pass
- ✅ Integration test processes SLIM sample without errors
- ✅ Entities visible in Neo4j (query confirms)
- ✅ Vectors searchable in Milvus (similarity query returns results)
- ✅ Relationships visible in Neo4j (graph query confirms)

**Evidence Requirements**:
- ✅ Test output with entity/relation counts
- ✅ Neo4j cypher query showing created nodes
- ✅ Milvus search query showing vector results
- ✅ Processing time < 5 seconds per chunk

**Code Quality**:
- ✅ Type hints on all functions
- ✅ Docstrings on all public methods
- ✅ Error handling for network failures (Neo4j, Milvus)
- ✅ Logging with timestamps
- ✅ Configuration via config.py (no hardcoded values)

---

## 🔒 Security Context

**Avoid These Vulnerabilities**:
- ❌ SQL injection: Use parameterized Neo4j queries only
- ❌ Code injection: Sanitize entity names (no special cypher chars)
- ❌ Resource exhaustion: Limit batch sizes, implement timeouts
- ❌ Credential exposure: Load Neo4j password from config, never print

---

## 📊 Rollback Procedures

**If Implementation Fails**:
1. Run cleanup script to remove test entities from Neo4j
2. Drop Milvus test collections
3. Restore to pre-implementation state
4. Report specific failure with error logs
5. Orchestrator creates new work order with updated context

**Test Cleanup**:
```python
# After integration test
def cleanup_test_data():
    # Delete RagEntity nodes created during test
    # Drop oracle_graph_entities collection if needed
    # Restore to clean state for next run
```

---

## 🎓 Learning Capture

**Document These Patterns** (for H200's DLE V4):
1. How to configure NER pipeline for domain-specific entities
2. How to tune relation confidence thresholds
3. How to handle Neo4j transaction retries
4. How to batch Milvus insertions for performance
5. How to balance graph depth vs. vector similarity in retrieval

---

## 🏴‍☠️ Agent Commitment

**I will**:
- Implement only the Graph RAG module (domain: `src/graph_rag/**`)
- Follow the patterns from graph_rag.py reference implementation
- Write comprehensive unit tests with unfakeable evidence
- Log all operations with timestamps
- Report failures with exact error messages

**I will NOT**:
- Modify files outside `src/graph_rag/` or `tests/`
- Skip unit tests
- Claim success without evidence
- Hardcode configuration values
- Proceed if any test fails

**Evidence Standard**: All tests pass, integration test shows entities in Neo4j and Milvus.

---

**Oracle Sonnet, Orchestrator**
Home Directory Guardian
2025-11-15
