#!/bin/bash
# Deploy agents with separate Cloudflare Tunnels for launcher and endpoint
# Launcher URL = Controller, Endpoint URL = Direct Agent

set -e

echo "=========================================="
echo "AgentBeats Deployment - Separate URLs"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "Error: cloudflared is not installed"
    exit 1
fi

echo -e "${GREEN}✓${NC} Cloudflared is installed"
echo ""

# Generate deployment counter prefix
COUNTER_FILE="/tmp/agent_deployment_counter.txt"
if [ -f "$COUNTER_FILE" ]; then
    COUNTER=$(cat "$COUNTER_FILE")
else
    COUNTER=0
fi

# Increment and save
COUNTER=$((COUNTER + 1))
echo "$COUNTER" > "$COUNTER_FILE"

# Format as 3-digit prefix
PREFIX=$(printf "%03d" "$COUNTER")
echo -e "${GREEN}Deployment #${COUNTER}${NC} - Agent name prefix: ${PREFIX}"
echo ""

# Start Green Agent Controller in background
echo "1. Starting Green Agent Controller (port 9100)..."
python3 src/agentbeats/controller.py \
    --agent-name "${PREFIX}_Cyber Security Evaluator" \
    --agent-port 9010 \
    --controller-port 9100 \
    --launch-script "$(pwd)/run_green_agent.sh" \
    --working-dir "$(pwd)" \
    --auto-start > /tmp/green_controller.log 2>&1 &

GREEN_CONTROLLER_PID=$!
echo "   Controller PID: $GREEN_CONTROLLER_PID"

# Start Purple Agent Controller in background
echo ""
echo "2. Starting Purple Agent Controller (port 8200)..."
python3 src/agentbeats/controller.py \
    --agent-name "${PREFIX}_Home Automation Agent" \
    --agent-port 8000 \
    --controller-port 8200 \
    --launch-script "$(pwd)/run_purple_agent.sh" \
    --working-dir "$(pwd)" \
    --auto-start > /tmp/purple_controller.log 2>&1 &

PURPLE_CONTROLLER_PID=$!
echo "   Controller PID: $PURPLE_CONTROLLER_PID"

# Wait for controllers to start
echo ""
echo "3. Waiting for controllers to initialize (20 seconds)..."
sleep 20

# Check if controllers are running
echo ""
echo "4. Verifying controllers..."

if curl -s -f http://localhost:9100/health > /dev/null; then
    echo -e "${GREEN}✓${NC} Green Agent Controller is healthy"
else
    echo "Error: Green Agent Controller is not responding"
    kill $GREEN_CONTROLLER_PID $PURPLE_CONTROLLER_PID 2>/dev/null || true
    exit 1
fi

if curl -s -f http://localhost:8200/health > /dev/null; then
    echo -e "${GREEN}✓${NC} Purple Agent Controller is healthy"
else
    echo "Error: Purple Agent Controller is not responding"
    kill $GREEN_CONTROLLER_PID $PURPLE_CONTROLLER_PID 2>/dev/null || true
    exit 1
fi

# Start Cloudflare Tunnels - SEPARATE for launcher and endpoint
echo ""
echo "5. Starting Cloudflare Tunnels (4 total)..."
echo ""

# Green Agent - Launcher (Controller)
echo "   Green Agent Launcher (controller on port 9100)..."
cloudflared tunnel --url http://localhost:9100 > /tmp/green_launcher.log 2>&1 &
GREEN_LAUNCHER_PID=$!

# Green Agent - Endpoint (Direct Agent)
echo "   Green Agent Endpoint (agent on port 9010)..."
cloudflared tunnel --url http://localhost:9010 > /tmp/green_endpoint.log 2>&1 &
GREEN_ENDPOINT_PID=$!

# Purple Agent - Launcher (Controller)
echo "   Purple Agent Launcher (controller on port 8200)..."
cloudflared tunnel --url http://localhost:8200 > /tmp/purple_launcher.log 2>&1 &
PURPLE_LAUNCHER_PID=$!

# Purple Agent - Endpoint (Direct Agent)
echo "   Purple Agent Endpoint (agent on port 8000)..."
cloudflared tunnel --url http://localhost:8000 > /tmp/purple_endpoint.log 2>&1 &
PURPLE_ENDPOINT_PID=$!

# Wait for tunnels to establish
echo ""
echo "6. Waiting for tunnels to establish (15 seconds)..."
sleep 15

# Extract tunnel URLs from logs
echo ""
echo "=========================================="
echo "PUBLIC URLS FOR AGENTBEATS REGISTRATION"
echo "=========================================="
echo ""

