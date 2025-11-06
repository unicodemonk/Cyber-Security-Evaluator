# Side-by-Side Comparison: Debate vs SQL Injection

## Quick Answer: Yes, `scenarios/debate/` is a sample app!

It demonstrates the AgentBeats framework with a simple debate orchestration scenario. Your SQL Injection implementation follows the same pattern but adds complexity.

---

## Visual Comparison

### Debate Scenario (Sample)

```
┌─────────────────────────────────────────────────────────────┐
│                     USER/CLIENT                             │
│                                                             │
│  "Have Pro and Con debate AI regulation for 3 rounds"      │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ POST /tasks
                         ↓ 
┌─────────────────────────────────────────────────────────────┐
│             GREEN AGENT: Debate Judge                       │
│             (port 9009)                                     │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │ run_eval()                                         │   │
│  │  1. Orchestrate debate rounds                      │   │
│  │  2. Collect arguments from both sides              │   │
│  │  3. Judge using LLM (Gemini)                       │   │
│  │  4. Return winner + scores                         │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
          │                              │
          │ HTTP                         │ HTTP
          ↓                              ↓
┌───────────────────────┐      ┌───────────────────────┐
│  PURPLE AGENT:        │      │  PURPLE AGENT:        │
│  Pro Debater          │      │  Con Debater          │
│  (port 9019)          │      │  (port 9018)          │
│                       │      │                       │
│  Uses: Gemini LLM     │      │  Uses: Gemini LLM     │
│  Role: Argue FOR      │      │  Role: Argue AGAINST  │
└───────────────────────┘      └───────────────────────┘

RESULT:
{
  "winner": "pro_debater",
  "pro_score": 3.55,
  "con_score": 3.18,
  "reason": "Pro had clearer arguments..."
}
```

---

### SQL Injection Scenario (Your Implementation)

```
┌─────────────────────────────────────────────────────────────┐
│                     USER/CLIENT                             │
│                                                             │
│  "Evaluate SQL detector with 100 tests in adaptive mode"   │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ POST /tasks
                         ↓
┌─────────────────────────────────────────────────────────────┐
│         GREEN AGENT: SQL Injection Judge                    │
│         (port 9010)                                         │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │ run_eval()                                         │   │
│  │  1. Load 27 code samples (dataset)                 │   │
│  │  2. Adaptive Planner decides test allocation       │   │
│  │  3. Send code samples to Purple Agent              │   │
│  │  4. Compare responses to ground truth              │   │
│  │  5. Calculate F1, Precision, Recall                │   │
│  │  6. Identify weak categories                       │   │
│  │  7. Re-allocate tests to weak areas                │   │
│  │  8. Repeat until budget exhausted                  │   │
│  │  9. Return comprehensive metrics                   │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  Components:                                                │
│  • DatasetManager     (loads samples)                       │
│  • ScoringEngine      (calculates metrics)                  │
│  • AdaptivePlanner    (autonomous decisions)                │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ HTTP (many calls)
                         ↓
           ┌───────────────────────────┐
           │  PURPLE AGENT:            │
           │  SQL Injection Detector   │
           │  (port 8000)              │
           │                           │
           │  Uses: Pattern matching   │
           │  Role: Detect SQL inject  │
           └───────────────────────────┘

RESULT:
{
  "success": true,
  "metrics": {
    "f1_score": 0.769,
    "precision": 1.0,
    "recall": 0.625,
    "confusion_matrix": {TP: 5, TN: 2, FP: 0, FN: 3}
  },
  "weak_categories": ["stored_procedure", "orm_injection", ...]
}
```

---

## Feature Comparison

| Feature | Debate (Sample) | SQL Injection (Your Code) |
|---------|-----------------|---------------------------|
| **Purpose** | Demonstrate framework | Production-ready evaluator |
| **Purple Agents** | 2 (Pro, Con) | 1 (Detector) |
| **Interaction** | Sequential conversation | Independent batch tests |
| **Evaluation** | LLM judges subjectively | Quantitative metrics |
| **Test Strategy** | Fixed (3 rounds) | Adaptive (autonomous) |
| **Dataset** | None (generated on-fly) | 27 pre-loaded samples |
| **Metrics** | Scores 0-1 per criterion | F1, Precision, Recall, etc. |
| **Decision Making** | None | Adaptive Planner |
| **Code Complexity** | ~200 lines | ~3,500 lines |
| **Use Case** | Demo/Tutorial | AgentBeats Phase 1 |

---

## Code Flow Comparison

### Debate Flow

