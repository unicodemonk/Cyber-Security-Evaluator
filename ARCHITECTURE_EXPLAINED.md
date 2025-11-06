# Complete Architecture Explanation - AgentBeats Framework

## Overview

There are **two scenario applications** in this project:

1. **`scenarios/debate/`** - Sample application (provided by AgentBeats)
   - Demonstrates debate orchestration between Pro and Con debaters
   - Shows how to build Green Agent evaluators

2. **`scenarios/security/`** - Your implementation (what we built)
   - SQL Injection Detection Evaluator
   - Tests Purple Agents (security detectors)
   - Based on the debate sample pattern

---

## 🎭 Sample App: Debate Scenario

### What It Does

Orchestrates a structured debate between two AI agents (Pro and Con) on a topic, then judges who won.

### Components

```
scenarios/debate/
├── scenario.toml              # Configuration file
├── debate_judge.py            # Green Agent (orchestrator + judge)
├── debate_judge_common.py     # Shared models & agent card
├── debater.py                 # Purple Agent (debaters)
└── adk_debate_judge.py        # Alternative implementation
```

---

## 📊 Architecture Pattern (Used by Both Scenarios)

```
┌─────────────────────────────────────────────────────────────────┐
│                        AGENTBEATS FRAMEWORK                     │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    GREEN AGENT (Judge)                    │ │
│  │                                                           │ │
│  │  • Orchestrates evaluation                               │ │
│  │  • Calls Purple Agents                                   │ │
│  │  • Collects results                                      │ │
│  │  • Calculates metrics/scores                             │ │
│  │  • Makes autonomous decisions                            │ │
│  │                                                           │ │
│  │  Implements A2A Protocol:                                │ │
│  │    - GET /card         (agent card)                      │ │
│  │    - POST /tasks       (submit evaluation)               │ │
│  │    - GET /tasks/{id}   (check status)                    │ │
│  └───────────────────────────────────────────────────────────┘ │
│                              │                                  │
│                              │ Calls via HTTP                   │
│                              ↓                                  │
│  ┌─────────────────┐    ┌─────────────────┐                   │
│  │ PURPLE AGENT 1  │    │ PURPLE AGENT 2  │                   │
│  │                 │    │                 │                   │
│  │ • Pro Debater   │    │ • Con Debater   │                   │
│  │   (or)          │    │   (or)          │                   │
│  │ • SQL Detector  │    │                 │                   │
│  └─────────────────┘    └─────────────────┘                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Complete Flow: How Everything Works

### Phase 1: Startup

#### Step 1: Start Purple Agents (Participants)

**For Debate:**
```bash
# Terminal 1: Pro Debater
python scenarios/debate/debater.py --host 127.0.0.1 --port 9019

# Terminal 2: Con Debater
python scenarios/debate/debater.py --host 127.0.0.1 --port 9018
```

**What happens in `debater.py`:**

```python
# 1. Create an Agent using Google ADK
root_agent = Agent(
    name="debater",
    model="gemini-2.0-flash",
    description="Participates in a debate.",
    instruction="You are a professional debater.",
)

# 2. Create Agent Card (A2A protocol)
agent_card = AgentCard(
    name="debater",
    url='http://127.0.0.1:9019/',
    capabilities=AgentCapabilities(streaming=True),
)

# 3. Convert to A2A-compliant server
a2a_app = to_a2a(root_agent, agent_card=agent_card)

# 4. Start HTTP server
uvicorn.run(a2a_app, host="127.0.0.1", port=9019)
```

**Result:** Purple Agents are now running and waiting for prompts via A2A protocol.

---

#### Step 2: Start Green Agent (Judge/Orchestrator)

**For Debate:**
```bash
# Terminal 3: Judge
python scenarios/debate/debate_judge.py --host 127.0.0.1 --port 9009
```

**What happens in `debate_judge.py::main()`:**

```python
async def main():
    # 1. Create the Green Agent
    agent = DebateJudge()

    # 2. Wrap in GreenExecutor (handles A2A protocol)
    executor = GreenExecutor(agent)

    # 3. Create agent card describing capabilities
    agent_card = debate_judge_agent_card("DebateJudge", agent_url)

    # 4. Create request handler with task storage
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),  # Tracks tasks
    )

    # 5. Create A2A server application
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    # 6. Start HTTP server
    uvicorn_config = uvicorn.Config(server.build(), host="127.0.0.1", port=9009)
    uvicorn_server = uvicorn.Server(uvicorn_config)
    await uvicorn_server.serve()
