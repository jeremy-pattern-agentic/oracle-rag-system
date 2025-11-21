#!/bin/bash
# Mr. AI Framework Test Suite (Platform Agnostic)

echo "🎯 Mr. AI Framework Verification"
echo "================================"

PYTHON="./.venv/bin/python"
PASS=0
FAIL=0

# Test function
test_component() {
    local name=$1
    local command=$2

    echo -n "Testing $name... "

    if eval "$command" > /dev/null 2>&1; then
        echo "✅ PASS"
        ((PASS++))
    else
        echo "❌ FAIL"
        ((FAIL++))
    fi
}

# Run tests
test_component "Directory Structure" "[ -d .mr_ai/agents ]"
test_component "Config File" "[ -f .mr_ai/config.yaml ]"
test_component "Work Order Template" "[ -f .mr_ai/templates/WORK_ORDER_TEMPLATE.md ]"
test_component "Validation Script" "[ -f .mr_ai/validation/validate_evidence.py ]"
test_component "Wisdom System" "[ -f .mr_ai/wisdom/AGENT_WISDOM.md ]"
test_component "Orchestrator Rules" "[ -f .mr_ai/ORCHESTRATOR_RULES.md ]"
test_component "Python Available" "$PYTHON -c 'import sys; sys.exit(0)'"

# Platform detection test
echo -n "Testing Platform Detection... "
if grep -q "ai_assistant:" .mr_ai/config.yaml; then
    echo "✅ PASS"
    ((PASS++))
    PLATFORM=$(grep "ai_assistant:" .mr_ai/config.yaml | awk '{print $2}')
    echo "   Detected platform: $PLATFORM"
else
    echo "❌ FAIL"
    ((FAIL++))
fi

# Evidence validation test
echo -n "Testing Evidence Validator... "
cat << 'EVIDENCE' | $PYTHON .mr_ai/validation/validate_evidence.py --stdin > /dev/null 2>&1
EVIDENCE[Test-2024-01-01-12:00]:
├── Test 1: [PASS]
├── Test 2: [PASS]
├── Test 3: [PASS]
├── External: [curl http://example.com result]
└── Stability: [3/3 successful]

RAW OUTPUT:
$ echo "Test 1"
Test 1
$ echo "Test 2"
Test 2
$ echo "Test 3"
Test 3
$ curl -s http://example.com | head -1
<!doctype html>
$ for i in {1..3}; do echo "Iteration $i: SUCCESS"; done
Iteration 1: SUCCESS
Iteration 2: SUCCESS
Iteration 3: SUCCESS
Framework validation test complete - all patterns detected and validated successfully
EVIDENCE

if [ $? -eq 0 ]; then
    echo "✅ PASS"
    ((PASS++))
else
    echo "❌ FAIL"
    ((FAIL++))
fi

echo "================================"
echo "Results: $PASS passed, $FAIL failed"
echo "Platform: Configured for multi-platform use"

if [ $FAIL -eq 0 ]; then
    echo "✅ Framework validation successful!"
    exit 0
else
    echo "❌ Framework validation failed"
    exit 1
fi
