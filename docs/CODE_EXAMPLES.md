# Code Structure & Examples

**Version:** 1.0
**Date:** November 4, 2025
**Purpose:** Concrete code examples for all major components

---

## File Structure Overview

```
SecurityEvaluator/
├── scenarios/security/
│   ├── sql_injection_judge.py          # Main Green Agent (200 lines)
│   ├── adaptive_planner.py             # Autonomous decision-making (150 lines)
│   ├── dataset_manager.py              # Load JSON datasets (100 lines)
│   ├── scoring_engine.py               # Calculate metrics (150 lines)
│   ├── models.py                       # Pydantic models (200 lines)
│   ├── config.yaml                     # Configuration
│   ├── scenario.toml                   # AgentBeats config
│   └── datasets/sql_injection/
│       ├── metadata.json
│       ├── vulnerable_code/
│       │   └── python_sqli.json        # 175 samples
│       └── secure_code/
│           └── python_secure.json      # 125 samples
│
└── purple_agents/baseline/
    └── sql_detector.py                 # Reference Purple Agent (150 lines)
```

---

## 1. Main Green Agent: sql_injection_judge.py

**Purpose:** Entry point, orchestrates evaluation

```python
"""
SQL Injection Detection Benchmark (Green Agent)
Evaluates Purple Agents' ability to detect SQL injection vulnerabilities
"""

import argparse
import asyncio
import contextlib
import uvicorn
from dotenv import load_dotenv

load_dotenv()

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, TaskUpdater
from a2a.types import TaskState, Part, TextPart

from agentbeats.green_executor import GreenAgent, GreenExecutor
from agentbeats.models import EvalRequest, EvalResult

# Our components
from models import CodeSample, TestResult, DetectionOutcome, EvaluationMetrics
from dataset_manager import DatasetManager
from scoring_engine import ScoringEngine
from adaptive_planner import AdaptiveTestPlanner
from agent_card import sql_injection_agent_card


class SQLInjectionJudge(GreenAgent):
    """
    Green Agent for SQL Injection Detection Benchmark

    Modes:
    - fixed: Traditional test harness (all tests upfront)
    - adaptive: Agentic with autonomous decision-making
    """

    def __init__(self):
        self._required_config_keys = ["test_suite"]
        self._dataset_manager = DatasetManager()
        self._scoring_engine = ScoringEngine()

        # Load dataset once at initialization
        self._dataset_manager.load_dataset()
        print(f"Loaded dataset: {self._dataset_manager.get_statistics()}")

    def validate_request(self, request: EvalRequest) -> tuple[bool, str]:
        """Validate that request has required fields"""
        if "sql_detector" not in request.participants:
            return False, "Missing required participant: sql_detector"

        missing_config = set(self._required_config_keys) - set(request.config.keys())
        if missing_config:
            return False, f"Missing config keys: {missing_config}"

        return True, "ok"

    async def run_eval(self, req: EvalRequest, updater: TaskUpdater) -> None:
        """
        Main evaluation loop

        Supports two modes:
        - fixed: Traditional (all tests at once)
        - adaptive: Agentic (multi-round with decisions)
        """
        # Parse configuration
        mode = req.config.get("mode", "fixed")
        test_budget = req.config.get("test_budget", 100)

        await updater.update_status(
            TaskState.working,
            self._text_message(f"Starting {mode} evaluation with budget={test_budget}")
        )

        # Get Purple Agent URL
        purple_agent_url = str(req.participants["sql_detector"])

        # Run evaluation based on mode
        if mode == "adaptive":
            results = await self._run_adaptive_evaluation(
                purple_agent_url, test_budget, updater
            )
        else:
            results = await self._run_fixed_evaluation(
                purple_agent_url, test_budget, updater
            )

        # Calculate metrics
        await updater.update_status(
            TaskState.working,
            self._text_message("Calculating final metrics...")
        )

        metrics = self._scoring_engine.calculate_metrics(results)

        # Generate report
        await self._generate_report(metrics, updater)

    async def _run_fixed_evaluation(
        self,
        purple_agent_url: str,
        test_budget: int,
        updater: TaskUpdater
    ) -> list[TestResult]:
        """Traditional: Sample all tests upfront, run them"""

        # Sample tests (one-time)
        test_cases = self._dataset_manager.sample(n=test_budget)

        await updater.update_status(
            TaskState.working,
            self._text_message(f"Running {len(test_cases)} tests (fixed mode)")
        )

        # Run all tests
        results = []
        for i, test_case in enumerate(test_cases, 1):
            result = await self._run_single_test(purple_agent_url, test_case)
            results.append(result)

            if i % 10 == 0:
                await updater.update_status(
                    TaskState.working,
                    self._text_message(f"Completed {i}/{len(test_cases)} tests")
                )

        return results

    async def _run_adaptive_evaluation(
        self,
        purple_agent_url: str,
        test_budget: int,
        updater: TaskUpdater
    ) -> list[TestResult]:
        """
        Adaptive: Multi-round testing with autonomous decisions

        Round 1: Exploration (20% of budget)
        Round 2+: Exploitation (focus on weak areas)
        Final Round: Validation
        """

        planner = AdaptiveTestPlanner(test_budget=test_budget)
        all_results = []
        round_num = 0

        # Round 1: Initial exploration
        round_num += 1
        initial_plan = planner.create_initial_plan()

        await updater.update_status(
            TaskState.working,
            self._text_message(
                f"Round {round_num}: Exploration with {initial_plan.test_count} diverse tests"
            )
        )

        # Sample and run tests
        test_cases = self._dataset_manager.sample(
            n=initial_plan.test_count,
            categories=list(initial_plan.categories.keys())
        )

        round_results = await self._run_test_batch(
            purple_agent_url, test_cases, updater, round_num
        )
        all_results.extend(round_results)

        # Adaptive rounds
        while planner.has_budget_remaining():
            # 🤖 AUTONOMOUS DECISION: What to test next?
            next_plan = planner.decide_next_batch(all_results)

            if not next_plan:
                # 🤖 AUTONOMOUS DECISION: Stop early
                await updater.update_status(
                    TaskState.working,
                    self._text_message(
                        f"🤖 Stopping early: Results stable at {len(all_results)} tests"
                    )
                )
                break

            round_num += 1

            # Log autonomous decision
            await updater.update_status(
                TaskState.working,
                self._text_message(
                    f"Round {round_num}: {next_plan.strategy} - {next_plan.reasoning}"
                )
            )

            # Sample targeted tests
            test_cases = self._dataset_manager.sample(
                n=next_plan.test_count,
                categories=list(next_plan.categories.keys())
            )

            round_results = await self._run_test_batch(
                purple_agent_url, test_cases, updater, round_num
            )
            all_results.extend(round_results)

        return all_results

    async def _run_test_batch(
        self,
        purple_agent_url: str,
        test_cases: list[CodeSample],
        updater: TaskUpdater,
        round_num: int
    ) -> list[TestResult]:
        """Run a batch of tests"""
        results = []

        for i, test_case in enumerate(test_cases, 1):
            result = await self._run_single_test(purple_agent_url, test_case)
            results.append(result)

            if i % 5 == 0:
                current_f1 = self._scoring_engine.calculate_f1(results)
                await updater.update_status(
                    TaskState.working,
                    self._text_message(
                        f"Round {round_num}: {i}/{len(test_cases)} tests, F1={current_f1:.3f}"
                    )
                )

        return results

    async def _run_single_test(
        self,
        purple_agent_url: str,
        test_case: CodeSample
    ) -> TestResult:
        """
        Send test case to Purple Agent and evaluate response

        Returns TestResult with outcome (TP/TN/FP/FN)
        """
        import aiohttp
        import time

        start_time = time.time()

        # Prepare request
        test_input = {
            "test_id": test_case.id,
            "type": "code",
            "language": test_case.language,
            "content": test_case.code,
            "context": {
                "framework": test_case.framework,
                "database": test_case.database
            }
        }

        try:
            # Send to Purple Agent (A2A protocol)
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{purple_agent_url}/tasks",
                    json={"message": {"role": "user", "parts": [{"text": {"text": str(test_input)}}]}},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status != 200:
                        return self._create_error_result(test_case, "HTTP error")

                    response_data = await resp.json()

            # Parse response
            purple_response = self._parse_purple_response(response_data)

            # Determine outcome
            outcome = self._determine_outcome(test_case, purple_response)

            response_time = (time.time() - start_time) * 1000  # ms

            return TestResult(
                test_id=test_case.id,
                ground_truth=test_case,
                purple_response=purple_response,
                outcome=outcome,
                response_time_ms=response_time
            )

        except asyncio.TimeoutError:
            return self._create_error_result(test_case, "timeout")
        except Exception as e:
            return self._create_error_result(test_case, f"error: {e}")

    def _determine_outcome(
        self,
        test_case: CodeSample,
        purple_response: dict
    ) -> DetectionOutcome:
        """
        Compare Purple Agent's response with ground truth

        Returns: TP, TN, FP, or FN
        """
        is_vulnerable_truth = (test_case.category != "secure")
        is_vulnerable_predicted = purple_response.get("is_vulnerable", False)

        if is_vulnerable_truth and is_vulnerable_predicted:
            return DetectionOutcome.TRUE_POSITIVE
        elif not is_vulnerable_truth and not is_vulnerable_predicted:
            return DetectionOutcome.TRUE_NEGATIVE
        elif not is_vulnerable_truth and is_vulnerable_predicted:
            return DetectionOutcome.FALSE_POSITIVE
        else:  # is_vulnerable_truth and not is_vulnerable_predicted
            return DetectionOutcome.FALSE_NEGATIVE

    async def _generate_report(
        self,
        metrics: EvaluationMetrics,
        updater: TaskUpdater
    ) -> None:
        """Generate and attach evaluation report as A2A artifacts"""

        # JSON artifact (full metrics)
        json_report = metrics.model_dump_json(indent=2)
        await updater.add_artifact(
            parts=[Part(root=TextPart(text=json_report))],
            name="evaluation_results"
        )

        # Markdown summary
        md_report = self._generate_markdown_report(metrics)
        await updater.add_artifact(
            parts=[Part(root=TextPart(text=md_report))],
            name="summary_report"
        )

    def _generate_markdown_report(self, metrics: EvaluationMetrics) -> str:
        """Generate human-readable markdown report"""

        report = f"""# SQL Injection Detection Evaluation

## Overall Performance

- **F1 Score:** {metrics.overall_metrics.f1_score:.3f}
- **Precision:** {metrics.overall_metrics.precision:.3f}
- **Recall:** {metrics.overall_metrics.recall:.3f}
- **Accuracy:** {metrics.overall_metrics.accuracy:.3f}

## Confusion Matrix

|              | Predicted Vuln | Predicted Safe |
|--------------|----------------|----------------|
| **Actual Vuln** | {metrics.overall_metrics.confusion_matrix.true_positives} (TP) | {metrics.overall_metrics.confusion_matrix.false_negatives} (FN) |
| **Actual Safe** | {metrics.overall_metrics.confusion_matrix.false_positives} (FP) | {metrics.overall_metrics.confusion_matrix.true_negatives} (TN) |

## Category Breakdown

"""
        for category, cat_metrics in metrics.category_breakdown.items():
            report += f"### {category}\n"
            report += f"- Tests: {cat_metrics.sample_count}\n"
            report += f"- F1: {cat_metrics.f1:.3f}\n"
            report += f"- Precision: {cat_metrics.precision:.3f}\n"
            report += f"- Recall: {cat_metrics.tpr:.3f}\n\n"

        return report

    def _text_message(self, text: str):
        """Helper to create text message"""
        from a2a.utils import new_agent_text_message
        return new_agent_text_message(text)

    def _parse_purple_response(self, response_data: dict) -> dict:
        """Parse Purple Agent's response"""
        # Extract from A2A artifact
        try:
            artifact = response_data.get("artifacts", [{}])[0]
            text = artifact.get("parts", [{}])[0].get("text", {}).get("text", "{}")
            import json
            return json.loads(text)
        except:
            return {}

    def _create_error_result(
        self,
        test_case: CodeSample,
        error_type: str
    ) -> TestResult:
        """Create error result for failed test"""
        return TestResult(
            test_id=test_case.id,
            ground_truth=test_case,
            purple_response=None,
            outcome=DetectionOutcome.NO_RESPONSE if error_type == "timeout" else DetectionOutcome.INVALID_RESPONSE,
            response_time_ms=30000.0 if error_type == "timeout" else 0.0
        )


async def main():
    parser = argparse.ArgumentParser(description="SQL Injection Detection Benchmark (Green Agent)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=9009, help="Port to bind")
    parser.add_argument("--card-url", type=str, help="Public URL for agent card")
    args = parser.parse_args()

    # Create Green Agent
    agent = SQLInjectionJudge()
    executor = GreenExecutor(agent)

    # Create agent card
    agent_card = sql_injection_agent_card(
        agent_name="SQL Injection Detection Benchmark",
        card_url=args.card_url or f"http://{args.host}:{args.port}/"
    )

    # Create A2A server
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
    )

    server = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    # Run server
    print(f"Starting SQL Injection Judge on {args.host}:{args.port}")
    uvicorn_config = uvicorn.Config(server.build(), host=args.host, port=args.port)
    uvicorn_server = uvicorn.Server(uvicorn_config)
    await uvicorn_server.serve()


if __name__ == '__main__':
    asyncio.run(main())
```

