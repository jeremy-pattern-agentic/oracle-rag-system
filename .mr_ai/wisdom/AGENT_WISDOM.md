# 🧠 Mr. AI Collective Intelligence

**Platform**: generic
**Framework**: Meta-Recursive AI Orchestrator v2.0.0
**Initialized**: 2025-11-21T20:20:14Z

This file contains the collective wisdom of all agents. Every failure teaches us. Every success proves a pattern.

## 🚫 Known Failures (DO NOT REPEAT)
| Date | Agent | Task | What Failed | Root Cause | Lesson Learned |
|------|-------|------|------------|------------|----------------|
| Init | System | Setup | Example entry | Template | Always verify with evidence |

## ✅ Proven Solutions
| Component | Problem | Solution | Evidence | Reuse Count |
|-----------|---------|----------|----------|-------------|
| System | Initialization | Run init_mr_ai.sh | Framework created | 1 |

## 🎯 Current System State
| Component | Status | Last Verified | Health | Notes |
|-----------|--------|---------------|--------|-------|
| Frontend | UNKNOWN | Never | - | Awaiting initialization |
| Backend | UNKNOWN | Never | - | Awaiting initialization |
| Database | UNKNOWN | Never | - | Awaiting initialization |
| Services | UNKNOWN | Never | - | Awaiting initialization |

## 🔄 Active Investigations
| Agent | Issue | Hypothesis | Next Test | Priority |
|-------|-------|------------|-----------|----------|
| - | - | - | - | - |

## 📚 Reusable Patterns

### Pattern: Evidence-First Validation
**Context**: Any validation task
**Problem**: Agents claim success without proof
**Solution**: Require paste of actual output
**Implementation**:
```bash
# Never accept description, always require:
command_here | tee output.log
cat output.log  # Paste this
```
**Success Rate**: 100%
**Platforms**: All (Claude Code, Cursor, Windsurf, API)

### Pattern: External Validation
**Context**: Testing any web service
**Problem**: Localhost works but external access fails
**Solution**: Always test from external IP
**Implementation**:
```bash
# Read server IP from config
SERVER_IP=$(grep "server_ip:" .mr_ai/config.yaml | awk '{print $2}')
curl -v http://$SERVER_IP:PORT/endpoint
```
**Success Rate**: 100%
**Platforms**: All

### Pattern: Platform-Agnostic Service Management
**Context**: Starting/stopping any service
**Problem**: Manual process management causes conflicts
**Solution**: Use configured service backend
**Implementation**:
```bash
# Read service backend from config
BACKEND=$(grep "type:" .mr_ai/config.yaml | grep service_backend -A1 | tail -1 | awk '{print $2}')
# Use appropriate manager: service_manager, systemd, docker-compose, etc.
```
**Success Rate**: 100%
**Platforms**: All

## 🛡️ Guard Rails

### Never Trust Without Evidence
• "Should work" → REJECTED
• "Appears to work" → REJECTED
• "I think it's fixed" → REJECTED
• Actual output → ACCEPTED

### The Three Laws of Mr. AI
1. An agent must provide evidence for all claims
2. An agent must use external validation except where config allows localhost
3. An agent must protect its own integrity as long as such protection doesn't conflict with the First or Second Laws

## 📈 Metrics
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Success Rate | 0% | >80% | 🔴 |
| Evidence Quality | 0% | 100% | 🔴 |
| False Positives | 0 | 0 | 🟢 |
| Wisdom Entries | 3 | >50 | 🔴 |

**Last Updated**: Framework Initialization
**Next Review**: After first 10 tasks
**Platform Notes**: Configured for generic - patterns work across all platforms