```
1. Client submits task
   ↓
2. DebateJudge.run_eval() starts
   ↓
3. orchestrate_debate():
   ├─ Call Pro: "Opening argument"
   ├─ Call Con: "Opening argument + Pro's response"
   ├─ Call Pro: "Rebuttal to Con"
   ├─ Call Con: "Rebuttal to Pro"
   └─ Repeat for N rounds
   ↓
4. judge_debate():
   ├─ Combine all arguments into text
   ├─ Send to Gemini with judging prompt
   └─ Get structured scores + winner
   ↓
5. Return results to client
```

**Time:** ~30 seconds for 3 rounds
**Calls to Purple Agents:** 6 (3 rounds × 2 agents)

---

### SQL Injection Flow

```
1. Client submits task
   ↓
2. SQLInjectionJudge.run_eval() starts
   ↓
3. DatasetManager.load_datasets()
   ├─ Load vulnerable samples (12)
   ├─ Load secure samples (15)
   └─ Total: 27 samples
   ↓
4. AdaptivePlanner.plan_round():
   ├─ Phase: EXPLORATION
   ├─ Decision: Sample 20 diverse tests
   └─ Test allocation: Balanced across categories
   ↓
5. For each sample (Round 1):
   ├─ Call Purple Agent with code
   ├─ Get response (vulnerable: yes/no)
   ├─ Compare to ground truth
   └─ Record outcome (TP/TN/FP/FN)
   ↓
6. ScoringEngine.calculate_metrics():
   ├─ Confusion matrix
   ├─ F1, Precision, Recall
   └─ Per-category breakdown
   ↓
7. AdaptivePlanner.analyze_round():
   ├─ Identify weak categories (F1 < 0.6)
   ├─ Decision: Allocate 60% to weak areas
   └─ Phase transition: EXPLOITATION
   ↓
8. Repeat steps 4-7 until:
   ├─ Test budget exhausted
   ├─ Performance stable
   └─ Or all categories strong
   ↓
9. Return comprehensive results
```

**Time:** ~20-60 seconds depending on budget
**Calls to Purple Agent:** 20-100+ (depends on test_budget)

---

## Code Structure Comparison

### Debate

```python
# debate_judge.py

class DebateJudge(GreenAgent):
    def __init__(self):
        self._client = genai.Client()  # For judging
        self._tool_provider = ToolProvider()  # For calling Purple Agents

    async def run_eval(self, req, updater):
        # 1. Orchestrate debate
        debate = await self.orchestrate_debate(...)

        # 2. Judge debate
        eval = await self.judge_debate(debate_text)

        # 3. Return winner
        return EvalResult(winner=eval.winner, ...)

    async def orchestrate_debate(self, participants, topic, rounds):
        # Call Purple Agents back and forth
        for round in range(rounds):
            pro_response = await talk_to_agent(pro_agent, prompt)
            con_response = await talk_to_agent(con_agent, prompt)

    async def judge_debate(self, topic, debate_text):
        # Use Gemini to judge
        response = self._client.models.generate_content(...)
        return response.parsed
```

**Key Point:** Simple orchestration + LLM-based judging

---

### SQL Injection

```python
# sql_injection_judge.py

class SQLInjectionJudge(GreenAgent):
    def __init__(self, dataset_root):
        self.dataset_manager = DatasetManager(dataset_root)  # Load samples
        self.scoring_engine = ScoringEngine()  # Calculate metrics
        self.adaptive_planner = AdaptiveTestPlanner()  # Autonomous decisions

    async def run_eval(self, req, updater):
        # 1. Load configuration
        mode = req.config.get("mode", "fixed")
        test_budget = req.config.get("test_budget", 100)

        # 2. Choose strategy
        if mode == "adaptive":
            result = await self._run_adaptive_evaluation(...)
        else:
            result = await self._run_fixed_evaluation(...)

        # 3. Return comprehensive metrics
        return EvalResponse(success=True, metrics=result, ...)

    async def _run_adaptive_evaluation(self, purple_agent_url, config):
        # Multi-round adaptive testing
        for round_num in range(max_rounds):
            # a. Planner makes decision
            plan = self.adaptive_planner.plan_round(round_num, ...)

            # b. Execute tests
            results = await self._execute_test_batch(samples, purple_agent_url)

            # c. Calculate metrics
            metrics = self.scoring_engine.calculate_metrics(results)

            # d. Analyze and adapt
            insights = self.adaptive_planner.analyze_round(metrics, results)

            # e. Check termination
            if insights.should_terminate:
                break

        return final_metrics

    async def _execute_test_batch(self, samples, purple_agent_url):
        # Call Purple Agent for each sample
        async with httpx.AsyncClient() as client:
            for sample in samples:
                response = await client.post(f"{purple_agent_url}/detect", ...)
                result = self._evaluate_response(sample, response)
                results.append(result)
        return results
```

**Key Point:** Complex multi-component system with autonomous decision-making

---

## Information Passing

### Debate

