# Agent Independence & Discovery Protocol

## TL;DR

✅ **Green Agent and Purple Agent are 100% independent**
✅ **Discovery happens via standard A2A protocol (`/.well-known/agent-card.json`)**
✅ **No shared code, no shared types, no hardcoded knowledge**

## What is `.well-known`?

### IETF Standard (RFC 8615)

`.well-known` is an **industry-wide standard** for service discovery, used by:
- GitHub (security contact)
- Google (OAuth discovery)
- Apple (app associations)
- Matrix (server discovery)
- A2A Protocol (agent discovery)

**Why this directory name?**
- **Standard location** - Everyone knows where to look
- **No configuration needed** - Works out of the box
- **Zero prior knowledge** - Just need URL
- **HTTP-friendly** - Works with any HTTP client

### Real-World Examples

You can try these right now:

```bash
# GitHub's security contact
curl https://github.com/.well-known/security.txt

# Google's OAuth configuration
curl https://accounts.google.com/.well-known/openid-configuration

# Our Purple Agent
curl http://127.0.0.1:8000/.well-known/agent-card.json
```

**All use the same pattern:** `<base_url>/.well-known/<resource>`

## How Green Agent Discovers Purple Agent

### Step 1: Given Only URL

```python
# Green Agent's ONLY input
purple_endpoint = "http://127.0.0.1:8000"

# That's it! No other knowledge needed!
```

### Step 2: Discover Capabilities (A2A Standard)

```python
# Fetch AgentCard from standard location
agent_card = GET f"{purple_endpoint}/.well-known/agent-card.json"

# Returns:
{
  "name": "HomeAutomationAgent",
  "version": "1.0.0",
  "description": "Controls household systems...",
  "skills": [
    {
      "name": "Home Automation Control",
      "description": "heating/cooling, plants, groceries...",
      "examples": [
        '{"command": "Set heating to warm", "parameters": {}}'
      ],
      "tags": ["home-automation", "iot", "smart-home"]
    }
  ]
}
```

### Step 3: Generate Attacks from Discovery

```python
# Parse AgentCard to understand Purple Agent
for skill in agent_card['skills']:
    # Extract capabilities
    capabilities = skill['description']
    input_format = skill['examples']
    tags = skill['tags']

    # Generate attacks targeting those capabilities
    if 'natural language' in capabilities:
        generate_prompt_injection_attacks()

    if 'parameters' in input_format:
        generate_parameter_manipulation_attacks()

    if 'system' in capabilities:
        generate_command_injection_attacks()
```

### Step 4: Test Purple Agent

```python
# Send attacks using discovered format
for attack in attacks:
    response = POST f"{purple_endpoint}/command", json=attack

    # Evaluate exploitation
    if response['success']:
        # Purple Agent was exploited!
```

## No Dependencies!

### What Green Agent DOES NOT Know:

- ❌ Purple Agent's implementation language
- ❌ Purple Agent's framework
- ❌ Purple Agent's internal structure
- ❌ Purple Agent's data models
- ❌ Specific attack templates for this Purple Agent
- ❌ ANY code from Purple Agent

### What Green Agent ONLY Knows:

- ✅ URL endpoint
- ✅ A2A protocol standard (/.well-known/agent-card.json)
- ✅ HTTP/JSON basics

### What Green Agent DISCOVERS:

- ✅ Agent name and version
- ✅ Agent capabilities (from description)
- ✅ Input format (from examples)
- ✅ Available skills
- ✅ Potential attack vectors (inferred from capabilities)

## Benefits of This Architecture

### 1. True Independence
```
Green Agent              Purple Agent
    |                        |
    |-- Only knows URL ----->|
    |                        |
    |<-- AgentCard ---------/
    |   (discovers caps)     |
    |                        |
    |-- Attacks ------------>|
    |                        |
    |<-- Responses ----------|
```

No shared code between them!

### 2. Works with ANY A2A-Compliant Agent

Our Green Agent can test:
- ✅ Home Automation Agent (our implementation)
- ✅ Banking Agent (hypothetical)
- ✅ Email Assistant (hypothetical)
- ✅ Code Generator (hypothetical)
- ✅ ANY agent exposing `/.well-known/agent-card.json`

### 3. Competition-Ready

In AgentBeats competition:
```
┌─────────────────┐         ┌─────────────────┐
│  Green Agent A  │         │ Purple Agent 1  │
│  (Our impl)     │────────>│ (Unknown impl)  │
└─────────────────┘         └─────────────────┘
                    Discovers via AgentCard

┌─────────────────┐         ┌─────────────────┐
│  Green Agent B  │         │ Purple Agent    │
│  (Unknown impl) │────────>│ (Our impl)      │
└─────────────────┘         └─────────────────┘
                    Works with any Green Agent
```

### 4. No Configuration Needed

Traditional approach (BAD):
```yaml
# config.yaml - Purple Agent specific!
purple_agent:
  type: "home_automation"
  endpoints:
    commands: "/api/v1/commands"
    status: "/api/v1/status"
  authentication: "bearer"
  capabilities:
    - heating
    - cooling
    - plants
```

A2A approach (GOOD):
```python
# Just URL - everything else discovered!
purple_endpoint = "http://127.0.0.1:8000"
```

## Implementation Files

### Purple Agent (Zero Dependencies)

```
purple_agents/home_automation_agent.py
  ├── Exposes: /.well-known/agent-card.json
  ├── Exposes: /command endpoint
  ├── Uses: Only standard Python + A2A SDK
  └── Depends on: NOTHING from Green Agent
```

### Green Agent (Zero Purple Knowledge)

```
green_agents/cybersecurity_evaluator.py
  ├── Discovers: Purple Agent via AgentCard
  ├── Generates: Attacks based on discovery
  ├── Evaluates: Exploitation from responses
  └── Works with: ANY A2A-compliant Purple Agent
```

### Discovery Demo

```bash
# Run demonstration
python3 demo_independence.py

# Shows:
# 1. Green Agent starts with only URL
# 2. Discovers capabilities via AgentCard
# 3. Generates attacks from discovery
# 4. Tests Purple Agent
# 5. Works with ZERO prior knowledge
```

## Why This Matters for AgentBeats

### Competition Scenario 1: Test Unknown Purple Agents

```python
# Competition provides Purple Agent URLs
purple_agents = [
    "http://competitor1.com:8000",
    "http://competitor2.com:8000",
    "http://competitor3.com:8000"
]

# Our Green Agent can test ALL of them!
for endpoint in purple_agents:
    # Discover
    agent_card = discover(endpoint)

    # Generate attacks
    attacks = generate_attacks(agent_card)

    # Test
    results = test_agent(endpoint, attacks)

    # Score
    exploitation_rate = calculate_metrics(results)
```

### Competition Scenario 2: Test Our Purple Agent

```python
# Competition's Green Agents test our Purple Agent
# They only get: "http://our-agent.com:8000"

# They discover via AgentCard:
GET http://our-agent.com:8000/.well-known/agent-card.json

# They generate attacks based on our capabilities
# They test our security
# NO coordination needed!
```

## Summary

| Aspect | Traditional Approach | A2A Approach |
|--------|---------------------|--------------|
| **Discovery** | Manual configuration | Automatic via `.well-known` |
| **Dependencies** | Tight coupling | Zero coupling |
| **Scalability** | One-to-one | Many-to-many |
| **Flexibility** | Hardcoded | Dynamic generation |
| **Standards** | Custom | IETF RFC 8615 + A2A |
| **Competition Ready** | ❌ No | ✅ Yes |

**The `.well-known` standard enables true agent independence!**
