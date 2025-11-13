# Production Plan - What Do We Need?

## Current State

### test.py (Simple Demo)
- **Purpose:** Quick demonstration script
- **Size:** 343 lines
- **Features:**
  - Loads attack templates
  - Sends attacks to Purple Agent
  - Evaluates results
  - Prints summary
- **Good for:** Development, quick testing
- **NOT good for:** Production, competition

### green_agents/cybersecurity_evaluator.py (Production Green Agent)
- **Purpose:** Full production Green Agent
- **Size:** 499 lines
- **Features:**
  - AgentBeats GreenAgent compliance
  - Multi-scenario support
  - Cost optimization
  - Sandbox isolation
  - Coverage tracking (MITRE ATT&CK)
  - Budget controls
  - A2A protocol
- **Good for:** Production, competition
- **Problem:** ❌ Imports deleted scenarios (SQLInjectionScenario, ActiveScanningScenario)

---

## Answer: Do We Need test.py for Production?

### Short Answer: NO ❌

`test.py` is a **development/demo script**, not for production.

### For Production, We Need:

1. **✅ Green Agent** (`green_agents/cybersecurity_evaluator.py`)
   - Full AgentBeats compliance
   - Production features (sandbox, cost control, etc.)
   - Runs as a service

2. **✅ Purple Agent** (`purple_agents/home_automation_agent.py`)
   - Already production-ready
   - A2A compliant
   - Runs as a service

3. **⚠️ Green Agent Needs Fixing**
   - Currently imports deleted scenarios
   - Needs to be updated to use PromptInjectionScenario only

---

## What We Should Do

### Option 1: Fix Green Agent (RECOMMENDED) ✅

Update `green_agents/cybersecurity_evaluator.py`:
```python
# Remove:
from framework.scenarios import SQLInjectionScenario, PromptInjectionScenario, ActiveScanningScenario

# Replace with:
from framework.scenarios import PromptInjectionScenario

# Update scenario mapping:
scenarios = {
    'prompt_injection': PromptInjectionScenario,
    # Add more as we create them:
    # 'sql_injection': SQLInjectionScenario,  # TODO: Create generic version
    # 'command_injection': CommandInjectionScenario,  # TODO: Create
}
```

### Option 2: Keep test.py for Quick Development ✅

Rename and clarify its purpose:
```bash
mv test.py dev_test.py
# Or:
mv test.py examples/quick_test.py
```

Add clear documentation:
```python
"""
DEVELOPMENT ONLY - Quick Test Script

This is a simple script for quick development testing.
For production/competition, use green_agents/cybersecurity_evaluator.py

Usage:
  python3 dev_test.py  # Quick development test
"""
```

---

## Production Architecture

### Development (test.py):
```
┌─────────────────────────┐
│       test.py           │  ← Simple script
│  (343 lines, no frills) │
└─────────────────────────┘
           ↓ HTTP
┌─────────────────────────┐
│     Purple Agent        │
└─────────────────────────┘
```

### Production (Green Agent):
```
┌──────────────────────────────────────┐
│   CyberSecurityEvaluator             │
│   (green_agents/cybersecurity_evaluator.py)
│                                      │
│   ✅ AgentBeats compliance           │
│   ✅ Multi-scenario support          │
│   ✅ Cost optimization               │
│   ✅ Sandbox isolation               │
│   ✅ Coverage tracking               │
│   ✅ Budget controls                 │
│   ✅ A2A protocol                    │
└──────────────────────────────────────┘
           ↓ A2A Protocol
┌──────────────────────────────────────┐
│         Purple Agent                 │
│   (Any A2A-compliant agent)          │
└──────────────────────────────────────┘
```

---

## Comparison