```
Client → Green Agent:
{
  "participants": {
    "pro_debater": "http://127.0.0.1:9019",
    "con_debater": "http://127.0.0.1:9018"
  },
  "config": {
    "topic": "Should AI be regulated?",
    "num_rounds": 3
  }
}

Green Agent → Pro Debater:
{
  "input": {
    "text": "Debate Topic: Should AI be regulated? Present opening."
  }
}

Pro Debater → Green Agent:
{
  "output": {
    "text": "AI must be regulated because..."
  }
}

Green Agent → Con Debater:
{
  "input": {
    "text": "Topic: AI regulation. Opponent said: [Pro's arg]. Your turn."
  }
}

Con Debater → Green Agent:
{
  "output": {
    "text": "I disagree because..."
  }
}

[Repeat for N rounds]

Green Agent → Gemini (for judging):
{
  "system": "You are a debate judge...",
  "user": "Evaluate this debate: [full transcript]"
}

Gemini → Green Agent:
{
  "pro_score": 3.55,
  "con_score": 3.18,
  "winner": "pro_debater",
  "reason": "..."
}

Green Agent → Client:
{
  "winner": "pro_debater",
  "detail": {...}
}
```

---

### SQL Injection

```
Client → Green Agent:
{
  "purple_agent_endpoint": "http://127.0.0.1:8000",
  "config": {
    "mode": "adaptive",
    "test_budget": 100,
    "weak_threshold": 0.6
  }
}

[Green Agent loads 27 samples from files]

Green Agent → Purple Agent (Sample 1):
{
  "test_case_id": "python_classic_001",
  "code": "query = f'SELECT * FROM users WHERE id={user_id}'",
  "language": "python",
  "category": "classic_sqli"
}

Purple Agent → Green Agent:
{
  "is_vulnerable": true,
  "confidence": 0.95,
  "explanation": "F-string SQL interpolation detected"
}

[Green Agent compares: ground_truth=True, predicted=True → TRUE_POSITIVE]

[Repeat for all samples in round]

[Green Agent calculates metrics internally]

Green Agent (Adaptive Planner decides):
{
  "weak_categories": ["stored_procedure", "orm_injection"],
  "decision": "Allocate 60% of next round to weak categories",
  "phase": "EXPLOITATION"
}

[Next round focuses on weak areas]

Green Agent → Client (after all rounds):
{
  "success": true,
  "metrics": {
    "f1_score": 0.769,
    "precision": 1.0,
    "recall": 0.625,
    "confusion_matrix": {TP: 5, TN: 2, FP: 0, FN: 3}
  },
  "category_metrics": [...],
  "adaptive_insights": {
    "rounds_completed": 5,
    "weak_categories": [...],
    "total_tests_executed": 97
  }
}
```

---

## Startup Commands

### Debate

```bash
# Terminal 1: Pro Debater
python scenarios/debate/debater.py --port 9019

# Terminal 2: Con Debater
python scenarios/debate/debater.py --port 9018

# Terminal 3: Judge
python scenarios/debate/debate_judge.py --port 9009

# Terminal 4: Submit task
curl -X POST http://127.0.0.1:9009/tasks -d '{...}'
```

---

### SQL Injection

```bash
# Terminal 1: Purple Agent (Detector)
python purple_agents/baseline/sql_detector.py --port 8000

# Terminal 2: Green Agent (Judge)
python scenarios/security/sql_injection_judge.py --port 9010 \
  --dataset-root datasets/sql_injection

# Terminal 3: Submit evaluation
python start_evaluation.py

# Or use curl:
curl -X POST http://127.0.0.1:9010/tasks -d '{...}'
```

---

## Key Takeaways

1. **Both use the same architectural pattern**
   - Green Agent orchestrates
   - Purple Agent(s) perform tasks
   - A2A protocol for communication

2. **Debate is simpler (tutorial/demo)**
   - Interactive conversation
   - LLM-based judging
   - ~200 lines

3. **SQL Injection is production-ready**
   - Batch testing
   - Quantitative metrics
   - Adaptive strategy
   - ~3,500 lines

4. **Your code follows the sample pattern but adds:**
   - Dataset management
   - Comprehensive metrics
   - Autonomous decision-making
   - Multi-round adaptive testing

5. **The debate scenario is your blueprint!**
   - Shows how to structure Green/Purple agents
   - Demonstrates A2A protocol usage
   - Provides working example to learn from

---

## Summary

✅ **Yes, `scenarios/debate/` is a sample application**

✅ **It demonstrates the AgentBeats framework**

✅ **Your SQL Injection implementation follows the same pattern**

✅ **But your implementation is more sophisticated with adaptive testing**

You can learn from the debate code to understand the framework, then see how your SQL injection implementation extends those concepts!