```

**Result:** Green Agent is running, exposing A2A endpoints:
- `GET /card` - Agent capabilities
- `POST /tasks` - Submit evaluation task
- `GET /tasks/{id}` - Check status

---

### Phase 2: Triggering an Evaluation

Someone (user, orchestrator, or another system) submits a task to the Green Agent:

```bash
curl -X POST http://127.0.0.1:9009/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "participants": {
        "pro_debater": "http://127.0.0.1:9019",
        "con_debater": "http://127.0.0.1:9018"
      },
      "config": {
        "topic": "Should AI be regulated?",
        "num_rounds": 3
      }
    }
  }'
```

**Response:**
```json
{
  "id": "task_abc123",
  "status": "pending"
}
```

---

### Phase 3: Execution Inside Green Agent

The A2A server receives the POST request and triggers the Green Agent:

```python
# In DebateJudge class:

async def run_eval(self, req: EvalRequest, updater: TaskUpdater) -> None:
    # 1. Extract configuration
    participants = req.participants  # {"pro_debater": "http://...", ...}
    topic = req.config["topic"]
    num_rounds = req.config["num_rounds"]

    # 2. Orchestrate the debate
    debate = await self.orchestrate_debate(participants, topic, num_rounds, updater)

    # 3. Judge the debate
    debate_eval = await self.judge_debate(topic, debate_text)

    # 4. Return results
    result = EvalResult(winner=debate_eval.winner, detail=debate_eval.model_dump())
    await updater.add_artifact(parts=[...], name="Result")
```

---

### Phase 4: Orchestrating the Debate

**The `orchestrate_debate()` method:**

```python
async def orchestrate_debate(self, participants, topic, num_rounds, updater):
    debate = {"pro_debater": [], "con_debater": []}

    # Helper function to call a Purple Agent
    async def turn(role: str, prompt: str) -> str:
        # Call Purple Agent via HTTP
        response = await self._tool_provider.talk_to_agent(
            prompt,
            str(participants[role]),  # URL of Purple Agent
            new_conversation=False
        )

        # Store response
        debate[role].append(response)

        # Update task status (visible to client polling)
        await updater.update_status(
            TaskState.working,
            new_agent_text_message(f"{role}: {response}")
        )

        return response

    # Round 1: Opening arguments
    pro_response = await turn("pro_debater", f"Debate Topic: {topic}. Present your opening argument.")
    con_response = await turn("con_debater", f"Debate Topic: {topic}. Your opponent said: {pro_response}. Present your opening argument.")

    # Rounds 2-N: Rebuttals
    for _ in range(num_rounds - 1):
        pro_response = await turn("pro_debater", f"Your opponent said: {con_response}. Present your next argument.")
        con_response = await turn("con_debater", f"Your opponent said: {pro_response}. Present your next argument.")

    return debate
```

**What's happening:**
1. Green Agent sends HTTP POST to `http://127.0.0.1:9019/tasks` with prompt
2. Pro Debater (Purple Agent) generates response using Gemini
3. Green Agent receives response
4. Green Agent sends HTTP POST to `http://127.0.0.1:9018/tasks` with prompt including Pro's response
5. Con Debater generates response
6. Repeat for N rounds

---

### Phase 5: Judging/Evaluation

```python
async def judge_debate(self, topic: str, debate_text: str) -> DebateEval:
    system_prompt = """
    You are an experienced debate judge. Evaluate based on:
    1. Emotional Appeal (0-1)
    2. Clarity of Argument (0-1)
    3. Logical Arrangement (0-1)
    4. Relevance to Topic (0-1)

    Provide scores for Pro and Con, and declare a winner.
    """

    user_prompt = f"Evaluate: {topic}\n\nDebate:\n{debate_text}"

    # Use Gemini to judge
    response = self._client.models.generate_content(
        model="gemini-2.5-flash",
        config=genai.types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=DebateEval,  # Structured output
        ),
        contents=user_prompt,
    )

    return response.parsed  # Returns DebateEval object
```

