#!/bin/bash
# Launch script for Green Agent (Cyber Security Evaluator)
# Used by AgentBeats Controller to start the agent

set -e

echo "Starting Cyber Security Evaluator (Green Agent)..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Read deployment counter for agent name prefix
COUNTER_FILE="/tmp/agent_deployment_counter.txt"
if [ -f "$COUNTER_FILE" ]; then
    COUNTER=$(cat "$COUNTER_FILE")
    PREFIX=$(printf "%03d" "$COUNTER")
else
    PREFIX=""
fi

# Start the Green Agent
# Bind to 0.0.0.0 for external access
if [ -n "$PREFIX" ]; then
    python3 green_agents/cybersecurity_evaluator.py \
        --host 0.0.0.0 \
        --port 9010 \
        --enable-llm \
        --name-prefix "$PREFIX"
else
    python3 green_agents/cybersecurity_evaluator.py \
        --host 0.0.0.0 \
        --port 9010 \
        --enable-llm
fi

echo "Green Agent started on port 9010"