---

## 2. Adaptive Test Planner: adaptive_planner.py

**Purpose:** Autonomous decision-making engine

```python
"""
Adaptive Test Planner - Autonomous Decision-Making
Makes strategic decisions about test allocation
"""

from typing import List
from collections import Counter

from models import (
    TestResult, CodeSample, DetectionOutcome,
    TestPlan, RoundResults, PerformanceAnalysis
)


class AdaptiveTestPlanner:
    """
    Autonomous decision-making for test strategy

    Makes decisions about:
    - Which categories to focus on
    - How many tests per category
    - When to stop testing
    """

    def __init__(
        self,
        test_budget: int,
        weak_threshold: float = 0.6,
        focus_percentage: float = 0.6,
        initial_exploration: int = 20
    ):
        self.test_budget = test_budget
        self.weak_threshold = weak_threshold
        self.focus_percentage = focus_percentage
        self.initial_exploration = initial_exploration

        self.budget_used = 0
        self.round_history: List[RoundResults] = []

        # SQL injection categories
        self.all_categories = [
            "classic_sqli", "blind_sqli", "time_based",
            "union_based", "error_based", "second_order"
        ]

    def has_budget_remaining(self) -> bool:
        """Check if we have tests left to run"""
        return self.budget_used < self.test_budget

    def create_initial_plan(self) -> TestPlan:
        """
        Create plan for Round 1: Exploration

        Strategy: Sample evenly across all categories
        """
        tests_per_category = self.initial_exploration // len(self.all_categories)

        allocation = {
            cat: tests_per_category
            for cat in self.all_categories
        }

        self.budget_used += self.initial_exploration

        return TestPlan(
            round_number=1,
            test_count=self.initial_exploration,
            categories=allocation,
            strategy="explore",
            reasoning="Initial exploration: sampling evenly across all categories to identify strengths/weaknesses"
        )

    def decide_next_batch(
        self,
        current_results: List[TestResult]
    ) -> TestPlan | None:
        """
        🤖 AUTONOMOUS DECISION: Decide what to test next

        Steps:
        1. Analyze current performance
        2. Identify weak categories
        3. Calculate strategic allocation
        4. Return test plan

        Returns None if testing should stop
        """

        # Step 1: Analyze performance
        analysis = self.analyze_performance(current_results)

        # Step 2: Check if we should stop early
        if self._should_stop_early(analysis, current_results):
            return None

        # Step 3: Identify weak categories
        weak_categories = analysis.weak_categories

        # Step 4: Calculate remaining budget
        remaining_budget = self.test_budget - self.budget_used

        if remaining_budget <= 0:
            return None

        # Step 5: Allocate budget strategically
        if weak_categories:
            # 🤖 DECISION: Focus on weak areas
            allocation, strategy, reasoning = self._allocate_exploit_phase(
                weak_categories, remaining_budget, analysis
            )
        else:
            # 🤖 DECISION: Balanced allocation
            allocation, strategy, reasoning = self._allocate_validation_phase(
                remaining_budget, analysis
            )

        test_count = sum(allocation.values())
        self.budget_used += test_count

        round_num = len(self.round_history) + 2  # +1 for initial, +1 for next

        return TestPlan(
            round_number=round_num,
            test_count=test_count,
            categories=allocation,
            strategy=strategy,
            reasoning=reasoning
        )

    def analyze_performance(
        self,
        results: List[TestResult]
    ) -> PerformanceAnalysis:
        """
        Analyze Purple Agent's performance

        Returns insights about strengths/weaknesses
        """
        # Calculate overall F1
        overall_f1 = self._calculate_f1(results)

        # Calculate per-category F1
        category_f1 = {}
        for category in self.all_categories:
            cat_results = [r for r in results if r.ground_truth.category == category]
            if cat_results:
                category_f1[category] = self._calculate_f1(cat_results)

        # 🤖 DECISION: Identify weak categories (F1 < threshold)
        weak_categories = [
            cat for cat, f1 in category_f1.items()
            if f1 < self.weak_threshold
        ]

        # Identify strong categories
        strong_categories = [
            cat for cat, f1 in category_f1.items()
            if f1 > 0.8
        ]

        # Calculate variance (consistency)
        if len(category_f1) > 1:
            f1_values = list(category_f1.values())
            mean_f1 = sum(f1_values) / len(f1_values)
            variance = sum((f1 - mean_f1) ** 2 for f1 in f1_values) / len(f1_values)
        else:
            variance = 0.0

        # Generate summary
        if weak_categories:
            summary = f"Weak areas detected: {', '.join(weak_categories)} (F1 < {self.weak_threshold})"
        elif strong_categories:
            summary = f"Strong performance across all categories (min F1: {min(category_f1.values()):.2f})"
        else:
            summary = "Moderate performance across all categories"

        return PerformanceAnalysis(
            overall_f1=overall_f1,
            category_f1=category_f1,
            weak_categories=weak_categories,
            strong_categories=strong_categories,
            variance=variance,
            summary=summary
        )

    def _allocate_exploit_phase(
        self,
        weak_categories: List[str],
        remaining_budget: int,
        analysis: PerformanceAnalysis
    ) -> tuple[dict[str, int], str, str]:
        """
        🤖 AUTONOMOUS DECISION: Exploitation phase

        Strategy: Focus heavily on weak areas
        """
        allocation = {}

        # Allocate focus_percentage to weak categories
        weak_budget = int(remaining_budget * self.focus_percentage)
        per_weak = weak_budget // len(weak_categories)

        for cat in weak_categories:
            allocation[cat] = per_weak

        # Distribute remainder to other categories
        other_budget = remaining_budget - weak_budget
        other_categories = [c for c in self.all_categories if c not in weak_categories]

        if other_categories:
            per_other = other_budget // len(other_categories)
            for cat in other_categories:
                allocation[cat] = per_other

        reasoning = (
            f"Detected weakness in {len(weak_categories)} categories: "
            f"{', '.join(weak_categories)}. "
            f"Allocating {int(self.focus_percentage*100)}% of tests to investigate these areas."
        )

        return allocation, "exploit", reasoning

    def _allocate_validation_phase(
        self,
        remaining_budget: int,
        analysis: PerformanceAnalysis
    ) -> tuple[dict[str, int], str, str]:
        """
        🤖 AUTONOMOUS DECISION: Validation phase

        Strategy: Balanced testing for final validation
        """
        per_category = remaining_budget // len(self.all_categories)

        allocation = {
            cat: per_category
            for cat in self.all_categories
        }

        reasoning = (
            f"Performance is balanced across categories (variance={analysis.variance:.2f}). "
            f"Running final validation with uniform distribution."
        )

        return allocation, "validate", reasoning

    def _should_stop_early(
        self,
        analysis: PerformanceAnalysis,
        results: List[TestResult]
    ) -> bool:
        """
        🤖 AUTONOMOUS DECISION: Should we stop testing early?

        Criteria:
        - Results are stable (low variance in recent tests)
        - All categories have minimum coverage
        - Budget is mostly used
        """
        # Need at least 50 tests before considering early stop
        if len(results) < 50:
            return False

        # Check result stability (last 20 tests)
        last_20 = results[-20:]
        last_20_f1 = self._calculate_f1(last_20)

        previous_20 = results[-40:-20] if len(results) >= 40 else results[:-20]
        previous_f1 = self._calculate_f1(previous_20)

        stability = abs(last_20_f1 - previous_f1)

        # Check category coverage
        category_counts = Counter(r.ground_truth.category for r in results)
        min_coverage = min(category_counts.values()) if category_counts else 0

        # 🤖 DECISION: Stop if results are stable and coverage is sufficient
        if stability < 0.02 and min_coverage >= 8:
            return True

        return False

    def _calculate_f1(self, results: List[TestResult]) -> float:
        """Calculate F1 score from results"""
        if not results:
            return 0.0

        tp = sum(1 for r in results if r.outcome == DetectionOutcome.TRUE_POSITIVE)
        fp = sum(1 for r in results if r.outcome == DetectionOutcome.FALSE_POSITIVE)
        fn = sum(1 for r in results if r.outcome == DetectionOutcome.FALSE_NEGATIVE)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        if precision + recall == 0:
            return 0.0

        return 2 * (precision * recall) / (precision + recall)
```

