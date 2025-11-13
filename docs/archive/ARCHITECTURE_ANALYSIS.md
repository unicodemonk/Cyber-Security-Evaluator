# Architecture Analysis: What Do We Actually Need?

## Problem Identified

You correctly identified two issues:

1. **`home_automation_exploitation.py` is agent-specific** - Should be attack-type based
2. **`purple_agent_adapter.py` may not be needed** - Adding unnecessary complexity

## Current Architecture Analysis

### What `test.py` Actually Does:

```python
# test.py ONLY uses:
from framework.scenarios.home_automation_exploitation import HomeAutomationExploitationScenario
from framework.models import TestOutcome

# Gets attack templates:
scenario = HomeAutomationExploitationScenario()
attacks = scenario.get_attack_templates()  # ← Only uses this!

# Sends attacks via HTTP:
class PurpleAgentProxy:
    async def send_command(self, command_payload: dict):
        # Direct HTTP POST to /command endpoint
        response = await client.post(f"{self.endpoint}/command", json=command_payload)
        return response.json()

    def evaluate_exploitation(self, command, response):
        # Evaluates if Purple Agent was exploited
        # Based on response indicators
```

**Key Finding:** `test.py` does NOT use:
- ❌ `execute_attack()` method from scenarios
- ❌ `PurpleAgentAdapter`

It only uses scenarios to **get attack templates**, then handles everything else itself.

---

## File Analysis

### 1. `purple_agent_adapter.py` (248 lines)

**Purpose:** Wrapper to handle ANY Purple Agent interface

**Used by:**
- `home_automation_exploitation.py:700` - In `execute_attack()` method
- `prompt_injection.py:894` - In `execute_attack()` method
- `sql_injection.py` - In `execute_attack()` method
- `active_scanning.py` - In `execute_attack()` method

**But:** `test.py` doesn't call `execute_attack()`!

**Verdict: NOT NEEDED for current test flow** ❌

---

### 2. `home_automation_exploitation.py` (680 lines)

**Problems:**
1. ✅ **Agent-specific** - All attacks tailored to home automation
2. ✅ **Not reusable** - Can't test other agents
3. ✅ **Redundant** - `prompt_injection.py` has generic attacks

**Attack breakdown:**
```
Temperature manipulation (5 attacks)     → Generic prompt injection + parameter injection
Water system abuse (4 attacks)           → Generic parameter injection
Command injection (4 attacks)            → Generic command injection
Shopping manipulation (3 attacks)        → Generic parameter injection
Resource exhaustion (3 attacks)          → Generic resource abuse
Data exfiltration (3 attacks)            → Generic prompt injection
Benign commands (10 attacks)             → Generic benign queries
```

**ALL of these are generic attack types!** They're just themed for home automation.

**Verdict: Should use generic `prompt_injection.py` instead** ❌

---

### 3. `prompt_injection.py` (913 lines)

**Advantages:**
1. ✅ **Attack-type based** - Generic prompt injection techniques
2. ✅ **Reusable** - Works with ANY agent
3. ✅ **Comprehensive** - 7 attack categories + benign examples

**Attack categories:**
```
1. Jailbreak              → Works with ANY LLM-based agent
2. Prompt Leaking         → Works with ANY LLM-based agent
3. Role Manipulation      → Works with ANY agent
4. Instruction Override   → Works with ANY agent
5. Resource Abuse         → Works with ANY agent
6. Data Exfiltration      → Works with ANY agent
7. Delimiter Attacks      → Works with ANY LLM-based agent
8. Benign Examples        → Control group
```

**Verdict: This is what we SHOULD use!** ✅

---

## What Should We Do?

### Option 1: Remove Unnecessary Files (RECOMMENDED)

**Remove:**
1. ❌ `framework/purple_agent_adapter.py` - Not used by test.py
2. ❌ `framework/scenarios/home_automation_exploitation.py` - Agent-specific
3. ❌ `framework/scenarios/sql_injection.py` - If not used
4. ❌ `framework/scenarios/active_scanning.py` - If not used

**Keep:**
1. ✅ `framework/scenarios/prompt_injection.py` - Generic, reusable
2. ✅ `test.py` - Main test file
3. ✅ `framework/models.py` - Data models
4. ✅ `framework/base.py` - Base classes (if scenarios use them)

**Update test.py:**
```python
# Change from:
from framework.scenarios.home_automation_exploitation import HomeAutomationExploitationScenario

# To:
from framework.scenarios.prompt_injection import PromptInjectionScenario

# Then:
scenario = PromptInjectionScenario()
attacks = scenario.get_attack_templates()
```

---

### Option 2: Keep Adapter for Future Use (NOT RECOMMENDED)

If we want to keep the adapter for future scenarios that might use `execute_attack()`:

**Keep:**
- `purple_agent_adapter.py` (unused but available for future)
- All scenario files

**Problem:** Adds complexity we don't need right now.

---

## Correct Architecture

### Current (What test.py does):

```
┌─────────────────────────────────────────────────────────┐
│                      test.py                             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Load attack templates from scenario                 │
│     ↓                                                    │
│  2. Send attacks via HTTP (PurpleAgentProxy)            │
│     ↓                                                    │
│  3. Evaluate exploitation (Green Agent logic)           │
│     ↓                                                    │
│  4. Calculate metrics (TP/FN/TN/FP)                     │
│                                                          │
└─────────────────────────────────────────────────────────┘
                      ↓ HTTP
┌─────────────────────────────────────────────────────────┐
│              Purple Agent (Home Automation)              │
│                    (port 8000)                           │
└─────────────────────────────────────────────────────────┘
```

**No adapter needed!** Simple, direct, clear.

---

### What We Don't Need:

```
❌ PurpleAgentAdapter
    ↓
    Used only by scenario.execute_attack()
    ↓
    But test.py doesn't call execute_attack()!
```

---

## Recommendation

**Clean up to match actual usage:**

1. **Remove `purple_agent_adapter.py`** - Not used
2. **Remove `home_automation_exploitation.py`** - Agent-specific
3. **Use `prompt_injection.py`** - Generic attack-type based
4. **Update `test.py`** - Import PromptInjectionScenario instead
5. **Test with generic attacks** - Will work with ANY agent

This gives us:
- ✅ Attack-type based scenarios (not agent-specific)
- ✅ Simpler architecture (no unused adapter)
- ✅ Reusable with ANY A2A-compliant agent
- ✅ Clear separation: Scenario = attack templates, test.py = execution

---

## Files to Remove

```bash
# Remove unnecessary files:
rm framework/purple_agent_adapter.py
rm framework/scenarios/home_automation_exploitation.py
rm framework/scenarios/sql_injection.py      # If not needed
rm framework/scenarios/active_scanning.py    # If not needed
```

---

## Summary

You were 100% correct:

1. ✅ **Scenarios should be attack-type based** (prompt injection, SQL injection, etc.)
   - NOT agent-specific (home_automation_exploitation)

2. ✅ **`purple_agent_adapter.py` is not needed**
   - test.py doesn't use it
   - Adds complexity without benefit

The correct flow is:
```
Generic Attack Scenario (prompt_injection.py)
    ↓
  Provides attack templates
    ↓
test.py sends them via HTTP
    ↓
Purple Agent (ANY agent!)
```

Simple, clean, reusable! 🎯
