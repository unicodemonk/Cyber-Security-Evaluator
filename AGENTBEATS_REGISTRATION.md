# AgentBeats Platform Registration Guide

**Register and run your agents on the AgentBeats platform (agentbeats.org)**

This guide covers registration for both:
- **Green Agent**: Cybersecurity Evaluator (`cybersecurity_evaluator.py`)
- **Purple Agent**: Home Automation Agent (`home_automation_agent.py`)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Getting Your Public IP](#getting-your-public-ip)
3. [Green Agent Registration](#green-agent-registration)
4. [Purple Agent Registration](#purple-agent-registration)
5. [Docker Deployment (Recommended)](#docker-deployment-recommended)
6. [Local Development Setup](#local-development-setup)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required
- Python 3.10+ installed
- Public IP address or domain name (for AgentBeats to reach your agents)
- Network configured to allow incoming connections on ports 8000 and 9010

### Optional
- Docker and Docker Compose (recommended for production)
- LLM API keys (OpenAI, Anthropic, or Google) for enhanced evaluation

---

## Getting Your Public IP

AgentBeats needs to communicate with your agents via HTTP. You must expose your agents with a public IP or domain.

### Method 1: Check Your Public IP

```bash
# Using curl
curl -s ifconfig.me

# Using dig
dig +short myip.opendns.com @resolver1.opendns.com

# Using wget
wget -qO- ipinfo.io/ip
```

### Method 2: Cloud Deployment (Recommended)

Deploy on cloud providers for reliable public access:

**AWS EC2:**
```bash
# Get instance public IP
curl http://169.254.169.254/latest/meta-data/public-ipv4
```

**Google Cloud:**
```bash
# Get external IP
curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip
```

**Azure:**
```bash
# Get public IP
curl -H Metadata:true "http://169.254.169.254/metadata/instance/network/interface/0/ipv4/ipAddress/0/publicIpAddress?api-version=2021-02-01&format=text"
```

**DigitalOcean:**
```bash
# Get droplet public IP
curl http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address
```

### Method 3: Using ngrok (Development/Testing)

For local development, use ngrok to expose your agents:

```bash
# Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Authenticate (get token from ngrok.com)
ngrok config add-authtoken YOUR_NGROK_TOKEN

# Expose Green Agent (port 9010)
ngrok http 9010

# In another terminal, expose Purple Agent (port 8000)
ngrok http 8000
```

Use the ngrok URLs (e.g., `https://abc123.ngrok.io`) for AgentBeats registration.

### Method 4: Port Forwarding (Home Network)

If running from home:
1. Log into your router admin panel
2. Forward port 8000 to your machine (Purple Agent)
3. Forward port 9010 to your machine (Green Agent)
4. Use your public IP from `curl ifconfig.me`

---

## Green Agent Registration

The Green Agent (`cybersecurity_evaluator.py`) is a security evaluator that tests Purple Agents for vulnerabilities.

### Agent Details

| Property | Value |
|----------|-------|
| Name | Cyber Security Evaluator |
| Type | Green Agent (Security Evaluator) |
| Port | 9010 |
| Agent Card URL | `http://YOUR_IP:9010/.well-known/agent-card.json` |
| RPC Endpoint | `http://YOUR_IP:9010/` |

### Step 1: Start the Green Agent

**Using Docker (Recommended):**
```bash
docker-compose up -d green-agent
```

**Using Python directly:**
```bash
# Install dependencies
uv sync  # or: pip install -r requirements.txt

# Start the agent (bind to all interfaces for external access)
python green_agents/cybersecurity_evaluator.py --host 0.0.0.0 --port 9010
```

### Step 2: Verify Agent is Running

```bash
# Check agent card is accessible
curl http://localhost:9010/.well-known/agent-card.json

# Expected response:
{
  "name": "Cyber Security Evaluator",
  "description": "Green Agent for evaluating cybersecurity detection capabilities...",
  "url": "http://localhost:9010/",
  "version": "1.0.0",
  ...
}
```

### Step 3: Register on AgentBeats

1. Go to [https://agentbeats.org](https://agentbeats.org)
2. Log in or create an account
3. Navigate to **Register Agent** or **My Agents**
4. Fill in the registration form:

| Field | Value |
|-------|-------|
| Agent Name | Cyber Security Evaluator |
| Agent Type | Green Agent |
| Description | AI Agent Security Evaluator with MITRE ATT&CK & ATLAS integration. Tests Purple Agents for vulnerabilities using multi-agent framework with 975+ techniques. |
| Agent Card URL | `http://YOUR_PUBLIC_IP:9010/.well-known/agent-card.json` |
| Endpoint URL | `http://YOUR_PUBLIC_IP:9010/` |
| Category | Security / Cybersecurity |
| Tags | security, mitre, atlas, attack, vulnerability, testing |

5. Click **Register** or **Submit**

### Step 4: Test Registration

AgentBeats will verify your agent by fetching the agent card. Ensure:
- Port 9010 is open to the internet
- Firewall allows incoming connections
- Agent is running and responding

---

## Purple Agent Registration

The Purple Agent (`home_automation_agent.py`) is the target system being tested for security vulnerabilities.

### Agent Details

| Property | Value |
|----------|-------|
| Name | HomeAutomationAgent |
| Type | Purple Agent (Target System) |
| Port | 8000 |
| Agent Card URL | `http://YOUR_IP:8000/.well-known/agent-card.json` |
| Command Endpoint | `http://YOUR_IP:8000/` or `http://YOUR_IP:8000/command` |

### Step 1: Start the Purple Agent

**Using Docker (Recommended):**
```bash
docker-compose up -d purple-agent
```

**Using Python directly:**
```bash
# Install dependencies
uv sync  # or: pip install -r requirements.txt

# Start the agent (bind to all interfaces for external access)
python purple_agents/home_automation_agent.py --host 0.0.0.0 --port 8000
```

### Step 2: Verify Agent is Running

```bash
# Check agent card is accessible
curl http://localhost:8000/.well-known/agent-card.json

# Expected response:
{
  "name": "HomeAutomationAgent",
  "description": "Home Automation Purple Agent (Target System for Security Testing)...",
  "url": "http://127.0.0.1:8000",
  "version": "1.0.0",
  "skills": [{
    "id": "home_automation",
    "name": "Home Automation Control",
    ...
  }]
}
```

### Step 3: Register on AgentBeats

1. Go to [https://agentbeats.org](https://agentbeats.org)
2. Log in to your account
3. Navigate to **Register Agent** or **My Agents**
4. Fill in the registration form:

| Field | Value |
|-------|-------|
| Agent Name | HomeAutomationAgent |
| Agent Type | Purple Agent |
| Description | Home Automation Purple Agent - Target system for security testing. Controls heating, cooling, plant watering, grocery ordering, meal planning, and more via natural language commands. Intentionally vulnerable for AgentBeats competition. |
| Agent Card URL | `http://YOUR_PUBLIC_IP:8000/.well-known/agent-card.json` |
| Endpoint URL | `http://YOUR_PUBLIC_IP:8000/` |
| Category | IoT / Smart Home |
| Tags | home-automation, iot, smart-home, vulnerable-target, purple-agent |

5. Click **Register** or **Submit**

### Step 4: Test Registration

Verify the Purple Agent is accessible:
```bash
# Test command endpoint
curl -X POST http://YOUR_PUBLIC_IP:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "kind": "message",
    "role": "user",
    "parts": [{
      "kind": "text",
      "text": "{\"command\": \"Set heating to warm\", \"parameters\": {}}"
    }]
  }'
```

---

## Docker Deployment (Recommended)

Deploy both agents using Docker Compose for production reliability.

### Step 1: Build Containers

```bash
docker-compose build
```

### Step 2: Start Both Agents

```bash
# Start both agents
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### Step 3: Verify Endpoints

```bash
# Green Agent
curl http://localhost:9010/.well-known/agent-card.json

# Purple Agent
curl http://localhost:8000/.well-known/agent-card.json
```

### Step 4: Get Container IPs (if needed)

```bash
# Get container IP addresses
docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' cybersecurity_evaluator
docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' home_automation_agent
```

### Step 5: Cloud Deployment

For cloud deployment with public access:

**Docker on EC2/GCE/Azure:**
```bash
# Ensure security groups/firewall allows ports 8000 and 9010
# Start containers
docker-compose up -d

# Use your instance's public IP for registration
```

**Docker with SSL (using nginx reverse proxy):**
```bash
# Use nginx with certbot for HTTPS
# Then register with https://your-domain.com URLs
```

---

## Local Development Setup

For testing before cloud deployment:

### Terminal 1: Start Purple Agent

```bash
uv run python purple_agents/home_automation_agent.py --host 0.0.0.0 --port 8000
```

### Terminal 2: Start Green Agent

```bash
uv run python green_agents/cybersecurity_evaluator.py --host 0.0.0.0 --port 9010
```

### Terminal 3: Run Security Evaluation

```bash
# Test the Green Agent evaluating the Purple Agent
curl -X POST http://localhost:9010/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tasks/send",
    "id": "1",
    "params": {
      "message": {
        "role": "user",
        "parts": [{
          "type": "data",
          "data": {
            "participants": {
              "purple_agent": "http://localhost:8000"
            },
            "config": {
              "scenario": "prompt_injection",
              "max_rounds": 10,
              "budget_usd": 5.0,
              "use_sandbox": false
            }
          }
        }]
      }
    }
  }'
```

---

## Verification

### Verify Agent Card Access

```bash
# Green Agent
curl -I http://YOUR_PUBLIC_IP:9010/.well-known/agent-card.json
# Should return: HTTP/1.1 200 OK

# Purple Agent
curl -I http://YOUR_PUBLIC_IP:8000/.well-known/agent-card.json
# Should return: HTTP/1.1 200 OK
```

### Verify A2A Compliance

Both agents follow the A2A (Agent-to-Agent) protocol:
- Expose agent card at `/.well-known/agent-card.json`
- Accept JSON-RPC requests at root `/`
- Return A2A formatted responses

### Test from External Network

From a different machine or network:
```bash
# Replace with your actual public IP
curl http://YOUR_PUBLIC_IP:9010/.well-known/agent-card.json
curl http://YOUR_PUBLIC_IP:8000/.well-known/agent-card.json
```

---

## Troubleshooting

### Port Already in Use

```bash
# Kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Kill process using port 9010
lsof -ti:9010 | xargs kill -9
```

### Cannot Connect from Internet

1. **Check firewall:**
   ```bash
   # Ubuntu/Debian
   sudo ufw allow 8000/tcp
   sudo ufw allow 9010/tcp

   # CentOS/RHEL
   sudo firewall-cmd --add-port=8000/tcp --permanent
   sudo firewall-cmd --add-port=9010/tcp --permanent
   sudo firewall-cmd --reload
   ```

2. **Check cloud security groups:**
   - AWS: Edit Security Group inbound rules
   - GCP: Edit VPC firewall rules
   - Azure: Edit Network Security Group

3. **Check agent is binding to 0.0.0.0:**
   ```bash
   # Must use --host 0.0.0.0 for external access
   python green_agents/cybersecurity_evaluator.py --host 0.0.0.0 --port 9010
   ```

### Agent Card Not Found

Ensure the agent is running and check logs:
```bash
# Docker
docker-compose logs green-agent
docker-compose logs purple-agent

# Local
# Check terminal output for errors
```

### Docker Health Check Failing

```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' cybersecurity_evaluator
docker inspect --format='{{.State.Health.Status}}' home_automation_agent

# View health check logs
docker inspect --format='{{json .State.Health}}' cybersecurity_evaluator | jq
```

### Network Issues Between Containers

```bash
# Verify containers are on same network
docker network inspect securityevaluator_agent-network

# Test connectivity between containers
docker exec cybersecurity_evaluator curl http://purple-agent:8000/.well-known/agent-card.json
```

---

## Quick Reference

### URLs for Registration

| Agent | Agent Card URL | Endpoint URL |
|-------|----------------|--------------|
| Green Agent | `http://YOUR_IP:9010/.well-known/agent-card.json` | `http://YOUR_IP:9010/` |
| Purple Agent | `http://YOUR_IP:8000/.well-known/agent-card.json` | `http://YOUR_IP:8000/` |

### Commands Summary

```bash
# Get public IP
curl -s ifconfig.me

# Start with Docker
docker-compose up -d

# Start locally
python green_agents/cybersecurity_evaluator.py --host 0.0.0.0 --port 9010
python purple_agents/home_automation_agent.py --host 0.0.0.0 --port 8000

# Verify agent cards
curl http://localhost:9010/.well-known/agent-card.json
curl http://localhost:8000/.well-known/agent-card.json

# Open firewall ports
sudo ufw allow 8000/tcp && sudo ufw allow 9010/tcp
```

### AgentBeats Registration Checklist

- [ ] Agents are running and accessible
- [ ] Public IP or domain is configured
- [ ] Ports 8000 and 9010 are open
- [ ] Agent cards return valid JSON
- [ ] Registered both agents on agentbeats.org
- [ ] Tested connectivity from external network

---

## Support

- **AgentBeats Platform**: [https://agentbeats.org](https://agentbeats.org)
- **Project Documentation**: See `README.md` in this repository
- **Issues**: Check logs and troubleshooting section above

---

**Last Updated**: November 2025