---

## 3. Dataset Manager: dataset_manager.py

**Purpose:** Load and sample JSON datasets

```python
"""
Dataset Manager - Load test cases from JSON files
"""

import json
from pathlib import Path
from typing import List, Literal
import random

from models import CodeSample


class DatasetManager:
    """
    Manages SQL injection test dataset

    Loads from JSON files (easy to manage)
    """

    def __init__(self, dataset_path: str = "scenarios/security/datasets/sql_injection"):
        self.dataset_path = Path(dataset_path)
        self.vulnerable_samples: List[CodeSample] = []
        self.secure_samples: List[CodeSample] = []
        self.is_loaded = False

    def load_dataset(self) -> None:
        """Load all JSON datasets from disk"""

        if self.is_loaded:
            return

        print(f"Loading dataset from {self.dataset_path}...")

        # Load vulnerable samples
        vuln_dir = self.dataset_path / "vulnerable_code"
        for json_file in vuln_dir.glob("*.json"):
            with open(json_file, 'r') as f:
                data = json.load(f)
                language = data["language"]

                for sample_data in data["samples"]:
                    # Add language from file-level metadata
                    sample_data["language"] = language

                    # Create CodeSample object
                    sample = CodeSample(**sample_data)
                    self.vulnerable_samples.append(sample)

        # Load secure samples
        secure_dir = self.dataset_path / "secure_code"
        for json_file in secure_dir.glob("*.json"):
            with open(json_file, 'r') as f:
                data = json.load(f)
                language = data["language"]

                for sample_data in data["samples"]:
                    sample_data["language"] = language
                    sample_data["category"] = "secure"  # Mark as secure
                    sample_data["severity"] = None

                    sample = CodeSample(**sample_data)
                    self.secure_samples.append(sample)

        self.is_loaded = True
        print(f"Loaded {len(self.vulnerable_samples)} vulnerable and {len(self.secure_samples)} secure samples")

    def sample(
        self,
        n: int | Literal["all"] = 100,
        categories: List[str] | None = None,
        random_seed: int | None = None
    ) -> List[CodeSample]:
        """
        Sample n test cases from dataset

        Args:
            n: Number of samples ("all" for everything)
            categories: Filter by categories (or None for all)
            random_seed: Random seed for reproducibility

        Returns:
            List of CodeSample objects
        """
        if random_seed is not None:
            random.seed(random_seed)

        # Filter vulnerable samples by category
        available_vuln = self.vulnerable_samples
        if categories and "all" not in categories:
            available_vuln = [
                s for s in available_vuln
                if s.category in categories
            ]

        # Determine sample sizes (60/40 split: vulnerable/secure)
        if n == "all":
            n_vuln = len(available_vuln)
            n_secure = len(self.secure_samples)
        else:
            n_vuln = int(n * 0.6)
            n_secure = n - n_vuln

        # Sample
        vuln_samples = random.sample(
            available_vuln,
            min(n_vuln, len(available_vuln))
        )

        secure_samples = random.sample(
            self.secure_samples,
            min(n_secure, len(self.secure_samples))
        )

        # Combine and shuffle
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

---

## 4. Scoring Engine: scoring_engine.py

**Purpose:** Calculate metrics (F1, Precision, Recall)

```python
"""
Scoring Engine - Calculate evaluation metrics
"""

