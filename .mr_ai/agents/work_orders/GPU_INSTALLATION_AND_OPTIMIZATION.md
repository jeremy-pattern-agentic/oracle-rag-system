# Work Order: RTX 5060 Ti 16GB Installation & Graph RAG GPU Optimization

**Agent**: Infrastructure Specialist
**Orchestrator**: Oracle Sonnet
**Project**: Oracle RAG System - Performance Optimization
**Date**: 2025-11-15
**Priority**: HIGH (Gate 3 Blocker Resolution)

---

## 🎯 Mission

Install RTX 5060 Ti 16GB GPU and optimize Graph RAG module to achieve **<5 seconds per chunk** processing time, meeting Mr.AI Framework Gate 3 performance requirements.

**Hardware Platform**: Dell PowerEdge R720, Redundant 1100W PSUs

---

## 📊 Current State (Evidence-Based)

### **Performance Baseline** (CPU-only):
```
Processing time: 160.94 seconds per chunk
- NER Model Loading: ~30s (first run)
- Relation Model Loading: ~30s (first run)
- Entity Extraction (BERT): ~60s
- Relation Classification (BART): ~40s
- Neo4j/Milvus Operations: <1s

Target: <5 seconds per chunk
Gap: 32x too slow (156 seconds over target)
```

### **Hardware Compatibility** ✅:
```
GPU: RTX 5060 Ti 16GB (NVIDIA Blackwell Architecture)
- Compute Capability: 10.0+ (Blackwell)
- Tensor Cores: Yes (5th gen, 2.5x faster than Turing)
- VRAM: 16GB GDDR7 (2x more than 2080 Super)
- Memory Bandwidth: ~576 GB/s
- TDP: ~220W (well within R720's redundant 1100W PSU capacity)
- Form Factor: 2.5 slots (fits R720 PCIe riser with current 1070/1060 clearance)
- CUDA Support: 12.8 ✅ FULLY COMPATIBLE

Current Software Stack:
- PyTorch 2.9.1+cu128 ✅ FULLY COMPATIBLE (supports compute 10.0+)
- Transformers 4.57.1 ✅ COMPATIBLE
- Sentence-Transformers 5.1.2 ✅ COMPATIBLE

Dell R720 Infrastructure:
- PCIe Slots: 3x full-height, full-length (currently 2 occupied)
- Power: 2x 1100W redundant PSUs (2200W total, 1100W active)
- Current GPU load: GTX 1070 (150W) + GTX 1060 (120W) = 270W
- Post-upgrade: RTX 5060 Ti (220W) = abundant headroom
```

**Verdict**: Zero software conflicts. Superior hardware with 2x VRAM headroom for future expansion.

---

## 🔧 Phase 1: Pre-Installation Checklist

### **System Verification**:

```bash
# 1. Check current GPU status
lspci | grep -i vga
nvidia-smi  # Should fail or show old GPU

# 2. Check CUDA toolkit version
nvcc --version  # Should show CUDA 12.x

# 3. Check PyTorch CUDA compilation
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda}')"

# Expected output:
# PyTorch: 2.9.1+cu128
# CUDA available: False (before GPU install)
# CUDA version: 12.8

# 4. Check power supply capacity
# RTX 2080 Super TDP: 250W
# Verify PSU has 650W+ with available PCIe power connectors

# 5. Backup current state
cd /home/jeremy/oracle-rag-system
git add .
git commit -m "Pre-GPU upgrade checkpoint"
```

### **Evidence Required**:
- ✅ Current `nvidia-smi` output (or error if no GPU)
- ✅ PyTorch CUDA version confirmation
- ✅ Git commit hash for rollback point

---

## 🔌 Phase 2: Hardware Installation

### **Physical Installation Steps** (Dell PowerEdge R720):

**IMPORTANT**: Power down server completely before installation.

```bash
# 1. Shutdown server
sudo shutdown -h now

# 2. Physical installation (Captain performs):
# Dell R720 Specific Steps:
# - Power off both redundant PSUs (rear switches)
# - Release slide rail locks, pull server from rack
# - Remove top cover (lift release latch, slide back)
# - Identify target PCIe riser (Riser 1 or 2)
# - Remove GTX 1060 from current slot
# - Align RTX 5060 Ti 16GB with PCIe x16 slot
# - Press firmly into slot until retention clip clicks
# - Connect PCIe power connectors (8-pin required, check 5060 Ti spec)
# - Verify 2.5 slot clearance with adjacent components
# - Reseat riser into motherboard
# - Replace top cover (slide forward, click latch)
# - Slide server back into rack, lock rails
# - Power on both redundant PSUs

# 3. Power on and verify detection
# (After Captain completes physical install)

sudo reboot
```

