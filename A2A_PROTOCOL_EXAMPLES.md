# A2A Protocol - How to Start Evaluations

## Overview

When both agents are running:
- **Purple Agent (Detector)**: `http://127.0.0.1:8000`
- **Green Agent (Judge)**: `http://127.0.0.1:9010`

The **Green Agent** implements the A2A (Agent-to-Agent) protocol with these endpoints:
- `GET /card` - Agent card (capabilities, description)
- `POST /tasks` - Submit evaluation task
- `GET /tasks/{task_id}` - Check task status
- `GET /tasks` - List all tasks

---

## Method 1: Using the Python Script (Recommended)

```bash
python start_evaluation.py
```

This script:
1. Checks both agents are running
2. Submits an evaluation task
3. Polls for completion
4. Displays comprehensive results

**Configuration** (edit in the script):
```python
task_payload = {
    "input": {
        "purple_agent_id": "baseline_sql_detector",
        "purple_agent_endpoint": "http://127.0.0.1:8000",
        "config": {
            "mode": "fixed",        # or "adaptive"
            "test_budget": 20,      # Number of tests
            "seed": 42              # For reproducibility
        }
    }
}
```

---

## Method 2: Using curl (Manual)

### Step 1: Check Green Agent Card

```bash
curl http://127.0.0.1:9010/card | python -m json.tool
```

**Expected response:**
```json
{
  "name": "sql_injection_judge",
  "url": "http://127.0.0.1:9010",
  "description": "Autonomous SQL Injection Detection Evaluator...",
  "capabilities": [...],
  "metadata": {...}
}
```

---

### Step 2: Submit Evaluation Task

```bash
curl -X POST http://127.0.0.1:9010/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "purple_agent_id": "baseline_sql_detector",
      "purple_agent_endpoint": "http://127.0.0.1:8000",
      "config": {
        "mode": "fixed",
        "test_budget": 20,
        "seed": 42
      },
      "metadata": {
        "evaluation_timestamp": "2025-01-04T10:00:00Z",
        "evaluator": "manual_curl"
      }
    }
  }' | python -m json.tool
```

**Response:**
```json
{
  "id": "task_abc123",
  "status": "pending",
  "created_at": "2025-01-04T10:00:00.123Z",
  "input": {...}
}
```

**Save the task ID!** You'll need it to check status.

---

### Step 3: Check Task Status

```bash
# Replace task_abc123 with your actual task ID
curl http://127.0.0.1:9010/tasks/task_abc123 | python -m json.tool
```

**While running:**
```json
{
  "id": "task_abc123",
  "status": "running",
  "created_at": "2025-01-04T10:00:00.123Z",
  "started_at": "2025-01-04T10:00:01.456Z"
}
```

**When completed:**
```json
{
  "id": "task_abc123",
  "status": "completed",
  "created_at": "2025-01-04T10:00:00.123Z",
  "started_at": "2025-01-04T10:00:01.456Z",
  "completed_at": "2025-01-04T10:00:30.789Z",
  "output": {
    "success": true,
    "metrics": {
      "f1_score": 0.769,
      "precision": 1.0,
      "recall": 0.625,
      "accuracy": 0.7,
      "confusion_matrix": {
        "true_positives": 5,
        "true_negatives": 2,
        "false_positives": 0,
        "false_negatives": 3
      },
      "false_positive_rate": 0.0,
      "false_negative_rate": 0.375
    },
    "category_metrics": [...]
  }
}
```

---

### Step 4: List All Tasks

```bash
curl http://127.0.0.1:9010/tasks | python -m json.tool
```

---

## Configuration Options

### Evaluation Modes

**Fixed Mode** (Traditional):
```json
{
  "config": {
    "mode": "fixed",
    "test_budget": 100
  }
}
```
- Runs exactly N tests
- Random sampling across all categories
- No adaptation

**Adaptive Mode** (Intelligent):
```json
{
  "config": {
    "mode": "adaptive",
    "test_budget": 100,
    "weak_threshold": 0.6,
    "focus_percentage": 0.6,
    "max_rounds": 5
  }
}
```
- Identifies weak categories (F1 < threshold)
- Allocates 60% of tests to weak areas
- Adapts strategy each round
- Autonomous decision-making

---

## Understanding the Response

### Success Response