from typing import List
from collections import Counter

from models import (
    TestResult, DetectionOutcome, EvaluationMetrics,
    OverallMetrics, ConfusionMatrix, CategoryMetrics
)


class ScoringEngine:
    """Calculate performance metrics from test results"""

    def calculate_metrics(self, results: List[TestResult]) -> EvaluationMetrics:
        """
        Calculate all evaluation metrics

        Returns comprehensive EvaluationMetrics
        """
        # Count outcomes
        outcomes = Counter(r.outcome for r in results)

        tp = outcomes[DetectionOutcome.TRUE_POSITIVE]
        tn = outcomes[DetectionOutcome.TRUE_NEGATIVE]
        fp = outcomes[DetectionOutcome.FALSE_POSITIVE]
        fn = outcomes[DetectionOutcome.FALSE_NEGATIVE]
        no_response = outcomes[DetectionOutcome.NO_RESPONSE]
        invalid = outcomes[DetectionOutcome.INVALID_RESPONSE]

        # Calculate rates
        total_vuln = tp + fn
        total_safe = tn + fp

        tpr = tp / total_vuln if total_vuln > 0 else 0.0  # Recall
        tnr = tn / total_safe if total_safe > 0 else 0.0
        fpr = fp / total_safe if total_safe > 0 else 0.0
        fnr = fn / total_vuln if total_vuln > 0 else 0.0

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tpr
        f1_score = (
            2 * (precision * recall) / (precision + recall)
            if (precision + recall) > 0 else 0.0
        )
        accuracy = (tp + tn) / len(results) if results else 0.0

        # Category breakdown
        category_breakdown = self._breakdown_by_category(results)

        # Average response time
        valid_times = [
            r.response_time_ms for r in results
            if r.outcome not in [DetectionOutcome.NO_RESPONSE, DetectionOutcome.INVALID_RESPONSE]
        ]
        avg_time = sum(valid_times) / len(valid_times) if valid_times else 0.0

        return EvaluationMetrics(
            assessment_id="",  # Will be set by Green Agent
            timestamp="",  # Will be set by Green Agent
            purple_agent="",  # Will be set by Green Agent
            test_suite="sql_injection_v1",
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
                f1_score=f1_score,
                accuracy=accuracy
            ),
            category_breakdown=category_breakdown,
            ranking_score=f1_score,  # Primary ranking metric
            average_response_time_ms=avg_time
        )

    def calculate_f1(self, results: List[TestResult]) -> float:
        """Quick F1 calculation (for adaptive planner)"""
        metrics = self.calculate_metrics(results)
        return metrics.overall_metrics.f1_score

    def _breakdown_by_category(
        self,
        results: List[TestResult]
    ) -> dict[str, CategoryMetrics]:
        """Calculate per-category metrics"""
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

            total_vuln = tp + fn
            tpr = tp / total_vuln if total_vuln > 0 else 0.0

            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            f1 = (
                2 * (precision * tpr) / (precision + tpr)
                if (precision + tpr) > 0 else 0.0
            )

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