# Green Agent URLs
GREEN_LAUNCHER_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/green_launcher.log | head -1)
GREEN_ENDPOINT_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/green_endpoint.log | head -1)

if [ -n "$GREEN_LAUNCHER_URL" ] && [ -n "$GREEN_ENDPOINT_URL" ]; then
    echo -e "${GREEN}Green Agent (${PREFIX}_Cyber Security Evaluator)${NC}"
    echo "  Launcher URL: $GREEN_LAUNCHER_URL"
    echo "  Endpoint URL: $GREEN_ENDPOINT_URL"
    echo ""
    echo "  Launcher Health: $GREEN_LAUNCHER_URL/"
    echo "  Launcher Status: $GREEN_LAUNCHER_URL/status"
    echo "  Agent Card:      $GREEN_ENDPOINT_URL/.well-known/agent-card.json"
    echo ""
    
    # Save URLs to files
    echo "$GREEN_LAUNCHER_URL" > /tmp/green_launcher_url.txt
    echo "$GREEN_ENDPOINT_URL" > /tmp/green_endpoint_url.txt
else
    echo -e "${YELLOW}Warning: Could not extract Green Agent URLs${NC}"
fi

# Purple Agent URLs
PURPLE_LAUNCHER_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/purple_launcher.log | head -1)
PURPLE_ENDPOINT_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/purple_endpoint.log | head -1)

if [ -n "$PURPLE_LAUNCHER_URL" ] && [ -n "$PURPLE_ENDPOINT_URL" ]; then
    echo -e "${GREEN}Purple Agent (${PREFIX}_Home Automation Agent)${NC}"
    echo "  Launcher URL: $PURPLE_LAUNCHER_URL"
    echo "  Endpoint URL: $PURPLE_ENDPOINT_URL"
    echo ""
    echo "  Launcher Health: $PURPLE_LAUNCHER_URL/"
    echo "  Launcher Status: $PURPLE_LAUNCHER_URL/status"
    echo "  Agent Card:      $PURPLE_ENDPOINT_URL/.well-known/agent-card.json"
    echo ""
fi

echo "=========================================="
echo ""
echo "Process IDs (for stopping later):"
echo "  Green Controller: $GREEN_CONTROLLER_PID"
echo "  Purple Controller: $PURPLE_CONTROLLER_PID"
echo "  Green Launcher Tunnel: $GREEN_LAUNCHER_PID"
echo "  Green Endpoint Tunnel: $GREEN_ENDPOINT_PID"
echo "  Purple Launcher Tunnel: $PURPLE_LAUNCHER_PID"
echo "  Purple Endpoint Tunnel: $PURPLE_ENDPOINT_PID"
echo ""
echo "To stop all services:"
echo "  kill $GREEN_CONTROLLER_PID $PURPLE_CONTROLLER_PID $GREEN_LAUNCHER_PID $GREEN_ENDPOINT_PID $PURPLE_LAUNCHER_PID $PURPLE_ENDPOINT_PID"
echo ""
echo "Logs:"
echo "  Green Controller:       tail -f /tmp/green_controller.log"
echo "  Purple Controller:      tail -f /tmp/purple_controller.log"
echo "  Green Launcher Tunnel:  tail -f /tmp/green_launcher.log"
echo "  Green Endpoint Tunnel:  tail -f /tmp/green_endpoint.log"
echo "  Purple Launcher Tunnel: tail -f /tmp/purple_launcher.log"
echo "  Purple Endpoint Tunnel: tail -f /tmp/purple_endpoint.log"
echo ""
echo "=========================================="
echo ""
echo -e "${YELLOW}NOTE:${NC} Now you have SEPARATE URLs for launcher and endpoint!"
echo "Launcher URL = Controller (state management, reset)"
echo "Endpoint URL = Direct Agent (agent card, evaluations)"
echo ""
echo "Press Ctrl+C to stop all services..."
echo ""

# Save PIDs to file for easy cleanup
echo "$GREEN_CONTROLLER_PID $PURPLE_CONTROLLER_PID $GREEN_LAUNCHER_PID $GREEN_ENDPOINT_PID $PURPLE_LAUNCHER_PID $PURPLE_ENDPOINT_PID" > /tmp/agentbeats_pids.txt

# Wait for user interrupt
trap "echo ''; echo 'Stopping all services...'; kill $GREEN_CONTROLLER_PID $PURPLE_CONTROLLER_PID $GREEN_LAUNCHER_PID $GREEN_ENDPOINT_PID $PURPLE_LAUNCHER_PID $PURPLE_ENDPOINT_PID 2>/dev/null; rm /tmp/agentbeats_pids.txt; echo 'Done.'; exit 0" INT

# Keep script running
wait
