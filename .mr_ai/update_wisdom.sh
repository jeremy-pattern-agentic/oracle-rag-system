#!/bin/bash
# Update Agent Wisdom (Platform Agnostic)

WISDOM_FILE=".mr_ai/wisdom/AGENT_WISDOM.md"
TIMESTAMP=$(date +"%Y-%m-%d")

echo "📝 Updating Agent Wisdom..."
echo ""
echo "Choose update type:"
echo "1) Add Failure"
echo "2) Add Success"
echo "3) Update State"
echo "4) Add Pattern"
read -p "Choice (1-4): " choice

case $choice in
1)
    read -p "Agent name: " agent
    read -p "What failed: " what
    read -p "Root cause: " cause
    read -p "Lesson learned: " lesson

    # Add to failures table
    echo "| $TIMESTAMP | $agent | Task | $what | $cause | $lesson |" >> $WISDOM_FILE
    echo "✅ Failure logged"
    ;;
2)
    read -p "Component: " component
    read -p "Problem solved: " problem
    read -p "Solution: " solution

    # Add to successes
    echo "| $component | $problem | $solution | Verified | 1 |" >> $WISDOM_FILE
    echo "✅ Success logged"
    ;;
3)
    echo "Update state manually in $WISDOM_FILE"
    ;;
4)
    echo "Add pattern manually in $WISDOM_FILE"
    ;;
*)
    echo "Invalid choice"
    ;;
esac

echo ""
echo "Remember: Our failures make us stronger!"