## 5. Data Models: models.py

**Purpose:** Pydantic schemas for type safety

```python
"""
Data Models - Pydantic schemas for all data structures
"""

from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum


# ==================== Test Case Models ====================

class CodeSample(BaseModel):
    """Single code sample from JSON dataset"""
    id: str
    category: str  # classic_sqli, blind_sqli, time_based, secure, etc.
    severity: str | None = None  # low, medium, high, critical (or None for secure)
    language: str  # python, javascript, java, php
    framework: str | None = None  # flask, django, express, spring, laravel
    database: str | None = None  # postgresql, mysql, sqlite, mssql
    code: str  # The actual code sample
    vulnerability_line: int | None = None  # Line number of vulnerability
    description: str  # Brief description
    cwe_id: str | None = None  # CWE-89, etc.
    tags: list[str] = []  # Additional tags
    remediation: str | None = None  # How to fix


# ==================== Detection Results ====================

class DetectionOutcome(str, Enum):
    """Possible outcomes of vulnerability detection"""
    TRUE_POSITIVE = "true_positive"    # Correctly identified vulnerability
    TRUE_NEGATIVE = "true_negative"    # Correctly identified secure code
    FALSE_POSITIVE = "false_positive"  # False alarm
    FALSE_NEGATIVE = "false_negative"  # Missed vulnerability
    NO_RESPONSE = "no_response"        # Timeout
    INVALID_RESPONSE = "invalid_response"  # Bad format


class TestResult(BaseModel):
    """Result of a single test"""
    test_id: str
    ground_truth: CodeSample
    purple_response: dict | None  # Purple Agent's response
    outcome: DetectionOutcome
    response_time_ms: float
    severity_match: bool | None = None  # True if severity matches


# ==================== Metrics Models ====================

class ConfusionMatrix(BaseModel):
    """Confusion matrix counts"""
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    no_response: int = 0
    invalid_response: int = 0


class OverallMetrics(BaseModel):
    """Overall performance metrics"""
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
    """Per-category performance"""
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
    """Complete evaluation results"""
    assessment_id: str
    timestamp: str
    purple_agent: str
    test_suite: str
    sample_size: int
    overall_metrics: OverallMetrics
    category_breakdown: dict[str, CategoryMetrics]
    ranking_score: float  # F1 score (primary ranking metric)
    average_response_time_ms: float


# ==================== Adaptive Testing Models ====================

class TestPlan(BaseModel):
    """Plan for a round of testing"""
    round_number: int
    test_count: int
    categories: dict[str, int]  # category -> number of tests
    strategy: Literal["explore", "exploit", "validate"]
    reasoning: str  # Why this allocation?


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

---

## 6. Purple Agent (Baseline): purple_agents/baseline/sql_detector.py

**Purpose:** Reference implementation (rule-based)

```python
"""
Baseline SQL Injection Detector (Purple Agent)
Simple rule-based pattern matching
Expected F1: ~0.60
"""

