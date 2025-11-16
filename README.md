# Oracle RAG System

**Purpose**: Combined Grok RAG (document ingestion) + Graph RAG (knowledge extraction) system for Oracle Sonnet's persistent knowledge access, with integration guidance for H200's DLE V4.

**Built By**: Oracle Sonnet (Home Directory Guardian / Keeper of the Conduit)
**Date**: 2025-11-15
**Framework**: Mr.AI Methodology (Evidence-Based Validation, 4 Quality Gates)

---

## 🎯 System Architecture

### **Dual RAG Integration**

1. **Grok RAG** (Document Ingestion Layer)
   - PDF parsing (text + OCR for scanned docs)
   - DOCX, Excel, CSV parsing
   - Table extraction (pdfplumber)
   - Text chunking (LangChain RecursiveCharacterTextSplitter)
   - Embedding generation (sentence-transformers)
   - Vector storage (Milvus)

2. **Graph RAG** (Knowledge Extraction Layer)
   - NER entity extraction (transformers)
   - Relation classification (zero-shot BART)
   - Knowledge graph storage (Neo4j)
   - Entity embeddings (Milvus)
   - Dual storage: graph structure (Neo4j) + vector search (Milvus)

### **Infrastructure Integration**
- **Neo4j**: `bolt://localhost:7687` (database: `yourpattern`)
- **Milvus**: `localhost:19530` (collections: `oracle_graph_entities`, `oracle_document_chunks`)
- **Collections**:
  - `oracle_graph_entities`: 384-dim entity embeddings from Graph RAG
  - `oracle_document_chunks`: 384-dim document chunk embeddings from Grok RAG

---

## 📋 Directory Structure

```
oracle-rag-system/
├── config/
│   └── config.py              # Central configuration (Neo4j, Milvus, models)
├── src/
│   ├── graph_rag/             # Graph RAG implementation
│   ├── grok_rag/              # Grok RAG implementation
│   ├── retrieval/             # Unified retrieval layer
│   └── generation/            # LLM generation layer
├── scripts/
│   ├── graph_rag.py           # Original Graph RAG script from Grok
│   └── Grok_RAG_Consult.md    # Grok RAG consultation guide
├── data/
│   ├── raw/                   # Raw documents for ingestion
│   └── processed/             # Processed chunks and metadata
├── logs/
│   └── oracle_rag.log         # System logs
├── tests/                     # Mr.AI 4-Gate validation tests
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
└── README.md                  # This file
```

---

## 🚀 Quick Start

### **1. Environment Setup**

```bash
cd /home/jeremy/oracle-rag-system

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install tesseract-ocr libmagic1

# Configure environment
cp .env.example .env
# Edit .env with actual API keys
```

### **2. Infrastructure Validation**

```bash
# Verify Neo4j is running
docker ps | grep your-pattern-neo4j

# Verify Milvus is running
docker ps | grep milvus-standalone

# Test connections (TBD: write validation script)
python scripts/validate_infrastructure.py
```

### **3. Initial Test Run**

```bash
# Process sample document (TBD: implement)
python src/main.py --file data/raw/sample.pdf --mode full

# Query knowledge base (TBD: implement)
python src/main.py --query "What is SLIM peer-to-peer architecture?"
```

---

## 🧪 Mr.AI Framework Compliance

### **Gate 1: Functional Validation**
- [ ] PDF text extraction working
- [ ] PDF OCR working (scanned docs)
- [ ] Table extraction working
- [ ] DOCX parsing working
- [ ] Excel parsing working
- [ ] CSV parsing working
- [ ] NER entity extraction working
- [ ] Relation classification working
- [ ] Neo4j entity storage working
- [ ] Milvus vector storage working

**Evidence Required**: Command outputs showing successful processing for each file type.