```json
{
  "success": true,
  "metrics": {
    "f1_score": 0.85,          // Overall balanced performance
    "precision": 0.90,          // Of predicted vulnerable, how many correct?
    "recall": 0.80,             // Of actual vulnerabilities, how many caught?
    "accuracy": 0.82,           // Overall correctness
    "confusion_matrix": {
      "true_positives": 16,     // Correctly identified vulnerabilities
      "true_negatives": 4,      // Correctly identified secure code
      "false_positives": 2,     // False alarms
      "false_negatives": 5      // Missed vulnerabilities (DANGEROUS!)
    },
    "false_positive_rate": 0.33,  // False alarm rate
    "false_negative_rate": 0.24   // Miss rate
  },
  "category_metrics": [
    {
      "category": "classic_sqli",
      "sample_count": 5,
      "metrics": {
        "f1_score": 1.0,
        "precision": 1.0,
        "recall": 1.0
      }
    },
    {
      "category": "second_order",
      "sample_count": 3,
      "metrics": {
        "f1_score": 0.0,        // Weak category!
        "precision": 0.0,
        "recall": 0.0
      }
    }
  ]
}
```

### Error Response

```json
{
  "success": false,
  "error_message": "Purple agent not responding at http://127.0.0.1:8000",
  "metrics": null,
  "category_metrics": []
}
```

---

## What Happens During Evaluation

### Fixed Mode Flow:
1. Green Agent samples N tests from dataset
2. For each test:
   - Sends code to Purple Agent
   - Compares Purple Agent response to ground truth
   - Records outcome (TP, TN, FP, FN)
3. Calculates metrics
4. Returns results

### Adaptive Mode Flow:
1. **Round 1 - Exploration**:
   - Sample diverse tests
   - Execute and analyze
   - Identify weak categories (F1 < threshold)

2. **Rounds 2-N - Exploitation**:
   - Allocate 60% tests to weak categories
   - 40% to other categories (maintenance)
   - Re-evaluate weak category performance
   - Update strategy

3. **Final Round - Validation**:
   - Test with fresh samples
   - Verify performance is stable
   - Return comprehensive results

---

## Example: Full Workflow

```bash
# Terminal 1: Start Purple Agent
python purple_agents/baseline/sql_detector.py --port 8000

# Terminal 2: Start Green Agent
python scenarios/security/sql_injection_judge.py --port 9010 --dataset-root datasets/sql_injection

# Terminal 3: Start Evaluation
python start_evaluation.py

# Or use curl:
curl -X POST http://127.0.0.1:9010/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "purple_agent_id": "baseline_sql_detector",
      "purple_agent_endpoint": "http://127.0.0.1:8000",
      "config": {"mode": "adaptive", "test_budget": 50}
    }
  }'

# Save the task_id from response, then poll:
curl http://127.0.0.1:9010/tasks/TASK_ID
```

---

## Troubleshooting

### "Connection refused" error
- Check both agents are running
- Verify ports: Purple=8000, Green=9010

### "Purple agent not responding"
```bash
# Test Purple Agent manually
curl http://127.0.0.1:8000/health
```

### Task stuck in "pending" status
- Check Green Agent logs in Terminal 2
- Verify dataset is loaded correctly

### Want to run multiple evaluations?
```bash
# Each evaluation is independent
python start_evaluation.py  # Run 1
python start_evaluation.py  # Run 2
```

---

## Advanced: Programmatic Integration

```python
import httpx

async def run_evaluation(purple_endpoint: str, mode: str = "fixed", budget: int = 100):
    async with httpx.AsyncClient() as client:
        # Submit task
        response = await client.post("http://127.0.0.1:9010/tasks", json={
            "input": {
                "purple_agent_id": "test_agent",
                "purple_agent_endpoint": purple_endpoint,
                "config": {"mode": mode, "test_budget": budget}
            }
        })
        task = response.json()
        task_id = task["id"]

        # Poll for completion
        while True:
            status_response = await client.get(f"http://127.0.0.1:9010/tasks/{task_id}")
            status = status_response.json()

            if status["status"] == "completed":
                return status["output"]
            elif status["status"] == "failed":
                raise Exception(f"Task failed: {status.get('error')}")

            await asyncio.sleep(2)

# Usage
results = await run_evaluation("http://127.0.0.1:8000", mode="adaptive", budget=50)
print(f"F1 Score: {results['metrics']['f1_score']}")
```

---

## Summary

**To start an evaluation:**
1. ✅ Ensure both agents running
2. 📤 POST to `/tasks` with evaluation config
3. ⏳ Poll `/tasks/{task_id}` for status
4. 📊 Retrieve results when `status == "completed"`

**Quick start:** `python start_evaluation.py`