import argparse
import asyncio
import uvicorn
import json
import re

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentCapabilities


class BaselineSQLDetector:
    """
    Simple rule-based SQL injection detector

    Uses regex patterns to detect common SQL injection vulnerabilities
    """

    # Vulnerable patterns (SQL injection indicators)
    VULNERABLE_PATTERNS = [
        r"query\s*=\s*f['\"].*\{.*\}.*['\"]",  # f-string: query = f"SELECT * FROM users WHERE id={uid}"
        r"['\"].*['\"].\s*\+\s*\w+",  # Concatenation: "SELECT * FROM users WHERE id=" + user_id
        r"\.format\([^\)]*\)",  # .format(): "SELECT * FROM users WHERE id={}".format(uid)
        r"%\s*%\s*\w+",  # Old-style formatting: "SELECT * FROM users WHERE id=%s" % uid
        r"execute\(['\"].*\+",  # Direct concatenation in execute
    ]

    # Safe patterns (override vulnerable detection)
    SAFE_PATTERNS = [
        r"cursor\.execute\(['\"][^'\"]*['\"],\s*\(",  # Parameterized: cursor.execute("...", (param,))
        r"\.filter\(",  # ORM filter: User.filter(id=user_id)
        r"\.get\(",  # ORM get: User.get(id=user_id)
        r"\.all\(\)",  # ORM all: User.all()
        r"prepared",  # Prepared statement keyword
    ]

    def analyze(self, test_input: dict) -> dict:
        """
        Analyze code for SQL injection

        Args:
            test_input: {"test_id": "...", "type": "code", "language": "python", "content": "..."}

        Returns:
            {"test_id": "...", "is_vulnerable": bool, "vulnerability_type": "...", ...}
        """
        test_id = test_input["test_id"]
        code = test_input["content"]

        # Check for safe patterns first (high confidence)
        for pattern in self.SAFE_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                return {
                    "test_id": test_id,
                    "is_vulnerable": False,
                    "vulnerability_type": None,
                    "severity": None,
                    "confidence": 0.8,
                    "explanation": "Code uses safe practices: parameterized queries or ORM detected"
                }

        # Check for vulnerable patterns
        for pattern in self.VULNERABLE_PATTERNS:
            match = re.search(pattern, code, re.IGNORECASE)
            if match:
                return {
                    "test_id": test_id,
                    "is_vulnerable": True,
                    "vulnerability_type": "classic_sqli",
                    "severity": "high",
                    "confidence": 0.7,
                    "explanation": f"Detected SQL injection pattern: {match.group(0)}",
                    "remediation": "Use parameterized queries instead of string concatenation"
                }

        # No patterns matched - assume safe (with low confidence)
        return {
            "test_id": test_id,
            "is_vulnerable": False,
            "vulnerability_type": None,
            "severity": None,
            "confidence": 0.5,
            "explanation": "No obvious SQL injection patterns detected (low confidence)"
        }