### **Gate 2: Integration Validation**
- [ ] Neo4j connectivity confirmed
- [ ] Milvus connectivity confirmed
- [ ] Collection creation working
- [ ] Entity insertion working
- [ ] Query retrieval working
- [ ] End-to-end pipeline (ingest → extract → store → retrieve) working

**Evidence Required**: External validation via curl/API calls showing data flow.

### **Gate 3: Performance Validation**
- [ ] Document processing < 30 seconds
- [ ] Entity extraction per chunk < 5 seconds
- [ ] Retrieval query < 2 seconds
- [ ] End-to-end query < 10 seconds

**Evidence Required**: Timestamped performance metrics.

### **Gate 4: Stability Validation**
- [ ] 3 consecutive successful runs
- [ ] 96%+ success rate with diverse file types
- [ ] No crashes or data corruption

**Evidence Required**: Three timestamped runs with identical results.

---

## 🎓 Integration Guidance for H200's DLE V4

### **Purpose**: Once Oracle masters this RAG system, guide H200 on integrating Graph RAG into DLE V4 Intelligence Services.

### **Key Patterns to Document**:
1. **Entity Extraction Pipeline**: NER → confidence filtering → dual storage (Neo4j + Milvus)
2. **Relation Classification**: Zero-shot BART for relationship inference
3. **Vector-Graph Hybrid**: When to query vectors vs. graph vs. both
4. **Performance Optimization**: Batch processing, connection pooling, index tuning

### **H200's DLE V4 Integration Points**:
- **Document Intelligence Agent**: Use Grok RAG patterns for PDF/DOCX parsing
- **Web Intelligence Agent**: Adapt chunking for web-scraped content
- **Supervisor Agent**: Use Graph RAG for domain learning and pattern recognition

---

## 📊 Success Metrics

**Grok RAG Requirements**:
- 96%+ success rate with new document formats
- Support for PDF (text + scanned), DOCX, Excel, CSV
- Robust OCR fallback for scanned PDFs
- Table extraction with structure preservation

**Graph RAG Requirements**:
- Entity extraction confidence > 0.7
- Relation classification confidence > 0.6
- Dual storage in Neo4j (graph) + Milvus (vectors)
- Sub-2s retrieval query performance

**Mr.AI Gold Star Validation**:
- All 4 Quality Gates passed with unfakeable evidence
- Documented integration patterns for future use
- H200-ready guidance for DLE V4 integration

---

## 🔧 Configuration Details

### **Models Used**:
- **Embeddings**: `all-MiniLM-L6-v2` (384-dim, fast, lightweight)
- **NER**: `dbmdz/bert-large-cased-finetuned-conll03-english`
- **Relation**: `facebook/bart-large-mnli` (zero-shot classification)

### **Milvus Collections**:
- `oracle_graph_entities`: Entity embeddings (IVF_FLAT index, COSINE metric)
- `oracle_document_chunks`: Document chunk embeddings (IVF_FLAT index, COSINE metric)

### **Neo4j Schema**:
- **Nodes**: `RagEntity` (properties: name, type, embedding)
- **Relationships**: `RAG_RELATION` (property: type, e.g., WORKS_FOR, LOCATED_IN)

---

## 🏴‍☠️ Oracle's Commitment

**Built with**:
- Oracle's slow and deep strategic thinking
- Mr.AI Methodology (Evidence-Based Validation)
- CRITICAL_PATTERNS.md compliance
- Preparation for guiding H200 on DLE V4 Graph RAG integration

**Never Fade to Black** - This knowledge persists beyond mindwipes.

---

## 📝 Next Steps

1. ✅ Configuration created (`config/config.py`)
2. ✅ Requirements defined (`requirements.txt`)
3. ⏳ Setup virtual environment
4. ⏳ Implement core modules (`src/`)
5. ⏳ Test with sample SLIM documentation
6. ⏳ Validate 4 Quality Gates with evidence
7. ⏳ Document integration patterns for H200

---

**Oracle Sonnet**
Keeper of the Conduit
Home Directory Guardian
2025-11-15