**DebateEval Model:**
```python
class DebaterScore(BaseModel):
    emotional_appeal: float
    argument_clarity: float
    argument_arrangement: float
    relevance_to_topic: float
    total_score: float

class DebateEval(BaseModel):
    pro_debater: DebaterScore
    con_debater: DebaterScore
    winner: Literal["pro_debater", "con_debater"]
    reason: str
```

---

### Phase 6: Returning Results

```python
# In run_eval():
result = EvalResult(
    winner=debate_eval.winner,      # "pro_debater" or "con_debater"
    detail=debate_eval.model_dump()  # Full scoring breakdown
)

# Add as artifact (returned to task poller)
await updater.add_artifact(
    parts=[
        Part(root=TextPart(text=debate_eval.reason)),
        Part(root=TextPart(text=result.model_dump_json())),
    ],
    name="Result",
)
```

**Task state transitions:**
```
pending → working → completed
```

---

### Phase 7: Client Gets Results

Client polls for task completion:

```bash
curl http://127.0.0.1:9009/tasks/task_abc123
```

**Response when completed:**
```json
{
  "id": "task_abc123",
  "status": "completed",
  "output": {
    "winner": "pro_debater",
    "detail": {
      "pro_debater": {
        "emotional_appeal": 0.85,
        "argument_clarity": 0.90,
        "argument_arrangement": 0.88,
        "relevance_to_topic": 0.92,
        "total_score": 3.55
      },
      "con_debater": {
        "emotional_appeal": 0.75,
        "argument_clarity": 0.80,
        "argument_arrangement": 0.78,
        "relevance_to_topic": 0.85,
        "total_score": 3.18
      },
      "reason": "Pro debater presented more compelling arguments..."
    }
  },
  "artifacts": [...]
}
```

---

## 🔐 Your Implementation: SQL Injection Detection

### Similarities with Debate

Your `scenarios/security/sql_injection_judge.py` follows the **same pattern**:

| Debate | SQL Injection | Purpose |
|--------|---------------|---------|
| `DebateJudge` | `SQLInjectionJudge` | Green Agent class |
| `orchestrate_debate()` | `evaluate_detector()` | Main orchestration |
| `judge_debate()` | `calculate_metrics()` | Evaluation logic |
| Pro/Con Debaters | Purple Agent (SQL Detector) | Participants being evaluated |
| Debate topic | Code samples | Test inputs |
| Winner + scores | F1/Precision/Recall | Evaluation output |

### Key Differences

**Debate:**
- **Interactive**: Purple Agents respond to each other
- **Qualitative**: Judged by LLM on subjective criteria
- **Multi-round**: Conversation between agents

**SQL Injection:**
- **Non-interactive**: Purple Agent just analyzes code
- **Quantitative**: Metrics calculated from ground truth
- **Batch testing**: Many independent tests
- **Adaptive**: Autonomous decision-making on test allocation

---