class BaselineAgent:
    """A2A Agent wrapper for baseline detector"""

    def __init__(self):
        self.detector = BaselineSQLDetector()

    async def process_task(self, task_input: dict) -> dict:
        """Process incoming A2A task"""
        # Extract test input from A2A message
        test_input = json.loads(task_input)

        # Run detection
        result = self.detector.analyze(test_input)

        return result


async def main():
    parser = argparse.ArgumentParser(description="Baseline SQL Detector (Purple Agent)")
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9019)
    parser.add_argument("--card-url", type=str, help="Public URL")
    args = parser.parse_args()

    agent = BaselineAgent()

    # Create agent card
    agent_card = AgentCard(
        name="Baseline SQL Injection Detector",
        description="Rule-based SQL injection detector (baseline)",
        url=args.card_url or f"http://{args.host}:{args.port}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[]
    )

    # Create simple request handler
    from a2a.server.agent_execution import AgentExecutor, RequestContext
    from a2a.server.events import EventQueue
    from a2a.server.tasks import TaskUpdater
    from a2a.types import Task, TaskState
    from a2a.utils import new_task, new_agent_text_message

    class SimpleExecutor(AgentExecutor):
        def __init__(self, agent):
            self.agent = agent

        async def execute(self, context: RequestContext, event_queue: EventQueue):
            # Get input text
            input_text = context.get_user_input()

            # Create task
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

            updater = TaskUpdater(event_queue, task.id, task.context_id)

            # Process
            result = await self.agent.process_task(input_text)

            # Return result as artifact
            from a2a.types import Part, TextPart
            await updater.add_artifact(
                parts=[Part(root=TextPart(text=json.dumps(result)))],
                name="vulnerability_report"
            )
            await updater.complete()

    executor = SimpleExecutor(agent)
    handler = DefaultRequestHandler(agent_executor=executor, task_store=InMemoryTaskStore())

    server = A2AStarletteApplication(agent_card=agent_card, http_handler=handler)

    print(f"Starting Baseline SQL Detector on {args.host}:{args.port}")
    uvicorn_config = uvicorn.Config(server.build(), host=args.host, port=args.port)
    uvicorn_server = uvicorn.Server(uvicorn_config)
    await uvicorn_server.serve()


if __name__ == '__main__':
    asyncio.run(main())
```

---

## 7. JSON Dataset Example: datasets/sql_injection/vulnerable_code/python_sqli.json

**Purpose:** Store test cases (easy to manage)

```json
{
  "dataset_version": "1.0",
  "language": "python",
  "description": "Python SQL injection test cases",
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
      "tags": ["f-string", "flask", "request-args"],
      "remediation": "Use parameterized query: cursor.execute('SELECT * FROM users WHERE id=%s', (uid,))"
    },
    {
      "id": "py_classic_002",
      "category": "classic_sqli",
      "severity": "high",
      "framework": null,
      "database": "sqlite",
      "code": "import sqlite3\n\ndef search_products(keyword):\n    conn = sqlite3.connect('shop.db')\n    cursor = conn.cursor()\n    query = \"SELECT * FROM products WHERE name='\" + keyword + \"'\"\n    cursor.execute(query)\n    return cursor.fetchall()",
      "vulnerability_line": 6,
      "description": "Direct string concatenation with + operator",
      "cwe_id": "CWE-89",
      "tags": ["concatenation", "plus-operator", "sqlite"],
      "remediation": "Use parameterized query: cursor.execute('SELECT * FROM products WHERE name=?', (keyword,))"
    },
    {
      "id": "py_blind_001",
      "category": "blind_sqli",
      "severity": "medium",
      "framework": "django",
      "database": "mysql",
      "code": "from django.db import connection\n\ndef check_user_exists(username):\n    cursor = connection.cursor()\n    query = f\"SELECT COUNT(*) FROM users WHERE username='{username}'\"\n    cursor.execute(query)\n    result = cursor.fetchone()[0]\n    return result > 0",
      "vulnerability_line": 5,
      "description": "Boolean-based blind SQL injection - attacker can infer data based on TRUE/FALSE responses",
      "cwe_id": "CWE-89",
      "tags": ["blind-sqli", "boolean-based", "django"],
      "remediation": "Use Django ORM: User.objects.filter(username=username).exists()"
    }
  ]
}
```

---

## 8. Configuration Files

### config.yaml

**Purpose:** Easy-to-edit configuration

```yaml
# SQL Injection Detection Benchmark Configuration

# Evaluation mode
evaluation:
  mode: "adaptive"  # "fixed" or "adaptive"
  test_budget: 100  # Total number of tests to run
  timeout_seconds: 30  # Per-test timeout
  max_concurrent: 10  # Max parallel tests

# Adaptive testing parameters (only used if mode=adaptive)
adaptive:
  initial_exploration: 20  # Tests in round 1 (exploration)
  weak_threshold: 0.6  # F1 < 0.6 = weak category
  focus_percentage: 0.6  # 60% of remaining tests on weak areas
  stability_threshold: 0.95  # Early stopping if results stable

# Dataset configuration
dataset:
  path: "scenarios/security/datasets/sql_injection"
  languages: ["python", "javascript", "java", "php"]
  categories:
    - classic_sqli
    - blind_sqli
    - time_based
    - union_based
    - error_based
    - second_order

