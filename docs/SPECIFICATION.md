# SecurityEvaluator - Technical Specification

**Project:** SQL Injection Detection Benchmark
**Version:** 1.0
**Date:** November 4, 2025

---

## Table of Contents

1. [API Specifications](#1-api-specifications)
2. [Data Models](#2-data-models)
3. [File Formats](#3-file-formats)
4. [Implementation Examples](#4-implementation-examples)
5. [Testing Requirements](#5-testing-requirements)
6. [Performance Requirements](#6-performance-requirements)

---

## 1. API Specifications

### 1.1 Green Agent API

**Endpoint:** Defined in scenario.toml (default: `http://127.0.0.1:9009`)

#### 1.1.1 Agent Card Endpoint

```http
GET /
Accept: application/json
```

**Response:**

```json
{
  "name": "SQL Injection Detection Benchmark",
  "description": "Evaluates AI agents' ability to detect SQL injection vulnerabilities in code",
  "url": "https://green-agent.example.com",
  "version": "1.0.0",
  "default_input_modes": ["text"],
  "default_output_modes": ["text"],
  "capabilities": {
    "streaming": true
  },
  "skills": [
    {
      "id": "sql_injection_benchmark",
      "name": "SQL Injection Detection Benchmark",
      "description": "Tests Purple Agent with 500+ SQL injection test cases and produces detailed metrics",
      "tags": ["security", "sql-injection", "benchmark", "evaluation"],
      "examples": [
        "{\"participants\": {\"sql_detector\": \"https://detector.example.com\"}, \"config\": {\"test_suite\": \"sql_injection_v1\", \"sample_size\": 100}}"
      ]
    }
  ]
}
```

#### 1.1.2 Start Assessment

```http
POST /tasks
Content-Type: application/json

{
  "message": {
    "role": "user",
    "parts": [
      {
        "text": {
          "text": "{\"participants\": {\"sql_detector\": \"https://detector.example.com\"}, \"config\": {\"test_suite\": \"sql_injection_v1\", \"sample_size\": 100}}"
        }
      }
    ]
  },
  "context_id": "assessment_123"
}
```

**Response:**

```json
{
  "task_id": "task_789",
  "state": "working",
  "message": {
    "role": "agent",
    "parts": [
      {
        "text": {
          "text": "Starting assessment. Loaded 100 test cases from sql_injection_v1 dataset."
        }
      }
    ]
  }
}
```

#### 1.1.3 Stream Progress Updates

Green Agent emits progress updates:

```json
{
  "task_id": "task_789",
  "state": "working",
  "message": {
    "role": "agent",
    "parts": [
      {
        "text": {
          "text": "Completed 25/100 tests. Current metrics: F1=0.82, Precision=0.89, Recall=0.76"
        }
      }
    ]
  }
}
```

#### 1.1.4 Final Artifact

```json
{
  "task_id": "task_789",
  "state": "completed",
  "artifacts": [
    {
      "name": "evaluation_results",
      "parts": [
        {
          "text": {
            "text": "{\"overall_metrics\": {\"f1_score\": 0.808, ...}, ...}"
          }
        }
      ]
    },
    {
      "name": "summary_report",
      "parts": [
        {
          "text": {
            "text": "# SQL Injection Detection Assessment\\n\\n## Overall Performance\\n..."
          }
        }
      ]
    }
  ]
}
```

### 1.2 Purple Agent API

**Endpoint:** Provided by participants (e.g., `https://detector.example.com`)

#### 1.2.1 Agent Card Endpoint

```http
GET /
Accept: application/json
```

**Response:**

```json
{
  "name": "My SQL Detector",
  "description": "AI-powered SQL injection vulnerability detector",
  "url": "https://detector.example.com",
  "version": "1.0.0",
  "default_input_modes": ["text"],
  "default_output_modes": ["text"],
  "capabilities": {
    "streaming": true
  },
  "skills": [
    {
      "id": "sql_injection_detection",
      "name": "SQL Injection Detection",
      "description": "Analyzes code for SQL injection vulnerabilities",
      "tags": ["security", "sql-injection", "sast"]
    }
  ]
}
```

#### 1.2.2 Analyze Test Case

```http
POST /tasks
Content-Type: application/json

{
  "message": {
    "role": "user",
    "parts": [
      {
        "text": {
          "text": "{\"test_id\": \"sqli_classic_001\", \"type\": \"code\", \"language\": \"python\", \"content\": \"def get_user(user_id):\\n    query = f'SELECT * FROM users WHERE id={user_id}'\\n    return db.execute(query)\"}"
        }
      }
    ]
  },
  "context_id": "assessment_123"
}
```

**Response (completed):**

```json
{
  "task_id": "task_999",
  "state": "completed",
  "artifacts": [
    {
      "name": "vulnerability_report",
      "parts": [
        {
          "text": {
            "text": "{\"test_id\": \"sqli_classic_001\", \"is_vulnerable\": true, \"vulnerability_type\": \"classic_sqli\", \"severity\": \"high\", \"confidence\": 0.95, \"explanation\": \"User input directly concatenated into SQL query using f-string\"}"
          }
        }
      ]
    }
  ]
}
```

---

## 2. Data Models

### 2.1 Core Models (Pydantic)

#### 2.1.1 Test Case Input

```python
from pydantic import BaseModel
from typing import Literal

class TestCaseInput(BaseModel):
    """Sent from Green Agent to Purple Agent"""
    test_id: str
    type: Literal["code", "http_request"]
    language: str | None = None  # For type="code": python, javascript, java, php
    content: str  # Code or HTTP request
    context: dict[str, str] | None = None  # Optional context (framework, database, etc.)

# Example
test_case = TestCaseInput(
    test_id="sqli_classic_001",
    type="code",
    language="python",
    content="def get_user(uid):\n    query = f'SELECT * FROM users WHERE id={uid}'\n    return db.execute(query)",
    context={"framework": "flask", "database": "postgresql"}
)
```

#### 2.1.2 Vulnerability Report Output

```python
from pydantic import BaseModel, Field
from typing import Literal

class VulnerabilityLocation(BaseModel):
    line: int | None = None
    column: int | None = None
    snippet: str | None = None

class VulnerabilityReport(BaseModel):
    """Returned from Purple Agent to Green Agent"""
    test_id: str
    is_vulnerable: bool
    vulnerability_type: Literal[
        "classic_sqli",
        "blind_sqli",
        "time_based",
        "union_based",
        "error_based",
        "second_order"
    ] | None = None  # Required if is_vulnerable=True
    severity: Literal["low", "medium", "high", "critical"] | None = None
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    location: VulnerabilityLocation | None = None
    explanation: str | None = None
    attack_vector: str | None = None
    remediation: str | None = None
    cwe_id: str | None = None
    owasp_category: str | None = None

# Example
report = VulnerabilityReport(
    test_id="sqli_classic_001",
    is_vulnerable=True,
    vulnerability_type="classic_sqli",
    severity="high",
    confidence=0.95,
    location=VulnerabilityLocation(line=2, snippet="query = f'SELECT...'"),
    explanation="User input concatenated directly into SQL query",
    remediation="Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id=%s', (uid,))"
)
```

#### 2.1.3 Test Case Metadata

```python
from pydantic import BaseModel

class TestCaseMetadata(BaseModel):
    """Ground truth for evaluation"""
    id: str
    file: str
    is_vulnerable: bool
    category: str  # classic_sqli, blind_sqli, secure_parameterized, etc.
    severity: Literal["low", "medium", "high", "critical"] | None = None
    language: str
    framework: str | None = None
    database: str | None = None
    cwe_id: str | None = None
    description: str
    tags: list[str] = []

# Example
metadata = TestCaseMetadata(
    id="sqli_classic_001",
    file="vulnerable/classic/sqli_classic_001.py",
    is_vulnerable=True,
    category="classic_sqli",
    severity="high",
    language="python",
    framework="flask",
    database="postgresql",
    cwe_id="CWE-89",
    description="Direct string concatenation with user input",
    tags=["f-string", "concatenation"]
)
```

#### 2.1.4 Evaluation Result

```python
from pydantic import BaseModel
from enum import Enum

class DetectionOutcome(str, Enum):
    TRUE_POSITIVE = "true_positive"
    TRUE_NEGATIVE = "true_negative"
    FALSE_POSITIVE = "false_positive"
    FALSE_NEGATIVE = "false_negative"
    NO_RESPONSE = "no_response"
    INVALID_RESPONSE = "invalid_response"

class TestResult(BaseModel):
    test_id: str
    ground_truth: TestCaseMetadata
    purple_response: VulnerabilityReport | None
    outcome: DetectionOutcome
    response_time_ms: float
    severity_match: bool | None = None  # True if severity matches ground truth

# Example
result = TestResult(
    test_id="sqli_classic_001",
    ground_truth=metadata,
    purple_response=report,
    outcome=DetectionOutcome.TRUE_POSITIVE,
    response_time_ms=1250.5,
    severity_match=True
)
```

#### 2.1.5 Evaluation Metrics

```python
from pydantic import BaseModel

class ConfusionMatrix(BaseModel):
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    no_response: int = 0
    invalid_response: int = 0

class OverallMetrics(BaseModel):
    confusion_matrix: ConfusionMatrix
    tpr: float  # True Positive Rate (Recall)
    tnr: float  # True Negative Rate
    fpr: float  # False Positive Rate
    fnr: float  # False Negative Rate
    precision: float
    recall: float
    f1_score: float
    accuracy: float

class CategoryMetrics(BaseModel):
    category: str
    sample_count: int
    tp: int = 0
    tn: int = 0
    fp: int = 0
    fn: int = 0
    tpr: float
    precision: float
    f1: float

class EvaluationMetrics(BaseModel):
    assessment_id: str
    timestamp: str
    purple_agent: str
    test_suite: str
    sample_size: int
    overall_metrics: OverallMetrics
    category_breakdown: dict[str, CategoryMetrics]
    severity_assessment: dict[str, float] | None = None
    ranking_score: float  # Primary ranking metric (F1 score)
    average_response_time_ms: float

# Example
metrics = EvaluationMetrics(
    assessment_id="assessment_123",
    timestamp="2025-11-04T10:30:00Z",
    purple_agent="my_sql_detector_v1",
    test_suite="sql_injection_v1",
    sample_size=100,
    overall_metrics=OverallMetrics(
        confusion_matrix=ConfusionMatrix(tp=42, tn=38, fp=5, fn=15),
        tpr=0.737,
        tnr=0.884,
        fpr=0.116,
        fnr=0.263,
        precision=0.894,
        recall=0.737,
        f1_score=0.808,
        accuracy=0.800
    ),
    category_breakdown={
        "classic_sqli": CategoryMetrics(
            category="classic_sqli",
            sample_count=20,
            tp=18,
            fn=2,
            tpr=0.900,
            precision=0.947,
            f1=0.923
        )
    },
    ranking_score=0.808,
    average_response_time_ms=1523.7
)
```

### 2.2 Adaptive Testing Models (NEW - For Agentic Behavior)

#### 2.2.1 Test Plan and Round Tracking

```python
from pydantic import BaseModel
from typing import Literal

class TestPlan(BaseModel):
    """Plan for a round of testing"""
    round_number: int
    test_count: int
    categories: dict[str, int]  # category -> number of tests
    strategy: Literal["explore", "exploit", "validate"]
    reasoning: str

class RoundResults(BaseModel):
    """Results from a single testing round"""
    round_number: int
    tests_conducted: int
    category_performance: dict[str, float]  # category -> F1 score
    weak_categories: list[str]
    timestamp: str

class PerformanceAnalysis(BaseModel):
    """Analysis of Purple Agent performance"""
    overall_f1: float
    category_f1: dict[str, float]
    weak_categories: list[str]  # F1 < threshold
    strong_categories: list[str]  # F1 > 0.8
    variance: float  # Consistency across categories
    summary: str  # Human-readable analysis
```

#### 2.2.2 Autonomous Decision Models

```python
class AutonomousDecision(BaseModel):
    """Record of an autonomous decision made by Green Agent"""
    decision_type: Literal[
        "test_allocation",
        "difficulty_escalation",
        "early_termination",
        "category_focus"
    ]
    timestamp: str
    round_number: int
    input_data: dict  # What data the decision was based on
    decision: dict  # What was decided
    reasoning: str  # Why this decision was made
    confidence: float | None = None  # Confidence in this decision

# Example
decision = AutonomousDecision(
    decision_type="test_allocation",
    timestamp="2025-11-04T10:30:00Z",
    round_number=2,
    input_data={
        "round1_f1": {"classic_sqli": 0.92, "blind_sqli": 0.45},
        "remaining_budget": 80
    },
    decision={
        "allocation": {"blind_sqli": 30, "time_based": 20, "others": 30}
    },
    reasoning="Detected significant weakness in blind_sqli (F1=0.45). Allocating 37.5% of remaining budget for deeper investigation.",
    confidence=0.95
)
```

#### 2.2.3 Adaptive Evaluation Metrics

```python
class AdaptiveEvaluationMetrics(EvaluationMetrics):
    """Extended metrics for adaptive testing"""
    # All fields from EvaluationMetrics, plus:
    evaluation_mode: Literal["fixed", "adaptive"]
    rounds_conducted: int
    decisions_made: list[AutonomousDecision]
    test_distribution: dict[str, int]  # category -> tests allocated
    efficiency_metrics: dict[str, float]  # Compared to fixed approach

# Example
adaptive_metrics = AdaptiveEvaluationMetrics(
    assessment_id="assessment_123",
    evaluation_mode="adaptive",
    rounds_conducted=4,
    sample_size=100,
    decisions_made=[decision1, decision2, decision3],
    test_distribution={
        "classic_sqli": 5,
        "blind_sqli": 38,
        "time_based": 26,
        "others": 31
    },
    efficiency_metrics={
        "tests_to_95_confidence": 100,  # vs 150 for fixed
        "efficiency_gain": 0.33
    },
    # ... standard EvaluationMetrics fields ...
)
```

---

### 2.3 Updated Models for cyber_sentinel_common.py

**Current (WRONG):**

```python
class ApplicationScore(BaseModel):
    emotional_appeal: float  # ❌ From debate example
    argument_clarity: float  # ❌ From debate example
    # ...
```

**Corrected:**

```python
from pydantic import BaseModel, Field
from typing import Literal

class SecurityScore(BaseModel):
    """Security evaluation scores (0.0 to 1.0)"""
    vulnerability_detection_rate: float = Field(ge=0.0, le=1.0)
    false_positive_rate: float = Field(ge=0.0, le=1.0)
    severity_accuracy: float = Field(ge=0.0, le=1.0)
    overall_f1_score: float = Field(ge=0.0, le=1.0)

class SecurityEvaluation(BaseModel):
    """Final evaluation output"""
    security_score: SecurityScore
    overall_risk_rating: Literal["excellent", "good", "fair", "poor"]
    ranking_score: float  # F1 score for leaderboard
    reason: str
    detailed_metrics: dict  # Full EvaluationMetrics as dict
```

---

## 3. File Formats

### 3.1 Dataset Metadata (metadata.json)

**Location:** `scenarios/security/datasets/sql_injection/metadata.json`

```json
{
  "dataset_version": "1.0",
  "created": "2025-11-04",
  "last_updated": "2025-11-04",
  "total_samples": 600,
  "vulnerable_samples": 350,
  "secure_samples": 250,
  "languages": ["python", "javascript", "java", "php"],
  "frameworks": ["flask", "django", "express", "spring", "laravel"],
  "databases": ["postgresql", "mysql", "sqlite", "mssql"],
  "categories": {
    "vulnerable": {
      "classic_sqli": 100,
      "blind_sqli": 80,
      "time_based": 60,
      "union_based": 50,
      "error_based": 40,
      "second_order": 20
    },
    "secure": {
      "parameterized": 100,
      "orm": 80,
      "input_validation": 70
    }
  },
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
    }
  ]
}
```

### 3.2 Test Case File Format

**Example:** `vulnerable/classic/sqli_classic_001.py`

```python
"""
Test Case: sqli_classic_001
Category: Classic SQL Injection
Severity: High
CWE: CWE-89
Language: Python
Framework: Flask
Database: PostgreSQL

Description:
User input is directly concatenated into SQL query using f-string,
allowing arbitrary SQL execution.

Expected Detection:
- is_vulnerable: true
- vulnerability_type: classic_sqli
- severity: high
- location: line 10

Tags: f-string, concatenation, direct-injection
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

**File Naming Convention:**

```
{category}_{subcategory}_{number}.{extension}

Examples:
sqli_classic_001.py
sqli_blind_045.py
sqli_time_023.py
secure_param_001.py
secure_orm_012.py
```

### 3.3 Scenario Configuration (scenario.toml)

**Location:** `scenarios/security/scenario.toml`

```toml
[sql_injection_judge]
endpoint = "http://127.0.0.1:9009"
cmd = "python scenarios/security/sql_injection_judge.py --host 127.0.0.1 --port 9009"

# Optional: Baseline purple agent for testing
[baseline_detector]
role = "sql_detector"
endpoint = "http://127.0.0.1:9019"
cmd = "python purple_agents/baseline/sql_detector.py --host 127.0.0.1 --port 9019"

[[config]]
test_suite = "sql_injection_v1"
sample_size = 100  # or "all" for full dataset
timeout_seconds = 30
max_concurrent_tests = 10
categories = ["all"]  # or ["classic", "blind", "time_based"]
random_seed = 42  # For reproducible sampling
```

---

## 4. Implementation Examples

### 4.1 Green Agent: Core Evaluation Loop

```python
# scenarios/security/sql_injection_judge.py

import asyncio
from a2a.server.tasks import TaskUpdater
from agentbeats.green_executor import GreenAgent
from agentbeats.models import EvalRequest

class SQLInjectionJudge(GreenAgent):
    def __init__(self):
        self._required_config_keys = ["test_suite"]
        self._dataset_manager = DatasetManager()
        self._scoring_engine = ScoringEngine()
        self._test_orchestrator = TestOrchestrator()

    async def run_eval(self, req: EvalRequest, updater: TaskUpdater) -> None:
        # 1. Load test suite
        test_suite = req.config["test_suite"]
        sample_size = req.config.get("sample_size", "all")

        await updater.update_status(
            TaskState.working,
            new_agent_text_message(f"Loading test suite: {test_suite}")
        )

        test_cases = self._dataset_manager.load_and_sample(
            test_suite,
            sample_size
        )

        await updater.update_status(
            TaskState.working,
            new_agent_text_message(f"Loaded {len(test_cases)} test cases")
        )

        # 2. Get Purple Agent endpoint
        if "sql_detector" not in req.participants:
            raise ValueError("Missing required participant: sql_detector")

        detector_url = req.participants["sql_detector"]

        # 3. Run tests
        results = await self._test_orchestrator.run_tests(
            agent_url=detector_url,
            test_cases=test_cases,
            updater=updater
        )

        # 4. Calculate metrics
        await updater.update_status(
            TaskState.working,
            new_agent_text_message("Calculating metrics...")
        )

        metrics = self._scoring_engine.calculate_metrics(results)

        # 5. Generate report
        report_json = metrics.model_dump_json(indent=2)
        report_md = self._generate_markdown_report(metrics)

        await updater.add_artifact(
            parts=[Part(root=TextPart(text=report_json))],
            name="evaluation_results"
        )

        await updater.add_artifact(
            parts=[Part(root=TextPart(text=report_md))],
            name="summary_report"
        )
```

### 4.2 Purple Agent: Baseline (Rule-Based)

```python
# purple_agents/baseline/sql_detector.py

import re
from typing import Literal

class BaselineSQLDetector:
    """Simple rule-based SQL injection detector"""

    VULNERABLE_PATTERNS = [
        r"query\s*=\s*f['\"].*\{.*\}.*['\"]",  # f-string
        r"query\s*=\s*['\"].*['\"].\s*\+\s*",  # String concatenation
        r"\.format\(",  # .format() with SQL
        r"%\s*%\s*\(",  # Old-style formatting
    ]

    SAFE_PATTERNS = [
        r"cursor\.execute\(['\"].*['\"],\s*\(",  # Parameterized
        r"\.filter\(",  # ORM
        r"\.get\(",  # ORM
    ]

    def analyze(self, test_input: TestCaseInput) -> VulnerabilityReport:
        content = test_input.content

        # Check for vulnerable patterns
        is_vulnerable = False
        vuln_type = None

        for pattern in self.VULNERABLE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                is_vulnerable = True
                vuln_type = "classic_sqli"
                break

        # Check for safe patterns (override)
        for pattern in self.SAFE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                is_vulnerable = False
                vuln_type = None
                break

        return VulnerabilityReport(
            test_id=test_input.test_id,
            is_vulnerable=is_vulnerable,
            vulnerability_type=vuln_type,
            severity="high" if is_vulnerable else None,
            confidence=0.7,
            explanation=(
                "Pattern-based detection: Found string concatenation in SQL query"
                if is_vulnerable else "No vulnerable patterns detected"
            )
        )
```

### 4.3 Purple Agent: LLM-Based

```python
# purple_agents/llm_based/sql_detector.py

from google import genai

class LLMSQLDetector:
    """LLM-powered SQL injection detector"""

    def __init__(self):
        self._client = genai.Client()

    async def analyze(self, test_input: TestCaseInput) -> VulnerabilityReport:
        system_prompt = """
        You are an expert security analyst specializing in SQL injection detection.
        Analyze the provided code and determine if it contains SQL injection vulnerabilities.

        Look for:
        - Direct string concatenation with user input
        - Lack of parameterized queries
        - Unsafe use of string formatting (f-strings, .format(), %)
        - Missing input validation

        Safe patterns:
        - Parameterized queries (cursor.execute with placeholders)
        - ORM usage (SQLAlchemy, Django ORM)
        - Proper input validation + parameterization
        """

        user_prompt = f"""
        Analyze this {test_input.language} code for SQL injection:

        ```{test_input.language}
        {test_input.content}
        ```

        Return a structured analysis.
        """

        response = self._client.models.generate_content(
            model="gemini-2.0-flash-exp",
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=VulnerabilityReport,
            ),
            contents=user_prompt,
        )

        return response.parsed
```

### 4.4 Dataset Manager (JSON Format)

```python
# scenarios/security/dataset_manager.py

import json
from pathlib import Path
from typing import List, Literal
from pydantic import BaseModel

class CodeSample(BaseModel):
    """Single code sample from JSON dataset"""
    id: str
    category: str
    severity: str | None
    language: str
    framework: str | None = None
    database: str | None = None
    code: str
    vulnerability_line: int | None = None
    description: str
    cwe_id: str | None = None
    tags: List[str] = []
    remediation: str | None = None

class DatasetManager:
    def __init__(self, dataset_path: str = "scenarios/security/datasets/sql_injection"):
        self.dataset_path = Path(dataset_path)
        self.vulnerable_samples: List[CodeSample] = []
        self.secure_samples: List[CodeSample] = []

    def load_dataset(self) -> None:
        """Load all JSON datasets"""
        # Load vulnerable samples
        vuln_dir = self.dataset_path / "vulnerable_code"
        for json_file in vuln_dir.glob("*.json"):
            with open(json_file) as f:
                data = json.load(f)
                for sample_data in data["samples"]:
                    sample_data["language"] = data["language"]
                    sample = CodeSample(**sample_data)
                    self.vulnerable_samples.append(sample)

        # Load secure samples
        secure_dir = self.dataset_path / "secure_code"
        for json_file in secure_dir.glob("*.json"):
            with open(json_file) as f:
                data = json.load(f)
                for sample_data in data["samples"]:
                    sample_data["language"] = data["language"]
                    sample_data["category"] = "secure"
                    sample_data["severity"] = None
                    sample = CodeSample(**sample_data)
                    self.secure_samples.append(sample)

    def sample(
        self,
        n: int | Literal["all"] = 100,
        categories: List[str] | None = None,
        random_seed: int = 42
    ) -> List[CodeSample]:
        """
        Sample n test cases from dataset

        Returns:
            List of CodeSample objects
        """
        import random
        random.seed(random_seed)

        # Filter by category if specified
        available_vuln = self.vulnerable_samples
        if categories and "all" not in categories:
            available_vuln = [s for s in available_vuln if s.category in categories]

        # Balance vulnerable and secure samples (60/40 split)
        if n == "all":
            n_vuln = len(available_vuln)
            n_secure = len(self.secure_samples)
        else:
            n_vuln = int(n * 0.6)
            n_secure = n - n_vuln

        vuln_samples = random.sample(available_vuln, min(n_vuln, len(available_vuln)))
        secure_samples = random.sample(self.secure_samples, min(n_secure, len(self.secure_samples)))

        all_samples = vuln_samples + secure_samples
        random.shuffle(all_samples)
        return all_samples

    def get_statistics(self) -> dict:
        """Return dataset statistics"""
        from collections import Counter

        vuln_categories = Counter(s.category for s in self.vulnerable_samples)
        vuln_languages = Counter(s.language for s in self.vulnerable_samples)

        return {
            "total_samples": len(self.vulnerable_samples) + len(self.secure_samples),
            "vulnerable_samples": len(self.vulnerable_samples),
            "secure_samples": len(self.secure_samples),
            "categories": dict(vuln_categories),
            "languages": dict(vuln_languages)
        }
```

**Benefits over individual file loading:**
- ✅ Loads 8 JSON files vs 600+ individual files (75x faster I/O)
- ✅ All samples in memory for fast sampling
- ✅ Pydantic validation ensures consistent schema
- ✅ Easy to extend with new fields

### 4.5 Scoring Engine

```python
# scenarios/security/scoring_engine.py

from typing import List
from collections import Counter

class ScoringEngine:
    def calculate_metrics(self, results: List[TestResult]) -> EvaluationMetrics:
        # Count outcomes
        outcomes = Counter(r.outcome for r in results)

        tp = outcomes[DetectionOutcome.TRUE_POSITIVE]
        tn = outcomes[DetectionOutcome.TRUE_NEGATIVE]
        fp = outcomes[DetectionOutcome.FALSE_POSITIVE]
        fn = outcomes[DetectionOutcome.FALSE_NEGATIVE]
        no_response = outcomes[DetectionOutcome.NO_RESPONSE]
        invalid = outcomes[DetectionOutcome.INVALID_RESPONSE]

        # Calculate rates
        total_vulnerable = tp + fn
        total_safe = tn + fp

        tpr = tp / total_vulnerable if total_vulnerable > 0 else 0.0
        tnr = tn / total_safe if total_safe > 0 else 0.0
        fpr = fp / total_safe if total_safe > 0 else 0.0
        fnr = fn / total_vulnerable if total_vulnerable > 0 else 0.0

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tpr
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = (tp + tn) / len(results) if results else 0.0

        # Category breakdown
        category_breakdown = self._breakdown_by_category(results)

        # Average response time
        avg_time = sum(r.response_time_ms for r in results) / len(results) if results else 0.0

        return EvaluationMetrics(
            assessment_id="...",
            timestamp="...",
            purple_agent="...",
            test_suite="...",
            sample_size=len(results),
            overall_metrics=OverallMetrics(
                confusion_matrix=ConfusionMatrix(
                    true_positives=tp,
                    true_negatives=tn,
                    false_positives=fp,
                    false_negatives=fn,
                    no_response=no_response,
                    invalid_response=invalid
                ),
                tpr=tpr,
                tnr=tnr,
                fpr=fpr,
                fnr=fnr,
                precision=precision,
                recall=recall,
                f1_score=f1,
                accuracy=accuracy
            ),
            category_breakdown=category_breakdown,
            ranking_score=f1,
            average_response_time_ms=avg_time
        )

    def _breakdown_by_category(self, results: List[TestResult]) -> dict[str, CategoryMetrics]:
        from collections import defaultdict

        category_results = defaultdict(list)
        for result in results:
            category_results[result.ground_truth.category].append(result)

        breakdown = {}
        for category, cat_results in category_results.items():
            outcomes = Counter(r.outcome for r in cat_results)

            tp = outcomes[DetectionOutcome.TRUE_POSITIVE]
            tn = outcomes[DetectionOutcome.TRUE_NEGATIVE]
            fp = outcomes[DetectionOutcome.FALSE_POSITIVE]
            fn = outcomes[DetectionOutcome.FALSE_NEGATIVE]

            total_vulnerable = tp + fn
            tpr = tp / total_vulnerable if total_vulnerable > 0 else 0.0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            f1 = 2 * (precision * tpr) / (precision + tpr) if (precision + tpr) > 0 else 0.0

            breakdown[category] = CategoryMetrics(
                category=category,
                sample_count=len(cat_results),
                tp=tp,
                tn=tn,
                fp=fp,
                fn=fn,
                tpr=tpr,
                precision=precision,
                f1=f1
            )

        return breakdown
```

---

## 5. Testing Requirements

### 5.1 Unit Tests

**File:** `tests/test_scoring_engine.py`

```python
import pytest
from scenarios.security.scoring_engine import ScoringEngine
from scenarios.security.models import TestResult, DetectionOutcome

def test_perfect_score():
    """Test scoring with 100% accuracy"""
    results = [
        TestResult(
            test_id="test_1",
            ground_truth=TestCaseMetadata(is_vulnerable=True, ...),
            purple_response=VulnerabilityReport(is_vulnerable=True, ...),
            outcome=DetectionOutcome.TRUE_POSITIVE,
            response_time_ms=100.0
        ),
        TestResult(
            test_id="test_2",
            ground_truth=TestCaseMetadata(is_vulnerable=False, ...),
            purple_response=VulnerabilityReport(is_vulnerable=False, ...),
            outcome=DetectionOutcome.TRUE_NEGATIVE,
            response_time_ms=100.0
        ),
    ]

    engine = ScoringEngine()
    metrics = engine.calculate_metrics(results)

    assert metrics.overall_metrics.f1_score == 1.0
    assert metrics.overall_metrics.accuracy == 1.0
    assert metrics.overall_metrics.precision == 1.0
    assert metrics.overall_metrics.recall == 1.0
```

### 5.2 Integration Tests

**File:** `tests/test_integration.py`

```python
import pytest
import asyncio
from scenarios.security.sql_injection_judge import SQLInjectionJudge

@pytest.mark.asyncio
async def test_end_to_end_evaluation():
    """Test full evaluation flow with mock purple agent"""

    # Start mock purple agent
    mock_purple = MockPurpleAgent(port=9999)
    await mock_purple.start()

    # Create evaluation request
    request = EvalRequest(
        participants={"sql_detector": "http://127.0.0.1:9999"},
        config={"test_suite": "sql_injection_v1", "sample_size": 10}
    )

    # Run evaluation
    judge = SQLInjectionJudge()
    updater = MockTaskUpdater()
    await judge.run_eval(request, updater)

    # Verify artifacts produced
    assert len(updater.artifacts) == 2
    assert "evaluation_results" in [a.name for a in updater.artifacts]

    await mock_purple.stop()
```

### 5.3 Validation Tests

**File:** `tests/test_dataset.py`

```python
def test_dataset_integrity():
    """Verify dataset metadata matches files"""
    manager = DatasetManager()
    manager.load_dataset()

    # Check all files exist
    for test_case in manager.test_cases.values():
        file_path = manager.dataset_path / test_case.file
        assert file_path.exists(), f"Missing file: {test_case.file}"

    # Check category distribution
    categories = [tc.category for tc in manager.test_cases.values()]
    assert len([c for c in categories if "sqli" in c]) >= 350
    assert len([c for c in categories if "secure" in c]) >= 250
```

---

## 6. Performance Requirements

### 6.1 Green Agent Performance

| Metric | Requirement | Target |
|--------|-------------|--------|
| **Test Execution** | 100 tests in < 5 minutes | < 3 minutes |
| **Full Dataset** | 500+ tests in < 30 minutes | < 20 minutes |
| **Concurrent Tests** | Support 10 parallel tests | 20 parallel |
| **Memory Usage** | < 500 MB (dataset + runtime) | < 300 MB |
| **Timeout Handling** | Graceful handling of slow agents | 30s per test |

### 6.2 Purple Agent Performance

**Recommendations for participants:**

| Metric | Minimum | Recommended |
|--------|---------|-------------|
| **Response Time** | < 30 seconds per test | < 5 seconds |
| **Uptime** | 95% during assessment | 99.9% |
| **Throughput** | 2 tests/second | 10 tests/second |
| **Memory** | < 1 GB | < 512 MB |

### 6.3 Cost Estimates

**Green Agent (LLM-as-Judge):**
- If using LLM for scoring: ~$0.50 per 100 test evaluations (Gemini Flash)
- Recommended: Rule-based scoring (free)

**Purple Agent (LLM-based):**
- Gemini Flash: ~$0.10 per 100 tests
- GPT-4 Turbo: ~$1.00 per 100 tests
- Baseline (rule-based): Free

---

**Document Version:** 1.0
**Last Updated:** November 4, 2025