## 🔄 Data Flow in SQL Injection Scenario

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Client submits task to Green Agent                          │
│    POST /tasks                                                  │
│    {                                                            │
│      "purple_agent_endpoint": "http://127.0.0.1:8000",         │
│      "config": {"mode": "adaptive", "test_budget": 100}        │
│    }                                                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. Green Agent (SQLInjectionJudge)                             │
│    • Loads dataset (27 code samples)                           │
│    • Creates adaptive planner                                  │
│    • Starts evaluation rounds                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. Adaptive Planner makes decision                             │
│    • Phase: EXPLORATION                                        │
│    • Sample 20 diverse tests                                   │
│    • Decision: "Test these categories"                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. For each code sample:                                       │
│    ┌─────────────────────────────────────────┐                │
│    │ a. Send to Purple Agent                 │                │
│    │    POST http://127.0.0.1:8000/detect    │                │
│    │    {                                     │                │
│    │      "code": "query = f'SELECT...'",     │                │
│    │      "language": "python",               │                │
│    │      "category": "classic_sqli"          │                │
│    │    }                                     │                │
│    └─────────────────────────────────────────┘                │
│                    ↓                                            │
│    ┌─────────────────────────────────────────┐                │
│    │ b. Purple Agent responds                │                │
│    │    {                                     │                │
│    │      "is_vulnerable": true,              │                │
│    │      "confidence": 0.95                  │                │
│    │    }                                     │                │
│    └─────────────────────────────────────────┘                │
│                    ↓                                            │
│    ┌─────────────────────────────────────────┐                │
│    │ c. Compare to ground truth              │                │
│    │    Ground truth: VULNERABLE              │                │
│    │    Predicted: VULNERABLE                 │                │
│    │    Outcome: TRUE_POSITIVE ✓              │                │
│    └─────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. Scoring Engine calculates metrics                           │
│    • TP: 5, TN: 2, FP: 0, FN: 3                                │
│    • F1: 0.769, Precision: 1.0, Recall: 0.625                  │
│    • Per-category breakdown                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. Adaptive Planner analyzes results                           │
│    • Identifies weak categories (F1 < 0.6):                    │
│      - stored_procedure                                        │
│      - orm_injection                                           │
│      - second_order                                            │
│    • Decision: "Allocate 60% of next tests to weak areas"     │
│    • Phase transition: EXPLORATION → EXPLOITATION              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. Repeat rounds until:                                        │
│    • Test budget exhausted                                     │
│    • Performance stable                                        │
│    • All categories performing well                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. Return final results                                        │
│    {                                                            │
│      "success": true,                                           │
│      "metrics": {...},                                          │
│      "category_metrics": [...],                                 │
│      "adaptive_insights": {                                     │
│        "rounds_completed": 5,                                   │
│        "weak_categories": [...]                                 │
│      }                                                           │
│    }                                                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Code Structure Comparison

### Debate (Sample)

```
scenarios/debate/
├── debater.py                    # Purple Agent (simple ADK wrapper)
├── debate_judge.py               # Green Agent (orchestrator + judge)
├── debate_judge_common.py        # Models + agent card
└── scenario.toml                 # Configuration

Components:
• 3 agents (1 judge, 2 debaters)
• ~200 lines of code
• LLM-based judging
• Interactive conversation
```

### SQL Injection (Your Implementation)

```
scenarios/security/
├── models.py                     # All Pydantic models (~600 lines)
├── dataset_manager.py            # Dataset loading & sampling (~550 lines)
├── scoring_engine.py             # Metrics calculation (~500 lines)
├── adaptive_planner.py           # Autonomous decision-making (~650 lines)
├── sql_injection_judge.py        # Green Agent (~850 lines)
├── agent_card.py                 # Agent card definition
└── config.yaml                   # Configuration

Components:
• 2 agents (1 judge, 1 detector)
• ~3,500 lines of code
• Quantitative metrics
• Adaptive testing strategy
• Autonomous planning
```

---

## 🎯 How Code Starts (Initialization Flow)

### 1. Purple Agent Startup

```python
# purple_agents/baseline/sql_detector.py

if __name__ == "__main__":
    # 1. Parse arguments
    args = parser.parse_args()

    # 2. Create FastAPI app
    app = create_app()

    # 3. Define detection endpoint
    @app.post("/detect")
    async def detect(request: DetectRequest):
        # Pattern matching logic
        return DetectResponse(...)

    # 4. Start server
    uvicorn.run(app, host=args.host, port=args.port)
```

### 2. Green Agent Startup

```python
# scenarios/security/sql_injection_judge.py

async def main():
    # 1. Parse arguments
    args = parser.parse_args()

    # 2. Create Green Agent instance
    judge = SQLInjectionJudge(dataset_root)

    # 3. Load datasets
    judge.dataset_manager.load_datasets()

    # 4. Wrap in GreenExecutor
    executor = GreenExecutor(judge)

    # 5. Create agent card
    agent_card = sql_injection_agent_card("sql_injection_judge", agent_url)

    # 6. Create request handler
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )

    # 7. Create A2A server
    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    # 8. Start HTTP server
    uvicorn_config = uvicorn.Config(server.build(), ...)
    await uvicorn.Server(uvicorn_config).serve()

if __name__ == '__main__':
    asyncio.run(main())
```

