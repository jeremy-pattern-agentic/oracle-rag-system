#!/bin/bash
# Work Order Generator for Mr. AI (Platform Agnostic)

TEMPLATE=".mr_ai/templates/WORK_ORDER_TEMPLATE.md"
OUTPUT_DIR=".mr_ai/agents/work_orders"
CONFIG_FILE=".mr_ai/config.yaml"

TIMESTAMP=$(date +"%Y-%m-%d-%H-%M")
ORDER_NUM=$(ls -1 $OUTPUT_DIR 2>/dev/null | wc -l | xargs printf "%03d")
ORDER_ID="WO-${TIMESTAMP}-${ORDER_NUM}"

if [[ ! -f "$TEMPLATE" ]]; then
    echo "Error: Template not found at $TEMPLATE"
    exit 1
fi

OUTPUT_FILE="${OUTPUT_DIR}/${ORDER_ID}.md"

# Copy template and update Order ID
sed "s/\[WO-YYYY-MM-DD-HH-MM-###\]/$ORDER_ID/g" "$TEMPLATE" > "$OUTPUT_FILE"

# If config exists, add platform info
if [[ -f "$CONFIG_FILE" ]]; then
    PLATFORM=$(grep "ai_assistant:" "$CONFIG_FILE" | awk '{print $2}' || echo "generic")
    sed -i "s/\[Claude Code|Cursor|Windsurf|API|Generic\]/$PLATFORM/g" "$OUTPUT_FILE"
fi

echo "✅ Work Order created: $OUTPUT_FILE"
echo "📝 Edit the work order and assign to appropriate agent"
echo "🔧 Environment configuration available in .mr_ai/config.yaml"
