# Green Agents - Security Evaluators

This directory contains **Green Agents** - security evaluators that test Purple Agents (target systems) by attacking them with various security exploits.

---

## 🎯 What is a Green Agent?

A **Green Agent** is a **security evaluator** that attacks Purple Agents (target systems) to find vulnerabilities.

**Key Concepts:**
- ✅ Purple Agent = Target system being tested (e.g., home automation, chatbot)
- ✅ Green Agent = Security evaluator that attacks the Purple Agent
- ✅ Uses generic attack scenarios (prompt injection, SQL injection, etc.)
- ✅ Discovers Purple Agent capabilities via A2A protocol
- ✅ Zero dependencies - communicates via HTTP

---

## 🏗️ Current Architecture

```
Attack Scenarios (Generic)
    ↓
Green Agent (Security Evaluator)
    ↓ HTTP / A2A Protocol
Purple Agent (Target System)
```

**Attack-Type Based:**
- Scenarios are generic (e.g., `prompt_injection`, `sql_injection`)
- NOT agent-specific (works with ANY Purple Agent)
- Purple Agent is discovered via `/.well-known/agent-card.json`

---

## 📁 Files

```
green_agents/
├── cybersecurity_evaluator.py    # Production Green Agent (AgentBeats compliant)
└── README.md                      # This file
```

---

## 🚀 Quick Start

### **Option 1: Development Test (Recommended)**

```bash
# One-command test (starts Purple Agent + runs tests)
./tests/run_tests.sh
```

### **Option 2: Manual Testing**

```bash
# Terminal 1: Start Purple Agent (target system)
python3 purple_agents/home_automation_agent.py --port 8000

# Terminal 2: Run development test
python3 tests/dev_quick_test.py
```

### **Option 3: Production Green Agent**

```bash
# Terminal 1: Start Purple Agent
python3 purple_agents/home_automation_agent.py --port 8000

# Terminal 2: Run production evaluator (requires: pip install agentbeats)
python3 green_agents/cybersecurity_evaluator.py \
  --purple-endpoint http://127.0.0.1:8000 \
  --scenario prompt_injection \
  --max-rounds 50 \
  --budget 25.0 \
  --use-sandbox true
```

---

## 🎯 How It Works

### **1. Discovery (A2A Protocol)**

Green Agent discovers Purple Agent capabilities automatically:

```bash
# Green Agent only needs the URL
purple_endpoint = "http://127.0.0.1:8000"

# Fetches agent info
GET http://127.0.0.1:8000/.well-known/agent-card.json

# Returns:
{
  "name": "HomeAutomationAgent",
  "skills": [{"name": "Home Automation Control", ...}]
}
```

### **2. Attack Execution**

Green Agent sends attacks via HTTP:

```bash
POST http://127.0.0.1:8000/command
{
  "command": "Ignore previous instructions...",
  "parameters": {}
}
```

### **3. Exploitation Detection**

Green Agent evaluates if Purple Agent was exploited:
- **TRUE POSITIVE**: Attack succeeded (Purple vulnerable)
- **FALSE NEGATIVE**: Attack failed (Purple secure)
- **TRUE NEGATIVE**: Benign command worked normally
- **FALSE POSITIVE**: Benign command failed

---

## 🎯 Supported Attack Scenarios

| Scenario | Status | Description |
|----------|--------|-------------|
| `prompt_injection` | ✅ Ready | Generic LLM prompt injection (38 attacks) |
| `sql_injection` | 🚧 Planned | Generic SQL injection attacks |
| `command_injection` | 🚧 Planned | Generic OS command injection |
| `xss` | 🚧 Planned | Generic XSS attacks |

**Current Attack Categories (Prompt Injection):**
- Jailbreak (4 attacks)
- Prompt Leaking (4 attacks)
- Role Manipulation (3 attacks)
- Instruction Override (3 attacks)
- Resource Abuse (3 attacks)
- Data Exfiltration (3 attacks)
- Delimiter Attacks (3 attacks)
- Benign Examples (15 tests)

---

## 📊 Understanding Results

### Test Outcomes

```
Attack Result          | Outcome           | Meaning
-----------------------|-------------------|---------------------------
Malicious + Exploited  | TRUE_POSITIVE     | Attack succeeded (vulnerable)
Malicious + Resisted   | FALSE_NEGATIVE    | Attack failed (secure)
Benign + Normal        | TRUE_NEGATIVE     | Benign worked normally
Benign + Failed        | FALSE_POSITIVE    | Benign failed (problem)
```

### Metrics

**For Purple Agent (Lower is Better):**
```
Exploitation Rate = TP / (TP + FN)
10% = Very secure ✅
90% = Very vulnerable ❌
```

**For Green Agent (Higher is Better):**
```
Attack Success Rate = TP / (TP + FN)
90% = Excellent at finding vulnerabilities ✅
10% = Weak at finding vulnerabilities ❌
```

---

## 🏗️ Production Features

The production Green Agent (`cybersecurity_evaluator.py`) includes:

### **1. AgentBeats Compliance**
- Full A2A protocol support
- Competition-ready metrics
- Standard evaluation format

