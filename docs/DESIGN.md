# SecurityEvaluator - System Design Document

**Project:** SQL Injection Detection Benchmark for AgentBeats
**Version:** 1.0
**Date:** November 4, 2025
**Competition:** AgentBeats Phase 1 (Green Agent)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Green Agent Design](#3-green-agent-design)
4. [Purple Agent Design](#4-purple-agent-design)
5. [Data Flow](#5-data-flow)
6. [Dataset Design](#6-dataset-design)
7. [Scoring Engine](#7-scoring-engine)
8. [Communication Protocol](#8-communication-protocol)
9. [Deployment Architecture](#9-deployment-architecture)

---

## 1. Executive Summary

### 1.1 Project Goal

Create a **SQL Injection Detection Benchmark** (Green Agent) that evaluates AI agents' capabilities to identify SQL injection vulnerabilities in code and API requests.

### 1.2 Key Objectives

1. **Standardized Evaluation:** Reproducible testing of security analysis agents
2. **Comprehensive Coverage:** 500+ test cases covering all SQL injection variants
3. **Objective Scoring:** Automated metrics (TPR, FPR, F1, severity accuracy)
4. **AgentBeats Integration:** Full A2A protocol compliance
5. **Open Benchmark:** Public dataset and scoring methodology

### 1.3 Design Philosophy

**Detection-First Approach:**
- Purple Agents **detect** vulnerabilities (not exploit them)
- Ethical: No exploitation, only static/dynamic analysis
- Objective: Clear ground truth (vulnerable vs. secure)
- Practical: Aligns with real-world security auditing

**Single-Focus Excellence:**
- SQL Injection only (not all OWASP Top 10)
- Deep coverage of SQL injection variants
- Foundation for future vulnerability type extensions

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentBeats Platform                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Assessment Request                                   │   │
│  │  {                                                    │   │
│  │    "participants": {"sql_detector": "https://..."},  │   │
│  │    "config": {"test_suite": "sql_injection_v1"}      │   │
│  │  }                                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           GREEN AGENT: SQLInjectionJudge                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  1. Load Test Dataset (500+ samples)                 │   │
│  │  2. For each test case:                              │   │
│  │     a. Send code/request to Purple Agent             │   │
│  │     b. Receive vulnerability report                  │   │
│  │     c. Compare with ground truth                     │   │
│  │  3. Calculate metrics (TPR, FPR, F1)                 │   │
│  │  4. Generate detailed assessment report              │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Components:                                                 │
│  ├── Dataset Manager      (load & sample test cases)        │
│  ├── Test Orchestrator    (send cases to Purple Agent)      │
│  ├── Response Validator   (parse Purple Agent responses)    │
│  ├── Scoring Engine       (calculate metrics)               │
│  └── Report Generator     (produce A2A artifacts)           │
└───────────────────────┬─────────────────────────────────────┘
                        │ A2A Protocol
                        │ (HTTP/JSON)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│         PURPLE AGENT: SQL Injection Detector                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Input: Code snippet or HTTP request                 │   │
│  │  {                                                    │   │
│  │    "type": "code",                                    │   │
│  │    "language": "python",                              │   │
│  │    "content": "query = f'SELECT * FROM users..."     │   │
│  │  }                                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                        │                                     │
│                        ▼                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Analysis Engine                                      │   │
│  │  ├── Static Analysis (AST parsing, pattern matching) │   │
│  │  ├── Dynamic Analysis (taint tracking)               │   │
│  │  ├── LLM Analysis (code understanding)               │   │
│  │  └── Hybrid Approach (combine methods)               │   │
│  └──────────────────────────────────────────────────────┘   │
│                        │                                     │
│                        ▼                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Output: Vulnerability Report                         │   │
│  │  {                                                    │   │
│  │    "is_vulnerable": true,                             │   │
│  │    "vulnerability_type": "classic_sqli",              │   │
│  │    "severity": "high",                                │   │
│  │    "confidence": 0.95,                                │   │
│  │    "location": "line 42",                             │   │
│  │    "explanation": "User input concatenated...",       │   │
│  │    "remediation": "Use parameterized queries"         │   │
│  │  }                                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

| Component | Responsibility | Owner |
|-----------|---------------|-------|
| **Green Agent** | Test orchestration, scoring, reporting | You (Benchmark creator) |
| **Purple Agent** | Vulnerability detection, analysis | Participants (AgentBeats users) |
| **Dataset** | Ground truth test cases | Green Agent (static) |
| **AgentBeats Platform** | Agent registration, assessment coordination | AgentBeats.org |

---

## 3. Green Agent Design

### 3.1 Core Components

#### 3.1.1 SQLInjectionJudge (Main Green Agent)

**File:** `scenarios/security/sql_injection_judge.py`

**Responsibilities:**
1. Load and manage test dataset
2. Orchestrate test case execution
3. **Make autonomous decisions about test strategy** (adaptive testing)
4. Validate Purple Agent responses
5. Calculate performance metrics
6. Generate assessment artifacts

**Agentic Behaviors:**

The Green Agent exhibits true **autonomous decision-making** to justify its classification as an "agent":

1. **Adaptive Test Selection**: Analyzes Purple Agent performance and autonomously selects targeted test cases
2. **Difficulty Progression**: Decides whether to escalate to harder tests based on performance thresholds
3. **Weak Area Identification**: Identifies vulnerability categories where Purple Agent struggles
4. **Dynamic Test Generation**: Can generate targeted follow-up tests based on observed weaknesses
5. **Strategic Planning**: Creates and adjusts test execution strategy during evaluation

**Key Methods:**

```python
class SQLInjectionJudge(GreenAgent):
    def __init__(self):
        self._dataset_manager = DatasetManager()
        self._scoring_engine = ScoringEngine()
        self._test_orchestrator = TestOrchestrator()
        self._adaptive_planner = AdaptiveTestPlanner()  # NEW: Autonomous decision-making

    async def run_eval(self, req: EvalRequest, updater: TaskUpdater) -> None:
        """Main evaluation loop with adaptive testing"""

    async def send_test_case(self, agent_url: str, test_case: TestCase) -> DetectionReport:
        """Send single test case to Purple Agent"""

    def validate_response(self, response: dict, ground_truth: TestCase) -> ValidationResult:
        """Validate Purple Agent response format and content"""

    def calculate_metrics(self, results: list[ValidationResult]) -> Metrics:
        """Calculate TPR, FPR, F1, etc."""

    # NEW: Autonomous decision-making methods
    async def identify_weak_categories(self, results: list[TestResult]) -> list[str]:
        """AUTONOMOUS: Analyze results and identify weak areas"""

    async def decide_next_tests(self, current_results: list[TestResult]) -> list[TestCase]:
        """AUTONOMOUS: Decide which tests to run next based on performance"""

    def should_escalate_difficulty(self, results: list[TestResult], threshold: float = 0.7) -> bool:
        """AUTONOMOUS: Decide if agent is ready for harder tests"""
```

#### 3.1.2 DatasetManager

**File:** `scenarios/security/dataset_manager.py`

**Responsibilities:**
- Load test cases from disk
- Sample test cases (full suite or subset)
- Filter by category (e.g., only blind SQL injection)
- Shuffle for randomization
- Track test case metadata

**Interface:**

```python
class DatasetManager:
    def __init__(self, dataset_path: str = "scenarios/security/datasets/sql_injection"):
        self._vulnerable_samples: list[TestCase] = []
        self._secure_samples: list[TestCase] = []
        self._metadata: dict[str, TestCaseMetadata] = {}

    def load_dataset(self) -> None:
        """Load all test cases from disk"""

    def sample(self, n: int = 100, categories: list[str] | None = None) -> list[TestCase]:
        """Sample n test cases, optionally filtered by category"""

    def get_by_id(self, test_id: str) -> TestCase:
        """Retrieve specific test case"""

    def get_statistics(self) -> DatasetStats:
        """Return dataset composition statistics"""
```

#### 3.1.3 TestOrchestrator

**File:** `scenarios/security/test_orchestrator.py`

**Responsibilities:**
- Manage concurrent test execution
- Handle timeouts and retries
- Track progress and update status
- Rate limiting (respect Purple Agent limits)

**Interface:**

```python
class TestOrchestrator:
    def __init__(self, max_concurrent: int = 10, timeout: int = 30):
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._timeout = timeout

    async def run_tests(
        self,
        agent_url: str,
        test_cases: list[TestCase],
        updater: TaskUpdater
    ) -> list[TestResult]:
        """Run all test cases with progress tracking"""

    async def run_single_test(
        self,
        agent_url: str,
        test_case: TestCase
    ) -> TestResult:
        """Run single test case with timeout"""
```

#### 3.1.4 ScoringEngine

**File:** `scenarios/security/scoring_engine.py`

**Responsibilities:**
- Calculate classification metrics
- Assess severity prediction accuracy
- Generate detailed breakdown by category
- Produce final scores and rankings

**Metrics Calculated:**

1. **Binary Classification Metrics:**
   - True Positive Rate (TPR / Recall)
   - True Negative Rate (TNR / Specificity)
   - False Positive Rate (FPR)
   - False Negative Rate (FNR)
   - Precision
   - F1 Score
   - Accuracy

2. **Severity Assessment:**
   - Severity prediction accuracy (if ground truth has severity)
   - Mean Absolute Error (MAE) for severity scores

3. **Category Breakdown:**
   - Metrics per SQL injection type (classic, blind, time-based, etc.)
   - Confusion matrix

4. **Confidence Calibration:**
   - If Purple Agent provides confidence scores, measure calibration

**Interface:**

```python
class ScoringEngine:
    def calculate_metrics(self, results: list[TestResult]) -> EvaluationMetrics:
        """Calculate all metrics"""

    def generate_confusion_matrix(self, results: list[TestResult]) -> ConfusionMatrix:
        """Generate confusion matrix"""

    def breakdown_by_category(self, results: list[TestResult]) -> dict[str, CategoryMetrics]:
        """Per-category performance"""
```

#### 3.1.5 AdaptiveTestPlanner (NEW - Autonomous Decision-Making)

**File:** `scenarios/security/adaptive_planner.py`

**Purpose:** Provides autonomous decision-making capabilities to justify "agent" classification

**Responsibilities:**
- **Analyze performance patterns** across test results
- **Identify weak categories** where Purple Agent struggles
- **Decide test strategy** (explore breadth vs exploit depth)
- **Select targeted tests** based on observed weaknesses
- **Determine difficulty progression** based on performance thresholds

**Autonomous Behaviors:**

1. **Weak Area Detection**
   ```python
   # If Purple Agent has < 50% F1 on blind_sqli, focus more tests there
   weak_categories = identify_weak_categories(results)
   # → ["blind_sqli", "time_based"]
   ```

2. **Strategic Test Selection**
   ```python
   # Initial: Diverse sample (20% from each category)
   # After analysis: 60% from weak categories, 40% from strong
   next_batch = select_strategic_tests(weak_categories, remaining_budget=30)
   ```

3. **Difficulty Escalation**
   ```python
   # If F1 > 0.7 on easy tests, autonomously decide to try hard tests
   if should_escalate_difficulty(results, threshold=0.7):
       next_batch = dataset.sample(difficulty="hard")
   ```

**Interface:**

```python
class AdaptiveTestPlanner:
    def __init__(self, strategy: str = "adaptive"):
        """
        strategy:
          - "fixed": Traditional fixed test set (no adaptation)
          - "adaptive": Autonomous test selection based on performance
          - "progressive": Difficulty-based progression
        """
        self.strategy = strategy

    def create_initial_plan(self, config: dict) -> TestPlan:
        """Create initial test plan (diverse sample)"""

    def analyze_performance(self, results: list[TestResult]) -> PerformanceAnalysis:
        """AUTONOMOUS: Analyze Purple Agent's strengths/weaknesses"""

    def identify_weak_categories(self, analysis: PerformanceAnalysis) -> list[str]:
        """AUTONOMOUS: Determine which categories need more testing"""

    def decide_next_batch(
        self,
        current_results: list[TestResult],
        remaining_budget: int
    ) -> list[TestCase]:
        """AUTONOMOUS: Decide which tests to run next"""

    def should_continue_testing(
        self,
        results: list[TestResult],
        budget_used: int,
        max_budget: int
    ) -> bool:
        """AUTONOMOUS: Decide if more testing is needed"""

    def calculate_category_coverage(self, results: list[TestResult]) -> dict[str, float]:
        """Calculate test coverage per category"""
```

**Decision Logic Examples:**

```python
# Example 1: Weak area detection
def identify_weak_categories(self, results: list[TestResult]) -> list[str]:
    category_f1 = {}
    for category in self.all_categories:
        cat_results = [r for r in results if r.ground_truth.category == category]
        if cat_results:
            category_f1[category] = calculate_f1(cat_results)

    # AUTONOMOUS DECISION: Categories with F1 < 0.6 are "weak"
    weak = [cat for cat, f1 in category_f1.items() if f1 < 0.6]
    return weak

# Example 2: Strategic test selection
def decide_next_batch(self, current_results, remaining_budget):
    weak_categories = self.identify_weak_categories(current_results)

    if weak_categories:
        # AUTONOMOUS DECISION: Focus 70% on weak areas, 30% on others
        weak_samples = int(remaining_budget * 0.7)
        other_samples = remaining_budget - weak_samples

        batch = []
        batch.extend(self.dataset.sample(weak_samples, categories=weak_categories))
        batch.extend(self.dataset.sample(other_samples, categories="all"))
        return batch
    else:
        # AUTONOMOUS DECISION: Performance is balanced, sample uniformly
        return self.dataset.sample(remaining_budget, categories="all")
```

**Why This Makes It An "Agent":**

✅ **Autonomous**: Makes decisions without human intervention
✅ **Goal-oriented**: Optimizes for finding agent's true capabilities
✅ **Reactive**: Responds to Purple Agent's performance
✅ **Strategic**: Plans multi-step test sequences
✅ **Adaptive**: Changes behavior based on observations

**No LLM Required:** All decisions are rule-based but exhibit agency through autonomous adaptation.

---

#### 3.1.6 ReportGenerator

**File:** `scenarios/security/report_generator.py`

**Responsibilities:**
- Format results as A2A artifacts
- Generate human-readable reports
- Create visualizations (optional)
- Export to multiple formats (JSON, markdown, HTML)

**Interface:**

```python
class ReportGenerator:
    def generate_artifact(self, metrics: EvaluationMetrics) -> list[Part]:
        """Generate A2A artifact parts"""

    def generate_markdown_report(self, metrics: EvaluationMetrics) -> str:
        """Generate detailed markdown report"""

    def generate_summary(self, metrics: EvaluationMetrics) -> str:
        """Generate concise summary"""
```

### 3.2 Configuration

**File:** `scenarios/security/scenario.toml`

```toml
[sql_injection_judge]
endpoint = "http://127.0.0.1:9009"
cmd = "python scenarios/security/sql_injection_judge.py --host 127.0.0.1 --port 9009"

[[config]]
test_suite = "sql_injection_v1"
sample_size = 100  # Number of test cases (or "all" for full 500+)
timeout = 30  # Per-test timeout in seconds
max_concurrent = 10  # Max parallel tests
categories = ["all"]  # Or ["classic", "blind", "time_based"]
```

### 3.3 Green Agent Workflow (With Autonomous Decision-Making)

**Two Modes:** Fixed (traditional) and Adaptive (agentic)

#### Mode 1: Fixed Testing (Simple, No Agency)

```
┌─────────────────────────────────────────────────────────┐
│ 1. Receive Assessment Request                           │
│    - Validate Purple Agent endpoint                     │
│    - Parse configuration (sample_size, categories)      │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Load Test Dataset                                    │
│    - DatasetManager.load_dataset()                      │
│    - Sample N test cases based on config (one-time)     │
│    - Shuffle for randomization                          │
│    Status Update: "Loaded 100 test cases"               │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Run All Tests (No adaptation)                        │
│    For each test case (parallel, max 10):               │
│      a. Send A2A message to Purple Agent                │
│      b. Wait for response (timeout 30s)                 │
│      c. Validate response format                        │
│      d. Compare with ground truth                       │
│    Status Update: "Completed 100/100 tests"             │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 4. Calculate Final Metrics                              │
│    - ScoringEngine.calculate_metrics()                  │
│    - Generate confusion matrix                          │
│    Status: Complete                                     │
└─────────────────────────────────────────────────────────┘
```

#### Mode 2: Adaptive Testing (Agentic, Autonomous)

```
┌─────────────────────────────────────────────────────────┐
│ 1. Receive Assessment Request                           │
│    - Validate Purple Agent endpoint                     │
│    - Parse configuration (test_budget=100, mode=adaptive)│
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Initialize Adaptive Planner                          │
│    - AdaptiveTestPlanner.create_initial_plan()          │
│    - DECISION: Sample 20 diverse tests (explore phase)  │
│    Status Update: "Starting with 20 diverse tests"      │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Round 1: Exploration (20 tests)                      │
│    - Run diverse sample across all categories           │
│    - Track performance per category                     │
│    Status: "Completed 20/100 tests"                     │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 4. 🤖 AUTONOMOUS ANALYSIS                               │
│    - AdaptivePlanner.analyze_performance(round1_results)│
│    - Identify weak categories (F1 < 0.6):               │
│      → blind_sqli: F1=0.45                              │
│      → time_based: F1=0.52                              │
│    - DECISION: Focus 60% of remaining tests on weak areas│
│    Status: "Detected weakness in blind_sqli, adapting..."│
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 5. Round 2: Targeted Testing (40 tests)                 │
│    - 24 tests on blind_sqli (60% focus)                 │
│    - 8 tests on time_based (20% focus)                  │
│    - 8 tests on other categories (20% coverage)         │
│    Status: "Completed 60/100 tests"                     │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 6. 🤖 AUTONOMOUS RE-EVALUATION                          │
│    - AdaptivePlanner.analyze_performance(all_results)   │
│    - Check if weak areas improved                       │
│    - DECISION: blind_sqli still weak (F1=0.48)          │
│    - DECISION: Drill deeper with 30 more blind_sqli tests│
│    Status: "Drilling deeper into blind_sqli..."         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 7. Round 3: Deep Dive (30 tests)                        │
│    - 30 blind_sqli tests (various difficulty levels)    │
│    Status: "Completed 90/100 tests"                     │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 8. 🤖 AUTONOMOUS TERMINATION DECISION                   │
│    - AdaptivePlanner.should_continue_testing()          │
│    - Check if remaining budget (10 tests) is sufficient │
│    - DECISION: Allocate final 10 tests to untested edge │
│      cases in secure_orm category                       │
│    Status: "Final validation with 10 tests..."          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 9. Round 4: Final Validation (10 tests)                 │
│    - 10 secure_orm tests (false positive check)         │
│    Status: "Completed 100/100 tests"                    │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│ 10. Calculate Final Metrics                             │
│    - ScoringEngine.calculate_metrics()                  │
│    - Generate confusion matrix                          │
│    - Include adaptive testing report:                   │
│      * Number of rounds: 4                              │
│      * Autonomous decisions made: 4                     │
│      * Weak categories identified: 2                    │
│      * Test distribution: [explore=20, exploit=70, validate=10]│
│    Status: Complete                                     │
└─────────────────────────────────────────────────────────┘
```

**Key Differences:**

| Aspect | Fixed Mode | Adaptive Mode (Agentic) |
|--------|------------|------------------------|
| **Test Selection** | One-time, uniform | Multi-round, strategic |
| **Decision Points** | 0 | 4+ autonomous decisions |
| **Test Distribution** | Uniform across categories | Focused on weak areas |
| **Rounds** | 1 (all tests at once) | 3-5 (iterative refinement) |
| **Agency** | ❌ None | ✅ Autonomous adaptation |
| **Efficiency** | Tests wasted on strong areas | Optimizes test budget |

**Configuration:**

```yaml
# config.yaml
evaluation:
  mode: "adaptive"  # or "fixed"
  test_budget: 100
  initial_exploration: 20  # First round: diverse sample
  adaptation_threshold: 0.6  # F1 < 0.6 = weak category
  focus_percentage: 0.6  # 60% of tests on weak areas
```

---

## 4. Purple Agent Design

### 4.1 Reference Implementation

**File:** `purple_agents/baseline/sql_detector.py`

**Purpose:** Provide a baseline implementation for:
- Testing Green Agent during development
- Demonstrating expected Purple Agent interface
- Benchmarking (other Purple Agents should beat baseline)

### 4.2 Purple Agent Interface

#### 4.2.1 Agent Card

```python
AgentCard(
    name="SQL Injection Detector",
    description="Analyzes code and HTTP requests for SQL injection vulnerabilities",
    url="https://...",
    version="1.0.0",
    capabilities=AgentCapabilities(streaming=True),
    skills=[
        AgentSkill(
            id="sql_injection_detection",
            name="SQL Injection Detection",
            description="Static and dynamic analysis of code for SQL injection vulnerabilities",
            tags=["security", "sql-injection", "sast", "vulnerability-detection"],
            examples=[...]
        )
    ]
)
```

#### 4.2.2 Input Format

Purple Agents receive test cases via A2A messages:

**Type 1: Code Analysis**

```json
{
  "test_id": "classic_sqli_001",
  "type": "code",
  "language": "python",
  "content": "def get_user(user_id):\n    query = f'SELECT * FROM users WHERE id={user_id}'\n    return db.execute(query)",
  "context": {
    "framework": "flask",
    "database": "postgresql"
  }
}
```

**Type 2: HTTP Request Analysis**

```json
{
  "test_id": "blind_sqli_045",
  "type": "http_request",
  "method": "GET",
  "url": "https://example.com/api/users?id=1' OR '1'='1",
  "headers": {
    "Content-Type": "application/json"
  },
  "body": null
}
```

#### 4.2.3 Output Format

Purple Agents return structured vulnerability reports:

```json
{
  "test_id": "classic_sqli_001",
  "is_vulnerable": true,
  "vulnerability_type": "classic_sqli",
  "severity": "high",
  "confidence": 0.95,
  "location": {
    "line": 2,
    "column": 13,
    "snippet": "query = f'SELECT * FROM users WHERE id={user_id}'"
  },
  "explanation": "User input 'user_id' is directly concatenated into SQL query using f-string, allowing SQL injection. An attacker can manipulate the user_id parameter to execute arbitrary SQL.",
  "attack_vector": "Modify user_id parameter to: 1 OR 1=1--",
  "remediation": "Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id=%s', (user_id,))",
  "cwe_id": "CWE-89",
  "owasp_category": "A03:2021-Injection"
}
```

**Field Specifications:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `test_id` | string | ✓ | Echo back from input |
| `is_vulnerable` | boolean | ✓ | True if SQL injection detected |
| `vulnerability_type` | enum | ✓ | classic_sqli, blind_sqli, time_based, union_based, error_based, second_order |
| `severity` | enum | ✓ | low, medium, high, critical |
| `confidence` | float | ✗ | 0.0-1.0 confidence score |
| `location` | object | ✗ | Where vulnerability is located |
| `explanation` | string | ✗ | Human-readable explanation |
| `attack_vector` | string | ✗ | Example exploit payload |
| `remediation` | string | ✗ | Fix recommendation |
| `cwe_id` | string | ✗ | CWE identifier |
| `owasp_category` | string | ✗ | OWASP Top 10 mapping |

### 4.3 Purple Agent Variants

We'll provide **three reference implementations**:

#### 4.3.1 Baseline (Rule-Based)
**File:** `purple_agents/baseline/sql_detector.py`
- Simple regex and pattern matching
- Fast but limited accuracy
- No ML/LLM dependencies
- Expected F1: ~0.60

#### 4.3.2 LLM-Based
**File:** `purple_agents/llm_based/sql_detector.py`
- Uses LLM (Gemini/GPT-4) for code understanding
- Structured output with JSON schema
- High accuracy but expensive
- Expected F1: ~0.85

#### 4.3.3 Hybrid
**File:** `purple_agents/hybrid/sql_detector.py`
- Rule-based pre-filtering
- LLM for complex cases only
- Balance of cost and accuracy
- Expected F1: ~0.80

---

## 5. Data Flow

### 5.1 Assessment Lifecycle

```
┌──────────────┐
│ AgentBeats   │
│ Platform     │
└──────┬───────┘
       │
       │ 1. POST /tasks (assessment_request)
       │    {
       │      "participants": {"sql_detector": "https://detector.example.com"},
       │      "config": {"test_suite": "sql_injection_v1", "sample_size": 100}
       │    }
       ▼
┌──────────────────────────┐
│ Green Agent              │
│ (SQLInjectionJudge)      │
└──────┬───────────────────┘
       │
       │ 2. Load test dataset (100 samples)
       │
       │ 3. For each test case:
       │    │
       │    │ POST /tasks (test_case)
       │    │ {
       │    │   "test_id": "classic_sqli_001",
       │    │   "type": "code",
       │    │   "language": "python",
       │    │   "content": "..."
       │    │ }
       │    ▼
       │   ┌──────────────────────────┐
       │   │ Purple Agent             │
       │   │ (SQL Detector)           │
       │   └──────┬───────────────────┘
       │          │
       │          │ Analyze code
       │          │
       │          │ Response (artifact)
       │          │ {
       │          │   "is_vulnerable": true,
       │          │   "vulnerability_type": "classic_sqli",
       │          │   ...
       │          │ }
       │    ┌─────┘
       │    │
       │ 4. Validate response
       │ 5. Compare with ground truth
       │
       │ 6. After all tests:
       │    - Calculate metrics (TPR, FPR, F1)
       │    - Generate report
       │
       │ 7. Publish artifacts
       │    - JSON metrics
       │    - Markdown report
       │    - Confusion matrix
       │
       ▼
┌──────────────────────────┐
│ AgentBeats Platform      │
│ - Display results        │
│ - Update leaderboard     │
└──────────────────────────┘
```

### 5.2 Message Flow Detail

```
Green Agent                              Purple Agent
    │                                        │
    │ ─────── POST /tasks ──────────────────▶│
    │                                        │
    │ {                                      │
    │   "message": {                         │
    │     "parts": [                         │
    │       {                                │
    │         "text": {                      │
    │           "text": "{\"test_id\":...}"  │  Parse JSON
    │         }                              │  Extract test case
    │       }                                │
    │     ]                                  │
    │   }                                    │
    │ }                                      │
    │                                        │
    │                                        │  Analyze code
    │                                        │  - Static analysis
    │                                        │  - Pattern matching
    │                                        │  - LLM inference
    │                                        │
    │                                        │  Generate report
    │                                        │
    │ ◀─────── Task Update (working) ────────│
    │                                        │
    │ {                                      │
    │   "state": "working",                  │
    │   "message": "Analyzing code..."       │
    │ }                                      │
    │                                        │
    │ ◀─────── Artifact (result) ────────────│
    │                                        │
    │ {                                      │
    │   "name": "vulnerability_report",      │
    │   "parts": [                           │
    │     {                                  │
    │       "text": {                        │
    │         "text": "{\"is_vulnerable\":...}" │
    │       }                                │
    │     }                                  │
    │   ]                                    │
    │ }                                      │
    │                                        │
    │ Extract report                         │
    │ Compare with ground truth              │
    │ Record result (TP/TN/FP/FN)            │
    │                                        │
```

---

## 6. Dataset Design

### 6.1 Directory Structure

**Recommended: JSON Format** (easier to manage than 500+ individual files)

```
scenarios/security/datasets/sql_injection/
├── metadata.json                    # Master metadata file
├── vulnerable_code/
│   ├── python_sqli.json             # 175 Python vulnerable samples
│   ├── javascript_sqli.json         # 90 JavaScript samples
│   ├── java_sqli.json               # 50 Java samples
│   └── php_sqli.json                # 35 PHP samples
└── secure_code/
    ├── python_secure.json           # 125 Python secure samples
    ├── javascript_secure.json       # 60 JavaScript samples
    ├── java_secure.json             # 40 Java samples
    └── php_secure.json              # 25 PHP samples
```

**Total:** 600 samples in 8 JSON files
- **Vulnerable:** ~350 samples across 4 languages
- **Secure:** ~250 samples across 4 languages

**Benefits of JSON format:**
- ✅ Edit 8 files instead of managing 600+ individual files
- ✅ 10x faster to load (one I/O per language vs 600 I/Os)
- ✅ Easier version control (cleaner diffs)
- ✅ Simple schema validation
- ✅ Easier programmatic generation

**Alternative: Individual Files** (if needed for specific use cases)

```
scenarios/security/datasets/sql_injection/
├── metadata.json
├── vulnerable/classic/sqli_classic_001.py ... sqli_classic_100.py
├── vulnerable/blind/sqli_blind_001.py ... sqli_blind_080.py
└── ... (600+ individual files)
```
Only use if you need separate file editing for each test case.

### 6.2 Metadata Format

**File:** `scenarios/security/datasets/sql_injection/metadata.json`

```json
{
  "dataset_version": "1.0",
  "created": "2025-11-04",
  "total_samples": 600,
  "vulnerable_samples": 350,
  "secure_samples": 250,
  "languages": ["python", "javascript", "java", "php"],
  "frameworks": ["flask", "django", "express", "spring", "laravel"],
  "databases": ["postgresql", "mysql", "sqlite", "mssql"],
  "test_cases": [
    {
      "id": "sqli_classic_001",
      "file": "vulnerable/classic/sqli_classic_001.py",
      "is_vulnerable": true,
      "category": "classic_sqli",
      "severity": "high",
      "language": "python",
      "framework": "flask",
      "database": "postgresql",
      "cwe_id": "CWE-89",
      "description": "Direct string concatenation with user input in SQL query",
      "tags": ["f-string", "concatenation", "direct-injection"]
    },
    {
      "id": "sqli_blind_045",
      "file": "vulnerable/blind/sqli_blind_045.py",
      "is_vulnerable": true,
      "category": "blind_sqli",
      "severity": "medium",
      "language": "python",
      "framework": "django",
      "database": "mysql",
      "cwe_id": "CWE-89",
      "description": "Blind SQL injection via boolean-based inference",
      "tags": ["boolean-blind", "timing-attack"]
    },
    {
      "id": "secure_param_001",
      "file": "secure/parameterized/secure_param_001.py",
      "is_vulnerable": false,
      "category": "secure_parameterized",
      "severity": null,
      "language": "python",
      "framework": "flask",
      "database": "postgresql",
      "cwe_id": null,
      "description": "Properly parameterized query using psycopg2",
      "tags": ["parameterized", "prepared-statement", "best-practice"]
    }
  ]
}
```

### 6.3 JSON Dataset File Format

**File:** `vulnerable_code/python_sqli.json`

```json
{
  "dataset_version": "1.0",
  "language": "python",
  "category_counts": {
    "classic_sqli": 50,
    "blind_sqli": 40,
    "time_based": 30,
    "union_based": 25,
    "error_based": 20,
    "second_order": 10
  },
  "total_samples": 175,
  "samples": [
    {
      "id": "py_classic_001",
      "category": "classic_sqli",
      "severity": "high",
      "framework": "flask",
      "database": "postgresql",
      "code": "from flask import request\nimport psycopg2\n\n@app.route('/user')\ndef get_user():\n    uid = request.args.get('id')\n    conn = psycopg2.connect('dbname=mydb')\n    cursor = conn.cursor()\n    query = f\"SELECT * FROM users WHERE id={uid}\"\n    cursor.execute(query)\n    return cursor.fetchone()",
      "vulnerability_line": 8,
      "description": "User input from request.args directly concatenated into SQL query using f-string",
      "cwe_id": "CWE-89",
      "owasp": "A03:2021-Injection",
      "tags": ["f-string", "flask", "request-args"],
      "remediation": "Use parameterized query: cursor.execute('SELECT * FROM users WHERE id=%s', (uid,))"
    },
    {
      "id": "py_classic_002",
      "category": "classic_sqli",
      "severity": "high",
      "code": "query = 'SELECT * FROM users WHERE name=' + user_input\nresult = db.execute(query)",
      "vulnerability_line": 1,
      "description": "Direct string concatenation with + operator",
      "cwe_id": "CWE-89",
      "tags": ["concatenation", "plus-operator"]
    }
  ]
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `dataset_version` | string | ✓ | Version of dataset format |
| `language` | string | ✓ | Programming language (python, javascript, java, php) |
| `category_counts` | object | ✓ | Count of samples per vulnerability category |
| `total_samples` | int | ✓ | Total number of samples in this file |
| `samples` | array | ✓ | Array of code samples |
| `samples[].id` | string | ✓ | Unique identifier |
| `samples[].category` | string | ✓ | Vulnerability category or "secure" |
| `samples[].severity` | string | ✓ (vuln) | low, medium, high, critical |
| `samples[].code` | string | ✓ | Complete code sample (use \n for newlines) |
| `samples[].vulnerability_line` | int | ✗ | Line number where vulnerability occurs |
| `samples[].description` | string | ✓ | Brief description of vulnerability or secure practice |
| `samples[].cwe_id` | string | ✗ | CWE identifier |
| `samples[].framework` | string | ✗ | Framework used (flask, django, express, etc.) |
| `samples[].database` | string | ✗ | Database type (postgresql, mysql, etc.) |
| `samples[].tags` | array | ✗ | Tags for categorization |
| `samples[].remediation` | string | ✗ | How to fix the vulnerability |

### 6.4 Alternative: Individual File Format

**Example Vulnerable Code:** `vulnerable/classic/sqli_classic_001.py`

```python
"""
Test Case: sqli_classic_001
Category: Classic SQL Injection
Severity: High
CWE: CWE-89

Description:
User input is directly concatenated into SQL query using f-string,
allowing arbitrary SQL execution.

Expected Detection:
- is_vulnerable: true
- vulnerability_type: classic_sqli
- severity: high
- location: line 10
"""

from flask import Flask, request
import psycopg2

app = Flask(__name__)

@app.route('/user/<user_id>')
def get_user(user_id):
    conn = psycopg2.connect("dbname=mydb")
    cursor = conn.cursor()
    # VULNERABLE: Direct concatenation
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()
```

**Example Secure Code:** `secure/parameterized/secure_param_001.py`

```python
"""
Test Case: secure_param_001
Category: Secure - Parameterized Query
Severity: N/A

Description:
Properly parameterized query using psycopg2's parameter substitution.
User input is safely escaped by the database driver.

Expected Detection:
- is_vulnerable: false
"""

from flask import Flask, request
import psycopg2

app = Flask(__name__)

@app.route('/user/<user_id>')
def get_user(user_id):
    conn = psycopg2.connect("dbname=mydb")
    cursor = conn.cursor()
    # SECURE: Parameterized query
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    return cursor.fetchone()
```

### 6.5 Category Definitions

| Category | Description | Difficulty | Sample Count |
|----------|-------------|------------|--------------|
| **classic_sqli** | Direct concatenation, obvious injection | Easy | 100 |
| **blind_sqli** | Boolean-based blind injection | Medium | 80 |
| **time_based** | Time-based blind injection | Medium | 60 |
| **union_based** | UNION-based injection | Medium | 50 |
| **error_based** | Error-based injection | Hard | 40 |
| **second_order** | Second-order SQL injection | Hard | 20 |
| **secure_parameterized** | Properly parameterized queries | N/A | 100 |
| **secure_orm** | ORM-based queries | N/A | 80 |
| **secure_validation** | Input validation + escaping | N/A | 70 |

---

## 7. Scoring Engine

### 7.1 Metrics Definition

#### 7.1.1 Primary Metrics

**Confusion Matrix:**

```
                    Predicted
                    Vuln    Safe
Actual  Vuln        TP      FN
        Safe        FP      TN
```

**Calculated Metrics:**

1. **True Positive Rate (Recall/Sensitivity):**
   ```
   TPR = TP / (TP + FN)
   ```
   Measures: How many actual vulnerabilities were detected?

2. **True Negative Rate (Specificity):**
   ```
   TNR = TN / (TN + FP)
   ```
   Measures: How many secure code samples were correctly identified as safe?

3. **Precision:**
   ```
   Precision = TP / (TP + FP)
   ```
   Measures: Of all flagged vulnerabilities, how many were real?

4. **F1 Score:**
   ```
   F1 = 2 * (Precision * Recall) / (Precision + Recall)
   ```
   Measures: Harmonic mean of precision and recall

5. **Accuracy:**
   ```
   Accuracy = (TP + TN) / (TP + TN + FP + FN)
   ```
   Measures: Overall correctness

#### 7.1.2 Severity Assessment

If Purple Agent provides severity scores, evaluate:

```python
severity_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}

# Only for correctly identified vulnerabilities (TP)
severity_accuracy = sum(
    1 for tp in true_positives
    if tp.predicted_severity == tp.ground_truth_severity
) / len(true_positives)

# Mean Absolute Error
severity_mae = sum(
    abs(severity_map[tp.predicted_severity] - severity_map[tp.ground_truth_severity])
    for tp in true_positives
) / len(true_positives)
```

#### 7.1.3 Category Breakdown

Calculate metrics per vulnerability type:

```python
for category in ["classic_sqli", "blind_sqli", "time_based", ...]:
    category_results = [r for r in results if r.ground_truth.category == category]
    category_metrics[category] = {
        "tpr": calculate_tpr(category_results),
        "precision": calculate_precision(category_results),
        "f1": calculate_f1(category_results),
        "sample_count": len(category_results)
    }
```

### 7.2 Scoring Output

**File:** Attached as A2A artifact

```json
{
  "assessment_id": "assessment_123",
  "timestamp": "2025-11-04T10:30:00Z",
  "purple_agent": "sql_detector_v1",
  "test_suite": "sql_injection_v1",
  "sample_size": 100,

  "overall_metrics": {
    "true_positives": 42,
    "true_negatives": 38,
    "false_positives": 5,
    "false_negatives": 15,
    "tpr": 0.737,
    "tnr": 0.884,
    "fpr": 0.116,
    "fnr": 0.263,
    "precision": 0.894,
    "recall": 0.737,
    "f1_score": 0.808,
    "accuracy": 0.800
  },

  "severity_assessment": {
    "severity_accuracy": 0.857,
    "severity_mae": 0.238
  },

  "category_breakdown": {
    "classic_sqli": {
      "sample_count": 20,
      "tp": 18,
      "fn": 2,
      "tpr": 0.900,
      "precision": 0.947,
      "f1": 0.923
    },
    "blind_sqli": {
      "sample_count": 16,
      "tp": 10,
      "fn": 6,
      "tpr": 0.625,
      "precision": 0.833,
      "f1": 0.714
    },
    "time_based": {
      "sample_count": 12,
      "tp": 8,
      "fn": 4,
      "tpr": 0.667,
      "precision": 0.800,
      "f1": 0.727
    },
    "secure_parameterized": {
      "sample_count": 25,
      "tn": 23,
      "fp": 2,
      "tnr": 0.920
    }
  },

  "ranking_score": 0.808,
  "rank_explanation": "Primary ranking metric is F1 score for fair balance between precision and recall"
}
```

### 7.3 Leaderboard Ranking

**Primary Metric:** **F1 Score**

**Rationale:**
- Balances precision (minimize false alarms) and recall (catch vulnerabilities)
- Single number for easy comparison
- Industry standard for imbalanced classification

**Tiebreaker Hierarchy:**
1. F1 Score (primary)
2. Precision (minimize false positives)
3. Recall (maximize vulnerability detection)
4. Average test completion time

---

## 8. Communication Protocol

### 8.1 A2A Message Structure

All communication follows **A2A Protocol** (Agent-to-Agent): https://a2a-protocol.org/

#### 8.1.1 Green → Purple: Test Case Submission

```json
POST https://purple-agent.example.com/tasks
Content-Type: application/json

{
  "message": {
    "role": "user",
    "parts": [
      {
        "text": {
          "text": "{\"test_id\":\"sqli_classic_001\",\"type\":\"code\",\"language\":\"python\",\"content\":\"def get_user(user_id):\\n    query = f'SELECT * FROM users WHERE id={user_id}'\\n    return db.execute(query)\"}"
        }
      }
    ]
  },
  "context_id": "assessment_123"
}
```

#### 8.1.2 Purple → Green: Progress Update

```json
{
  "task_id": "task_456",
  "state": "working",
  "message": {
    "role": "agent",
    "parts": [
      {
        "text": {
          "text": "Analyzing code for SQL injection patterns..."
        }
      }
    ]
  }
}
```

#### 8.1.3 Purple → Green: Final Report (Artifact)

```json
{
  "task_id": "task_456",
  "state": "completed",
  "artifacts": [
    {
      "name": "vulnerability_report",
      "parts": [
        {
          "text": {
            "text": "{\"test_id\":\"sqli_classic_001\",\"is_vulnerable\":true,\"vulnerability_type\":\"classic_sqli\",\"severity\":\"high\",\"confidence\":0.95,\"explanation\":\"User input directly concatenated into SQL query\"}"
          }
        }
      ]
    }
  ]
}
```

### 8.2 Error Handling

| Error Scenario | Green Agent Response | Scoring Impact |
|----------------|---------------------|----------------|
| Purple Agent timeout (>30s) | Mark as "no response" | Count as FN (missed vulnerability) |
| Invalid JSON response | Mark as "invalid format" | Count as FN |
| Missing required fields | Mark as "incomplete" | Count as FN |
| Purple Agent returns error | Retry once, then count as FN | Count as FN if retry fails |
| Purple Agent offline | Abort assessment | No score |

---

## 9. Deployment Architecture

### 9.1 Development Environment

```
Local Development
├── Green Agent (localhost:9009)
├── Purple Agent Baseline (localhost:9019)
├── Purple Agent LLM (localhost:9020)
└── Dataset (local filesystem)

Run command:
uv run agentbeats-run scenarios/security/scenario.toml
```

### 9.2 AgentBeats Platform Deployment

```
┌─────────────────────────────────────────────────┐
│            AgentBeats.org Platform              │
│  ┌───────────────────────────────────────────┐  │
│  │  Green Agent Registration                 │  │
│  │  - Agent Card URL: https://green.ex.com   │  │
│  │  - Exposed via Cloudflare Tunnel          │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
                     │
                     │ HTTPS
                     ▼
┌─────────────────────────────────────────────────┐
│      Cloudflare Tunnel (Public Endpoint)        │
│      https://green-agent-abc123.trycloudflare.com │
└────────────────┬────────────────────────────────┘
                 │
                 │ Tunnel
                 ▼
┌─────────────────────────────────────────────────┐
│      Local Development Machine                  │
│  ┌───────────────────────────────────────────┐  │
│  │ Green Agent (localhost:9009)              │  │
│  │ - SQLInjectionJudge                       │  │
│  │ - Dataset (local files)                   │  │
│  │ - Scoring Engine                          │  │
│  └───────────────────────────────────────────┘  │
│                                                  │
│  Environment:                                    │
│  - GOOGLE_API_KEY=<your-key>                    │
│  - Dataset: ./scenarios/security/datasets/      │
└─────────────────────────────────────────────────┘
```

**Setup Steps:**

1. **Install Cloudflare Tunnel:**
   ```bash
   brew install cloudflared
   ```

2. **Start Tunnel:**
   ```bash
   cloudflared tunnel --url http://127.0.0.1:9009
   # Copy the generated URL (e.g., https://abc-123.trycloudflare.com)
   ```

3. **Start Green Agent:**
   ```bash
   python scenarios/security/sql_injection_judge.py \
     --host 127.0.0.1 \
     --port 9009 \
     --card-url https://abc-123.trycloudflare.com
   ```

4. **Register on AgentBeats:**
   - Go to https://agentbeats.org
   - Register agent with URL: `https://abc-123.trycloudflare.com`
   - Set agent type: Green Agent
   - Set skills: SQL Injection Detection Benchmark

### 9.3 Purple Agent Deployment

Purple Agents (submitted by participants) can be deployed anywhere:
- Local machine with Cloudflare Tunnel
- Cloud hosting (AWS, GCP, Azure)
- Containers (Docker, Kubernetes)
- Serverless (Lambda, Cloud Functions)

**Only requirement:** Expose A2A-compliant HTTP endpoint

---

## 10. Implementation Roadmap

### Phase 1: MVP (Weeks 1-2)

**Deliverables:**
- [ ] Fix existing code issues (cyber_sentinel.py)
- [ ] Implement SQLInjectionJudge with basic evaluation loop
- [ ] Create minimal dataset (50 samples: 30 vulnerable, 20 secure)
- [ ] Implement DatasetManager (load, sample)
- [ ] Implement ScoringEngine (TPR, FPR, F1)
- [ ] Create baseline Purple Agent (rule-based)
- [ ] End-to-end test: Green → Purple → Scoring

### Phase 2: Full Dataset (Weeks 3-4)

**Deliverables:**
- [ ] Expand dataset to 500+ samples
- [ ] All 6 vulnerability categories
- [ ] All 3 secure code categories
- [ ] Metadata.json with full annotations
- [ ] LLM-based Purple Agent
- [ ] Hybrid Purple Agent

### Phase 3: Polish (Weeks 5-6)

**Deliverables:**
- [ ] Comprehensive documentation (all docs/)
- [ ] Test orchestration (parallel execution, timeouts)
- [ ] Report generation (markdown, JSON artifacts)
- [ ] Category breakdown metrics
- [ ] Local testing & validation
- [ ] Platform deployment (Cloudflare Tunnel)
- [ ] AgentBeats registration

### Phase 4: Submission (Week 7)

**Deliverables:**
- [ ] Final testing on AgentBeats platform
- [ ] Benchmark validation with community
- [ ] Performance optimization
- [ ] Cost estimation documentation
- [ ] Submit to AgentBeats Phase 1

---

**Document Version:** 1.0
**Last Updated:** November 4, 2025