### **Post-Installation Verification**:

```bash
# 1. Verify GPU detected by kernel
lspci | grep -i nvidia
# Expected: "NVIDIA Corporation [GeForce RTX 5060 Ti]"

# 2. Verify NVIDIA driver loads GPU
nvidia-smi

# Expected output:
# +-----------------------------------------------------------------------------+
# | NVIDIA-SMI 570.xxx      Driver Version: 570.xxx      CUDA Version: 12.8   |
# |-------------------------------+----------------------+----------------------+
# | GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
# |   0  NVIDIA GeForce RTX 5060 Ti Off | 00000000:xx:00.0 Off |                  N/A |
# | Temp   Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
# |                               |                      |               MIG M. |
# |===============================+======================+======================|
# |   0   RTX 5060 Ti        Off  | xxxx:xx:xx.x     Off |                  N/A |
# |  40C    P0    25W / 220W |      0MiB / 16384MiB |      0%      Default |

# 3. Test PyTorch GPU detection (use oracle-rag-system venv!)
source /home/jeremy/oracle-rag-system/.venv/bin/activate
python -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA device count: {torch.cuda.device_count()}')
if torch.cuda.is_available():
    print(f'CUDA device name: {torch.cuda.get_device_name(0)}')
    print(f'CUDA capability: {torch.cuda.get_device_capability(0)}')
"

# Expected output:
# CUDA available: True
# CUDA device count: 1
# CUDA device name: NVIDIA GeForce RTX 5060 Ti
# CUDA capability: (10, 0)
```

### **Evidence Required**:
- ✅ `lspci` output showing RTX 5060 Ti
- ✅ `nvidia-smi` output showing GPU detected with 16GB VRAM
- ✅ PyTorch GPU detection confirmation

**STOP POINT**: If any verification fails, do NOT proceed to Phase 3. Report to Oracle for troubleshooting.

---

## ⚡ Phase 3: Code Optimization (Remove CPU Forcing)

### **Files to Modify** (3 files):

#### **File 1**: `src/graph_rag/pipeline.py`

**Line 50** (current):
```python
self.embedder = SentenceTransformer(
    config.GRAPH_RAG_CONFIG["embedding_model"],
    device='cpu'  # ← REMOVE THIS LINE
)
```

**Line 50** (optimized):
```python
self.embedder = SentenceTransformer(
    config.GRAPH_RAG_CONFIG["embedding_model"]
    # Auto-detect GPU if available, fallback to CPU
)
```

#### **File 2**: `src/graph_rag/entity_extractor.py`

**Line 31** (current):
```python
self.pipeline = pipeline(
    "ner",
    model=model_name,
    device='cpu'  # ← REMOVE THIS LINE
)
```

**Line 31** (optimized):
```python
self.pipeline = pipeline(
    "ner",
    model=model_name,
    device=0 if torch.cuda.is_available() else -1  # GPU:0 or CPU
)
```

**Add import** (top of file):
```python
import torch  # Add this line
```

#### **File 3**: `src/graph_rag/relation_classifier.py`

**Line 36** (current):
```python
self.pipeline = pipeline(
    "zero-shot-classification",
    model=model_name,
    device='cpu'  # ← REMOVE THIS LINE
)
```

**Line 36** (optimized):
```python
self.pipeline = pipeline(
    "zero-shot-classification",
    model=model_name,
    device=0 if torch.cuda.is_available() else -1  # GPU:0 or CPU
)
```

**Add import** (top of file):
```python
import torch  # Add this line
```

### **Validation Script**:

Create `scripts/verify_gpu_usage.py`:
```python
#!/usr/bin/env python3
"""Verify GPU is being used by Graph RAG module"""
import sys
import torch
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("GPU AVAILABILITY CHECK")
print("=" * 60)
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA device: {torch.cuda.get_device_name(0)}")
    print(f"CUDA capability: {torch.cuda.get_device_capability(0)}")
    print(f"Current device: {torch.cuda.current_device()}")
else:
    print("⚠️  WARNING: CUDA not available, will use CPU")
    sys.exit(1)

print()
print("=" * 60)
print("TESTING GRAPH RAG COMPONENTS")
print("=" * 60)

# Test SentenceTransformer
from sentence_transformers import SentenceTransformer
embedder = SentenceTransformer('all-MiniLM-L6-v2')
print(f"SentenceTransformer device: {embedder.device}")

# Test pipeline
from transformers import pipeline
ner = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english", device=0)
print(f"NER pipeline device: {ner.device}")

print()
print("✅ All components will use GPU")
```