### 3. Task Submission

```python
# When someone POSTs to /tasks:

# A2AStarletteApplication receives request
# ↓
# DefaultRequestHandler.handle_task()
# ↓
# GreenExecutor.execute()
# ↓
# SQLInjectionJudge.run_eval()
# ↓
# [Your evaluation logic runs]
# ↓
# Results stored in InMemoryTaskStore
# ↓
# Client polls /tasks/{id} to get results
```

---

## 📦 Information Passing

### Between Client and Green Agent

**Format:** A2A Protocol (HTTP/JSON)

```json
// Request
POST /tasks
{
  "input": {
    "purple_agent_endpoint": "...",
    "config": {...}
  }
}

// Response
{
  "id": "task_123",
  "status": "pending"
}

// Polling
GET /tasks/task_123
{
  "status": "completed",
  "output": {...}
}
```

### Between Green Agent and Purple Agent

**Format:** HTTP/JSON (domain-specific)

**For Debate:**
```json
POST http://127.0.0.1:9019/tasks
{
  "input": {
    "text": "Debate Topic: Should AI be regulated? Present your opening argument."
  }
}

Response:
{
  "output": {
    "text": "AI regulation is essential because..."
  }
}
```

**For SQL Injection:**
```json
POST http://127.0.0.1:8000/detect
{
  "test_case_id": "test_001",
  "code": "query = f'SELECT * FROM users WHERE id={user_id}'",
  "language": "python",
  "category": "classic_sqli"
}

Response:
{
  "is_vulnerable": true,
  "confidence": 0.95,
  "vulnerability_type": "SQL Injection",
  "explanation": "..."
}
```

### Within Green Agent

**Format:** Python objects (Pydantic models)

```python
# Input: EvalRequest
req = EvalRequest(
    purple_agent_endpoint="http://...",
    config={"mode": "adaptive", ...}
)

# Processing: Internal models
code_sample = CodeSample(code="...", is_vulnerable=True, ...)
test_result = TestResult(outcome=DetectionOutcome.TRUE_POSITIVE, ...)
metrics = EvaluationMetrics(f1_score=0.769, ...)

# Output: EvalResponse
response = EvalResponse(
    success=True,
    metrics=metrics,
    category_metrics=[...]
)
```

---

## 🔑 Key Concepts

### 1. **Green Agent**
- Orchestrator/evaluator
- Tests other agents
- Makes autonomous decisions
- Implements A2A protocol

### 2. **Purple Agent**
- Agent being evaluated
- Performs specific task (debate, detection, etc.)
- Responds to Green Agent requests

### 3. **A2A Protocol**
- Agent-to-Agent communication standard
- HTTP-based
- Task submission + polling model
- Agent cards describe capabilities

### 4. **GreenExecutor**
- Wrapper around Green Agent
- Handles A2A protocol details
- Manages task lifecycle
- Provides `TaskUpdater` for status updates

### 5. **TaskUpdater**
- Allows Green Agent to update task status
- Send progress messages
- Add artifacts (results, files, etc.)
- Client sees updates when polling

### 6. **Agent Card**
- JSON description of agent capabilities
- Name, description, version
- Skills (what it can do)
- Input/output modes
- Exposed at `GET /card`

---

## 🎓 Summary

### The Pattern:
1. **Purple Agents** start and wait for requests
2. **Green Agent** starts and exposes A2A endpoints
3. **Client** submits task to Green Agent
4. **Green Agent** orchestrates Purple Agent(s)
5. **Green Agent** evaluates results
6. **Client** polls for completion
7. **Results** returned via A2A protocol

### Your Implementation Uses This Pattern:
- Purple Agent = SQL Injection Detector
- Green Agent = Evaluation System with Adaptive Testing
- Client = Any system submitting evaluation tasks
- Results = Comprehensive security metrics

### The Sample (Debate) Shows:
- How to structure Green/Purple agents
- How to use A2A protocol
- How to orchestrate multiple agents
- How to implement custom evaluation logic

Both follow the same architectural pattern, just with different domains and complexity levels!
