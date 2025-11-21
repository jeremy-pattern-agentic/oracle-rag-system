#!/bin/bash
# Quick evidence validation (platform-agnostic)

VALIDATOR="./.venv/bin/python .mr_ai/validation/validate_evidence.py"

# Check if PyYAML is installed
if ! ./.venv/bin/python -c "import yaml" 2>/dev/null; then
    echo "⚠️  Installing PyYAML dependency..."
    ./.venv/bin/python -m pip install -q pyyaml
fi

if [[ -z "$1" ]]; then
    echo "Usage: ./validate.sh <evidence_file>"
    exit 1
fi

echo "🔍 Validating evidence..."
$VALIDATOR "$1" | jq '.' 2>/dev/null || $VALIDATOR "$1"

if [[ $? -eq 0 ]]; then
    echo "✅ Evidence validated successfully"
else
    echo "❌ Evidence validation failed"
fi