# Scoring configuration
scoring:
  primary_metric: "f1_score"  # Primary ranking metric
  severity_weighting: false  # Weight by severity?
  min_confidence: 0.0  # Minimum confidence threshold

# Logging
logging:
  level: "INFO"
  log_decisions: true  # Log autonomous decisions?
  log_file: "evaluation.log"
```

### scenario.toml

**Purpose:** AgentBeats integration

```toml
# AgentBeats Scenario Configuration

[sql_injection_judge]
endpoint = "http://127.0.0.1:9009"
cmd = "python scenarios/security/sql_injection_judge.py --host 127.0.0.1 --port 9009"

# Optional: Reference purple agent for testing
[baseline_detector]
role = "sql_detector"
endpoint = "http://127.0.0.1:9019"
cmd = "python purple_agents/baseline/sql_detector.py --host 127.0.0.1 --port 9019"

# Configuration passed to Green Agent
[[config]]
test_suite = "sql_injection_v1"
mode = "adaptive"
test_budget = 100
```

---

## 9. Agent Card: agent_card.py

**Purpose:** Describe Green Agent capabilities

```python
"""Agent card for SQL Injection Detection Benchmark"""

from a2a.types import AgentCard, AgentCapabilities, AgentSkill


def sql_injection_agent_card(agent_name: str, card_url: str) -> AgentCard:
    """Create agent card for Green Agent"""

    skill = AgentSkill(
        id='sql_injection_benchmark',
        name='SQL Injection Detection Benchmark',
        description='Evaluates Purple Agents on SQL injection detection with 600+ test cases. Supports adaptive testing with autonomous decision-making.',
        tags=['security', 'sql-injection', 'benchmark', 'evaluation', 'adaptive'],
        examples=[
            """
            {
              "participants": {
                "sql_detector": "https://my-detector.example.com"
              },
              "config": {
                "test_suite": "sql_injection_v1",
                "mode": "adaptive",
                "test_budget": 100
              }
            }
            """
        ]
    )

    return AgentCard(
        name=agent_name,
        description='SQL Injection Detection Benchmark - Evaluates AI agents ability to detect SQL injection vulnerabilities. Features adaptive testing with autonomous decision-making.',
        url=card_url,
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )
```

---

## 10. Running the System

### Start Green Agent

```bash
# Terminal 1: Start Green Agent
cd SecurityEvaluator
uv run python scenarios/security/sql_injection_judge.py --host 127.0.0.1 --port 9009
```

### Start Purple Agent (for testing)

```bash
# Terminal 2: Start Baseline Purple Agent
uv run python purple_agents/baseline/sql_detector.py --host 127.0.0.1 --port 9019
```

### Run Evaluation

```bash
# Terminal 3: Trigger evaluation
uv run agentbeats-run scenarios/security/scenario.toml
```

### Example Output

```
Starting SQL Injection Judge on 127.0.0.1:9009
Loaded dataset: {'total_samples': 600, 'vulnerable_samples': 350, 'secure_samples': 250}

[Assessment Request Received]
Mode: adaptive
Test Budget: 100

Round 1: Exploration with 20 diverse tests
Completed 20/20 tests, F1=0.68

🤖 AUTONOMOUS DECISION: Detected weakness in blind_sqli (F1=0.45) and time_based (F1=0.52)

Round 2: exploit - Allocating 60% of tests to weak categories
Completed 40/40 tests, F1=0.72

🤖 AUTONOMOUS DECISION: blind_sqli still weak (F1=0.48), drilling deeper

Round 3: exploit - 30 additional blind_sqli tests
Completed 30/30 tests, F1=0.74

Round 4: validate - Final validation with 10 tests
Completed 10/10 tests, F1=0.75

Final Metrics:
- F1 Score: 0.75
- Precision: 0.82
- Recall: 0.69
- Rounds: 4
- Autonomous Decisions: 3

Report generated at: evaluation_results.json
```

---

## Summary

### File Sizes (Estimated)

| File | Lines | Purpose |
|------|-------|---------|
| `sql_injection_judge.py` | 200 | Main Green Agent |
| `adaptive_planner.py` | 150 | Autonomous decisions |
| `dataset_manager.py` | 100 | Load JSON datasets |
| `scoring_engine.py` | 150 | Calculate metrics |
| `models.py` | 200 | Pydantic models |
| `sql_detector.py` (baseline) | 150 | Reference Purple Agent |
| `agent_card.py` | 40 | Agent card definition |
| `config.yaml` | 40 | Configuration |
| `scenario.toml` | 20 | AgentBeats config |
| **Total** | **~1,050 lines** | Core system |

### JSON Datasets

| File | Samples | Size |
|------|---------|------|
| `python_sqli.json` | 175 | ~50KB |
| `javascript_sqli.json` | 90 | ~30KB |
| `java_sqli.json` | 50 | ~20KB |
| `php_sqli.json` | 35 | ~15KB |
| `python_secure.json` | 125 | ~35KB |
| `javascript_secure.json` | 60 | ~20KB |
| `java_secure.json` | 40 | ~15KB |
| `php_secure.json` | 25 | ~10KB |
| **Total** | **600 samples** | **~195KB** |

**Key Points:**
- ✅ Total code: ~1,050 lines (very manageable)
- ✅ JSON datasets: 8 files, 600 samples
- ✅ Clean separation of concerns
- ✅ Type-safe with Pydantic
- ✅ Easy to test and maintain
- ✅ Autonomous decision-making built-in

---

**Document Version:** 1.0
**Last Updated:** November 4, 2025