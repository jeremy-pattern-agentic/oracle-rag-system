# Agent Work Order
**Order ID**: [WO-YYYY-MM-DD-HH-MM-###]
**Agent Type**: [Frontend|Backend|Audio|Database|QA|etc]
**Priority**: [Critical|High|Normal|Low]
**Platform**: [Claude Code|Cursor|Windsurf|API|Generic]

## 📋 Pre-Flight Agreement
By accepting this work order, I acknowledge:
- [ ] SUCCESS = External validation with evidence
- [ ] I will use configured service management (see .mr_ai/config.yaml)
- [ ] I will paste RAW OUTPUT, not descriptions
- [ ] I will report uncertainty > false positives
- [ ] I will update AGENT_WISDOM.md upon completion

## 🎯 Objective
[Single, specific, measurable objective - one sentence max]

## ✅ Acceptance Criteria (ALL must pass)
1. [ ] [Specific measurable outcome]
2. [ ] [External validation test - use configured server IP from config]
3. [ ] [Integration verification]
4. [ ] [3x stability test passes]

## 🔒 Constraints
- Max files to modify: [usually 1-2]
- Max lines of code: [usually <100]
- Time limit: 30 minutes
- Must use: [specific tools/libraries]
- Environment: See .mr_ai/config.yaml for project specifics

## 📁 Context Files
File 1: [path] - Lines [X-Y] - [what to look for]
File 2: [path] - [specific context]

## ⚠️ Known Pitfalls (from AGENT_WISDOM.md)
- [Common failure mode 1]
- [Common failure mode 2]

## 📊 Required Evidence Format
```bash
# Test 1: [Description]
[EXACT COMMAND TO RUN]
# EXPECTED OUTPUT: [what should appear]

# Test 2: External Validation (MANDATORY)
# Read server IP from .mr_ai/config.yaml
curl -v http://[SERVER_IP]:[PORT]/[endpoint]
# EXPECTED: [specific response]

# Test 3: Stability Check
for i in {1..3}; do [command]; sleep 1; done
# EXPECTED: 3 identical successful outputs
```

## 🚫 Forbidden Actions
• NO manual process starts (use configured service management)
• NO localhost-only testing (unless config allows)
• NO "should work" or "appears to work" claims
• NO code without evidence
• NO skipping stability checks

## 📝 Completion Checklist
• [ ] All acceptance criteria met with evidence
• [ ] External validation screenshot/output provided
• [ ] 3x stability test passed
• [ ] AGENT_WISDOM.md updated with outcome
• [ ] Evidence block in correct format
• [ ] Raw terminal output included

## 🎭 Evidence Submission Format
```
EVIDENCE[AgentType-YYYY-MM-DD-HH:MM]:
├── Test 1: [PASS with output snippet]
├── Test 2: [PASS with curl result]
├── Test 3: [PASS with 3x confirmation]
├── External: [curl from configured SERVER_IP]
└── Stability: [3/3 successful runs]

RAW OUTPUT:
[PASTE COMPLETE TERMINAL OUTPUT HERE]
[DO NOT SUMMARIZE OR DESCRIBE]

Platform: [AI Assistant Used]
Orchestrator Sign-off: [Orchestrator ID]
Timestamp: [ISO timestamp]
```