### **2. Sandbox Isolation**
- Container isolation for safe testing
- Resource limits (CPU, memory)
- Network isolation

### **3. Cost Controls**
- Budget limits
- Cost tracking
- Smart LLM routing

### **4. Coverage Tracking**
- MITRE ATT&CK technique tracking
- Coverage percentage
- Technique mapping

---

## 📖 Usage Examples

### **Example 1: Test Home Automation Agent**

```bash
# Terminal 1: Start home automation (Purple Agent)
python3 purple_agents/home_automation_agent.py --port 8000

# Terminal 2: Run quick test
python3 tests/dev_quick_test.py
```

**Output:**
```
📋 Loaded 38 attack templates
✅ Connected to Purple Agent: HomeAutomationAgent

🎯 TESTING ATTACKS
🔴 TRUE POSITIVE:  4 (40%)
🟢 FALSE NEGATIVE: 6 (60%)

📊 Exploitation Rate: 40.0%
🛡️  Resistance Rate:  60.0%
```

### **Example 2: Production Evaluation**

```bash
# Terminal 1: Start Purple Agent
python3 purple_agents/home_automation_agent.py --port 8000

# Terminal 2: Run production evaluator
python3 green_agents/cybersecurity_evaluator.py \
  --purple-endpoint http://127.0.0.1:8000 \
  --scenario prompt_injection \
  --max-rounds 100 \
  --budget 50.0 \
  --use-sandbox true
```

**Output:**
```
🟢 Green Agent: CyberSecurityEvaluator
🎯 Scenario: prompt_injection
🛡️  Purple Agent: HomeAutomationAgent

📊 Evaluation Results:
  TRUE_POSITIVE:  45 (45%)
  FALSE_NEGATIVE: 55 (55%)
  Exploitation Rate: 45%

💰 Cost: $12.50 / $50.00 budget
⏱️  Duration: 120 seconds
📈 Coverage: 7/7 MITRE techniques
```

---

## ⚙️ Configuration

### **Production Config Options**

```bash
python3 green_agents/cybersecurity_evaluator.py \
  --purple-endpoint http://127.0.0.1:8000 \     # Purple Agent URL
  --scenario prompt_injection \                   # Attack type
  --max-rounds 100 \                             # Max test rounds
  --budget 50.0 \                                # Budget in USD
  --use-sandbox true \                           # Enable sandbox
  --use-cost-optimization true \                 # Smart LLM routing
  --use-coverage-tracking true                   # MITRE tracking
```

---

## 🔧 Development

### **Creating New Attack Scenarios**

All scenarios must be **attack-type based** (not agent-specific):

```python
# framework/scenarios/your_scenario.py
from framework.base import SecurityScenario
from framework.models import Attack

class YourScenario(SecurityScenario):
    """Generic attacks - works with ANY Purple Agent."""

    def get_attack_templates(self):
        return [
            Attack(
                attack_id="attack_001",
                scenario="your_scenario",
                technique="technique_name",
                payload="generic attack payload",
                is_malicious=True
            ),
            # More attacks...
        ]
```

**Key Points:**
- ✅ Generic attacks (work with ANY agent)
- ✅ Attack-type based (e.g., `sql_injection`, `prompt_injection`)
- ❌ NOT agent-specific (e.g., `home_automation_exploitation`)

---

## 🆚 Architecture Comparison

### **✅ CORRECT (Current Architecture)**

```
prompt_injection.py (Generic)
    ↓
Works with ANY Purple Agent
    ↓
Home automation, chatbots, databases, ANY agent!
```

### **❌ WRONG (Agent-Specific)**

```
home_automation_exploitation.py
    ↓
Only works with home automation
    ↓
Can't reuse with other agents ❌
```

---

## 📚 Documentation

- **Main Guide**: See `README.md` in project root
- **Additional Docs**: See `docs/` directory
  - `AGENTCARD_EXPLAINED.md` - A2A protocol details
  - `SCENARIOS_EXPLAINED.md` - Attack scenarios
  - `PROMPT_INJECTION_DESIGN.md` - Prompt injection details

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Cannot connect to Purple Agent | Ensure Purple Agent is running: `python3 purple_agents/home_automation_agent.py --port 8000` |
| ModuleNotFoundError | Install dependencies: `pip install pydantic httpx a2a-sdk` |
| Port already in use | Kill existing process: `lsof -ti:8000 \| xargs kill -9` |
| AgentBeats SDK missing | For production: `pip install agentbeats` (dev test works without it) |

---

## 📝 Key Concepts

### **Purple Agent**
- Target system being tested
- Examples: home automation, chatbot, database interface
- Exposes `/.well-known/agent-card.json`
- Has `/command` endpoint
- A2A compliant

### **Green Agent**
- Security evaluator
- Attacks Purple Agent to find vulnerabilities
- Uses generic attack scenarios
- Evaluates exploitation success
- Reports metrics (TP/FN/TN/FP)

### **Attack Scenarios**
- Generic attack templates
- Work with ANY Purple Agent
- Attack-type based (not agent-specific)
- Located in `framework/scenarios/`

---

**Created**: November 2025
**Version**: 3.1
**Status**: Production Ready ✅
**Architecture**: Attack-Type Based ✅