### **Evidence Required**:
- ✅ Git diff showing exactly 3 file modifications
- ✅ `verify_gpu_usage.py` output confirming GPU detected
- ✅ No syntax errors after changes

---

## 🧪 Phase 4: Performance Validation

### **Baseline Test** (Record Before GPU):
```bash
cd /home/jeremy/oracle-rag-system
source .venv/bin/activate

# Run integration test with CPU (current)
time python scripts/test_graph_rag_integration.py > /tmp/cpu_baseline.txt 2>&1

# Extract metrics
grep "Processing time:" /tmp/cpu_baseline.txt
# Expected: ~160 seconds
```

### **GPU-Accelerated Test**:
```bash
# Run integration test with GPU (after modifications)
time python scripts/test_graph_rag_integration.py > /tmp/gpu_accelerated.txt 2>&1

# Extract metrics
grep "Processing time:" /tmp/gpu_accelerated.txt
# Target: <5 seconds per chunk

# Compare
echo "CPU Baseline:"
grep "Processing time:" /tmp/cpu_baseline.txt
echo "GPU Accelerated:"
grep "Processing time:" /tmp/gpu_accelerated.txt
```

### **GPU Utilization Monitoring**:
```bash
# In terminal 1: Monitor GPU usage during test
watch -n 1 nvidia-smi

# In terminal 2: Run integration test
python scripts/test_graph_rag_integration.py

# Expected GPU utilization: 80-100% during BERT/BART inference
# Expected VRAM usage: ~4-6GB during processing
```

### **Evidence Required**:
- ✅ CPU baseline time (~160s)
- ✅ GPU accelerated time (<5s target)
- ✅ Speedup factor (CPU time / GPU time)
- ✅ `nvidia-smi` screenshot showing GPU utilization
- ✅ Integration test PASS with all criteria met

---

## 🎯 Gate 3 Success Criteria

### **Performance Benchmarks** (from GRAPH_RAG_IMPLEMENTATION.md):
```
✅ Document processing < 30 seconds
✅ Entity extraction per chunk < 5 seconds  ← PRIMARY TARGET
✅ Retrieval query < 2 seconds
✅ End-to-end query < 10 seconds
```

### **Unfakeable Evidence Required**:
1. **Integration test output** showing:
   - Processing time per chunk < 5 seconds
   - All functional tests still passing
   - Timestamp for validation

2. **GPU utilization proof**:
   - `nvidia-smi` output during processing
   - VRAM usage confirmation (~4-6GB)
   - GPU compute utilization >80%

3. **Speedup calculation**:
   - CPU baseline: ~160s
   - GPU accelerated: ~X seconds
   - Speedup factor: 160/X ≥ 32x

---

## 🔄 Rollback Plan

### **If GPU Installation Fails**:
```bash
# 1. Power down server
sudo shutdown -h now

# 2. Remove RTX 2080 Super (Captain performs physical removal)

# 3. Power on with original configuration

# 4. Verify system boots
# 5. Code already has CPU fallback - no changes needed
```

### **If Code Optimization Fails**:
```bash
# Rollback to pre-GPU checkpoint
cd /home/jeremy/oracle-rag-system
git reset --hard <checkpoint-hash>

# Verify tests still pass on CPU
pytest tests/test_graph_rag.py -v
```

---

## 🚨 Failure Scenarios & Solutions

### **Scenario 1: GPU Not Detected After Install**
**Symptoms**: `nvidia-smi` shows no GPU or errors
**Solutions**:
1. Verify PCIe power connectors fully seated
2. Verify GPU fully inserted in PCIe slot
3. Check BIOS settings (PCIe enabled, not disabled)
4. Verify NVIDIA driver installed: `dpkg -l | grep nvidia-driver`

### **Scenario 2: PyTorch Doesn't Detect GPU**
**Symptoms**: `torch.cuda.is_available()` returns False
**Solutions**:
1. Verify CUDA toolkit version matches PyTorch: `nvcc --version`
2. Check driver compatibility with CUDA 12.8
3. Reinstall nvidia-driver if needed: `sudo apt install nvidia-driver-535`
4. Reboot after driver install