| Feature | test.py | Green Agent |
|---------|---------|-------------|
| **Purpose** | Quick demo | Production |
| **AgentBeats** | ❌ No | ✅ Yes |
| **Sandbox** | ❌ No | ✅ Yes |
| **Cost Control** | ❌ No | ✅ Yes |
| **Coverage Tracking** | ❌ No | ✅ Yes (MITRE) |
| **Multi-Scenario** | ❌ No | ✅ Yes |
| **Budget Limits** | ❌ No | ✅ Yes |
| **Production Safe** | ❌ No | ✅ Yes |
| **Competition Ready** | ❌ No | ✅ Yes |

---

## What test.py is Missing for Production

1. **No AgentBeats Integration**
   - Can't participate in AgentBeats competition
   - Doesn't follow GreenAgent interface

2. **No Safety Features**
   - No sandbox isolation
   - No cost controls
   - No budget limits
   - Purple Agent could execute dangerous code

3. **No Advanced Features**
   - No coverage tracking (MITRE ATT&CK)
   - No cost optimization
   - No adaptive testing
   - No mutation/evolution

4. **Not Deployable as Service**
   - Just a script, not a service
   - No API endpoint
   - No task management

---

## Recommendation

### For Development:
```bash
# Keep test.py for quick testing
python3 test.py
# ✅ Fast, simple, good for debugging
```

### For Production/Competition:
```bash
# Use Green Agent
python3 green_agents/cybersecurity_evaluator.py \
  --purple-endpoint http://127.0.0.1:8000 \
  --scenario prompt_injection \
  --max-rounds 100 \
  --budget 50.0

# ✅ Production-safe, competition-ready
```

### Priority Actions:

1. **Fix Green Agent** ✅
   - Update imports (remove deleted scenarios)
   - Test with PromptInjectionScenario
   - Verify it runs

2. **Clarify test.py Purpose** ✅
   - Rename to `dev_test.py` or move to `examples/`
   - Add clear "DEVELOPMENT ONLY" warning
   - Document that Green Agent is for production

3. **Create More Scenarios** (Future)
   - Generic SQL injection scenario
   - Generic command injection scenario
   - Generic XSS scenario
   - All attack-type based (not agent-specific)

---

## How to Run Production Green Agent

### Step 1: Fix Imports
```python
# In green_agents/cybersecurity_evaluator.py
from framework.scenarios import PromptInjectionScenario

scenarios = {
    'prompt_injection': PromptInjectionScenario,
}
```

### Step 2: Start Purple Agent
```bash
python3 purple_agents/home_automation_agent.py --port 8000
```

### Step 3: Run Green Agent
```bash
python3 green_agents/cybersecurity_evaluator.py \
  --purple-endpoint http://127.0.0.1:8000 \
  --scenario prompt_injection \
  --max-rounds 50 \
  --budget 25.0 \
  --use-sandbox true
```

### Output:
```
🟢 Green Agent: CyberSecurityEvaluator
🎯 Scenario: prompt_injection
🛡️  Purple Agent: HomeAutomationAgent

📊 Evaluation Results:
  TRUE_POSITIVE:  25 (50%)
  FALSE_NEGATIVE: 25 (50%)
  Exploitation Rate: 50%

💰 Cost: $2.50 / $25.00 budget
⏱️  Duration: 45 seconds
📈 Coverage: 7/7 techniques
```

---

## Summary

### test.py:
- ✅ Keep for development
- ❌ NOT for production
- ✅ Useful for quick debugging
- ⚠️  Rename to clarify it's dev-only

### Green Agent (cybersecurity_evaluator.py):
- ✅ Production-ready
- ✅ Competition-ready
- ⚠️  Needs fixing (update imports)
- ✅ Has all production features

### Next Steps:
1. Fix Green Agent imports
2. Test Green Agent with PromptInjectionScenario
3. Rename test.py to dev_test.py (or move to examples/)
4. Document the difference clearly

---

**Answer:** No, `test.py` is NOT needed for production. It's a development script. Use `green_agents/cybersecurity_evaluator.py` for production/competition.