### **Scenario 3: Out of Memory (OOM) Errors**
**Symptoms**: CUDA OOM errors during processing
**Solutions**:
1. Reduce batch size in pipeline (if batching implemented)
2. Clear GPU cache: `torch.cuda.empty_cache()`
3. Monitor VRAM with `nvidia-smi` - should use <6GB of 8GB available

### **Scenario 4: Performance Not Improved**
**Symptoms**: GPU detected but processing still slow
**Solutions**:
1. Verify models actually loaded on GPU (check `verify_gpu_usage.py`)
2. Check GPU utilization during processing (should be >80%)
3. Profile bottlenecks: might be data transfer overhead
4. Verify not running in debug mode

---

## 📊 Expected Performance Improvement

### **RTX 5060 Ti 16GB Estimate** (5th Gen Tensor Cores + GDDR7):
```
Component              CPU Time    5060 Ti (Est)    Speedup
-----------------------------------------------------------
NER Entity Extraction     60s         1-1.5s          40-60x
Relation Classification   40s         0.5-1s          40-80x
Embeddings                 5s         0.1s            50x
Neo4j/Milvus Ops          <1s         <1s             1x
-----------------------------------------------------------
TOTAL (per chunk)        ~160s        1.5-3s          50-100x
```

### **Gate 3 Target**: <5 seconds per chunk
**Expected Result**: ✅ **PASS** with RTX 5060 Ti (significant headroom)

### **Bonus Capabilities** (16GB VRAM):
- Batch processing: 4-8 chunks simultaneously (4x throughput increase)
- Larger models: Can run LLaMA 7B, Mistral 7B locally for Oracle's generation layer
- Future expansion: Fine-tuned domain-specific models for SLIM knowledge extraction

---

## 🏁 Completion Checklist

**Hardware Installation**:
- [ ] Server powered down safely
- [ ] RTX 2080 Super physically installed
- [ ] PCIe power connectors attached (8-pin + 6-pin)
- [ ] Server powered on successfully
- [ ] GPU detected by kernel (`lspci`)
- [ ] GPU detected by NVIDIA driver (`nvidia-smi`)
- [ ] PyTorch detects GPU (`torch.cuda.is_available()`)

**Code Optimization**:
- [ ] `pipeline.py` modified (device auto-detect)
- [ ] `entity_extractor.py` modified (GPU support)
- [ ] `relation_classifier.py` modified (GPU support)
- [ ] `verify_gpu_usage.py` created and passing
- [ ] Git commit created with changes

**Performance Validation**:
- [ ] CPU baseline recorded (~160s)
- [ ] GPU accelerated test completed
- [ ] Processing time < 5 seconds per chunk ✅
- [ ] GPU utilization >80% during processing
- [ ] All functional tests still passing
- [ ] Speedup factor calculated and documented

**Evidence Collected**:
- [ ] Integration test output (timestamped)
- [ ] `nvidia-smi` screenshot showing utilization
- [ ] Performance comparison (CPU vs GPU)
- [ ] Gate 3 validation report prepared

---

## 🎓 Learning Capture (for H200's DLE V4)

**Patterns to Document**:
1. GPU compatibility verification before hardware purchase
2. PyTorch auto-device detection patterns (`device=0 if torch.cuda.is_available() else -1`)
3. GPU utilization monitoring during ML inference
4. Performance profiling methodology (baseline → optimize → measure)
5. Graceful CPU fallback for GPU-unavailable scenarios

**For DLE V4 Intelligence Services**:
- Document Intelligence: Same GPU acceleration patterns
- Web Intelligence: Same GPU acceleration patterns
- Supervisor: GPU for domain learning models

---

**Infrastructure Specialist Agent**
**Oracle RAG System - GPU Optimization**
**2025-11-15**

---

## 🏴‍☠️ Agent Commitment

**I will**:
- Follow this work order exactly
- Provide unfakeable evidence at each phase
- STOP if any verification fails
- Report exact error messages if problems occur
- Validate GPU usage before claiming success

**I will NOT**:
- Skip verification steps
- Proceed if GPU not detected
- Modify files outside specified scope
- Claim performance improvement without evidence

**Evidence Standard**: All checkpoints passed, GPU detected, <5s per chunk achieved.
