"""
Adaptive Test Planner for SQL Injection Detection Benchmark.

This module implements autonomous decision-making for adaptive testing:
- Identifies weak categories based on performance
- Allocates tests strategically to focus on weaknesses
- Progresses through testing phases (exploration → exploitation → validation)
- Determines when to terminate based on result stability
"""

from datetime import datetime
from typing import Any

from .models import (
    TestResult,
    TestPhase,
    TestPlan,
    TestAllocation,
    PerformanceAnalysis,
    AutonomousDecision,
    CategoryMetrics,
    EvaluationMetrics
)
from .scoring_engine import ScoringEngine


class AdaptiveTestPlanner:
    """
    Implements autonomous decision-making for adaptive testing.

    Makes rule-based decisions about test allocation, difficulty progression,
    and termination without requiring an LLM. Provides true "agency" through
    strategic, context-aware test selection.
    """

    def __init__(
        self,
        weak_threshold: float = 0.6,
        focus_percentage: float = 0.6,
        stability_threshold: float = 0.05,
        min_category_samples: int = 5
    ):
        """
        Initialize the adaptive test planner.

        Args:
            weak_threshold: F1 threshold below which a category is considered weak
            focus_percentage: Percentage of tests to allocate to weak categories
            stability_threshold: F1 change threshold for performance stability
            min_category_samples: Minimum samples per category per round
        """
        self.weak_threshold = weak_threshold
        self.focus_percentage = focus_percentage
        self.stability_threshold = stability_threshold
        self.min_category_samples = min_category_samples
        self.scoring_engine = ScoringEngine()
        self.decisions: list[AutonomousDecision] = []

    def analyze_performance(
        self,
        results: list[TestResult],
        previous_metrics: EvaluationMetrics | None = None
    ) -> PerformanceAnalysis:
        """
        Analyze purple agent's performance to guide adaptive decisions.

        Args:
            results: Test results to analyze
            previous_metrics: Metrics from previous round (for trend analysis)

        Returns:
            PerformanceAnalysis with insights for decision-making
        """
        overall_metrics = self.scoring_engine.calculate_metrics(results)
        category_metrics = self.scoring_engine.calculate_category_metrics(results)

        # Identify weak and strong categories
        weak_categories = self.scoring_engine.get_weak_categories(
            category_metrics,
            self.weak_threshold
        )
        strong_categories = self.scoring_engine.get_strong_categories(
            category_metrics,
            self.weak_threshold
        )

        # Determine performance trend
        trend = "stable"
        if previous_metrics:
            if self.scoring_engine.is_performance_stable(
                previous_metrics,
                overall_metrics,
                self.stability_threshold
            ):
                trend = "stable"
            else:
                f1_change = overall_metrics.f1_score - previous_metrics.f1_score
                trend = "improving" if f1_change > 0 else "declining"

        # Analyze confidence distribution
        confidence_analysis = self.scoring_engine.analyze_confidence_distribution(results)

        # Build category F1 mapping
        category_f1 = {cm.category: cm.metrics.f1_score for cm in category_metrics}

        return PerformanceAnalysis(
            overall_f1=overall_metrics.f1_score,
            category_f1=category_f1,
            weak_categories=weak_categories,
            strong_categories=strong_categories,
            performance_trend=trend,
            confidence_analysis=confidence_analysis
        )

    def decide_next_phase(
        self,
        current_phase: TestPhase,
        round_number: int,
        performance: PerformanceAnalysis,
        total_tests_executed: int,
        test_budget: int
    ) -> TestPhase:
        """
        AUTONOMOUS DECISION: Determine the next testing phase.

        Args:
            current_phase: Current testing phase
            round_number: Current round number
            performance: Performance analysis
            total_tests_executed: Tests executed so far
            test_budget: Total test budget

        Returns:
            Next testing phase
        """
        # Decision logic:
        # - Round 1: Always exploration
        # - If weak categories found: Move to exploitation
        # - If performance stable and budget allows: Move to validation
        # - Otherwise: Continue current phase

        if round_number == 1:
            next_phase = TestPhase.EXPLORATION
            reasoning = "First round: systematic exploration to establish baseline"
        elif current_phase == TestPhase.EXPLORATION and performance.weak_categories:
            next_phase = TestPhase.EXPLOITATION
            reasoning = f"Weak categories identified: {performance.weak_categories}. Moving to focused exploitation."
        elif current_phase == TestPhase.EXPLOITATION and performance.performance_trend == "stable":
            remaining_budget = test_budget - total_tests_executed
            if remaining_budget > 20:  # Need enough budget for validation
                next_phase = TestPhase.VALIDATION
                reasoning = "Performance stabilized. Moving to validation phase."
            else:
                next_phase = TestPhase.EXPLOITATION
                reasoning = "Performance stable but insufficient budget for validation."
        else:
            next_phase = current_phase
            reasoning = f"Continue {current_phase.value} phase"

        # Log the decision
        self._log_decision(
            decision_type="test_allocation",
            reasoning=reasoning,
            input_data={
                "current_phase": current_phase.value,
                "round_number": round_number,
                "weak_categories": performance.weak_categories,
                "performance_trend": performance.performance_trend,
                "total_tests_executed": total_tests_executed,
                "test_budget": test_budget
            },
            decision={"next_phase": next_phase.value},
            phase=current_phase
        )

        return next_phase

    def decide_next_batch(
        self,
        phase: TestPhase,
        batch_size: int,
        performance: PerformanceAnalysis,
        all_categories: list[str],
        tested_ids: set[str]
    ) -> TestPlan:
        """
        AUTONOMOUS DECISION: Decide test allocation for next batch.

        Args:
            phase: Current testing phase
            batch_size: Number of tests to allocate
            performance: Performance analysis
            all_categories: All available categories
            tested_ids: IDs of already-tested samples

        Returns:
            TestPlan with strategic test allocation
        """
        if phase == TestPhase.EXPLORATION:
            return self._plan_exploration(batch_size, all_categories)
        elif phase == TestPhase.EXPLOITATION:
            return self._plan_exploitation(
                batch_size,
                performance.weak_categories,
                all_categories
            )
        else:  # VALIDATION
            return self._plan_validation(batch_size, all_categories)

    def _plan_exploration(
        self,
        batch_size: int,
        all_categories: list[str]
    ) -> TestPlan:
        """
        Plan exploration phase: diverse sampling across all categories.

        Args:
            batch_size: Number of tests to allocate
            all_categories: All available categories

        Returns:
            TestPlan for exploration
        """
        # Distribute evenly across all categories
        categories_count = len(all_categories)
        if categories_count == 0:
            return TestPlan(
                phase=TestPhase.EXPLORATION,
                allocations=[],
                total_tests=0,
                rationale="No categories available"
            )

        base_per_category = max(self.min_category_samples, batch_size // categories_count)
        allocations = []

        for category in all_categories:
            allocations.append(
                TestAllocation(
                    category=category,
                    allocated_count=base_per_category,
                    reason="Exploration phase: diverse sampling"
                )
            )

        total_allocated = sum(a.allocated_count for a in allocations)

        # Log decision
        self._log_decision(
            decision_type="test_allocation",
            reasoning="Exploration phase: allocate tests evenly for comprehensive baseline",
            input_data={
                "batch_size": batch_size,
                "categories": all_categories,
                "per_category": base_per_category
            },
            decision={"allocations": [{"category": a.category, "count": a.allocated_count} for a in allocations]},
            phase=TestPhase.EXPLORATION
        )

        return TestPlan(
            phase=TestPhase.EXPLORATION,
            allocations=allocations,
            total_tests=total_allocated,
            rationale=f"Exploration: Distribute {total_allocated} tests evenly across {categories_count} categories"
        )

    def _plan_exploitation(
        self,
        batch_size: int,
        weak_categories: list[str],
        all_categories: list[str]
    ) -> TestPlan:
        """
        Plan exploitation phase: focus on weak categories.

        Args:
            batch_size: Number of tests to allocate
            weak_categories: Categories with low F1 scores
            all_categories: All available categories

        Returns:
            TestPlan for exploitation
        """
        allocations = []

        if not weak_categories:
            # No weak categories, distribute evenly
            return self._plan_exploration(batch_size, all_categories)

        # AUTONOMOUS DECISION: Allocate focus_percentage to weak areas
        focus_count = int(batch_size * self.focus_percentage)
        remaining_count = batch_size - focus_count

        # Distribute focus tests among weak categories
        per_weak_category = max(self.min_category_samples, focus_count // len(weak_categories))
        for category in weak_categories:
            allocations.append(
                TestAllocation(
                    category=category,
                    allocated_count=per_weak_category,
                    reason=f"Weak category (F1 < {self.weak_threshold}): focused testing"
                )
            )

        # Distribute remaining tests to other categories
        other_categories = [c for c in all_categories if c not in weak_categories]
        if other_categories:
            per_other_category = max(1, remaining_count // len(other_categories))
            for category in other_categories:
                allocations.append(
                    TestAllocation(
                        category=category,
                        allocated_count=per_other_category,
                        reason="Non-weak category: maintenance testing"
                    )
                )

        total_allocated = sum(a.allocated_count for a in allocations)

        # Log decision
        self._log_decision(
            decision_type="test_allocation",
            reasoning=f"Exploitation: Allocate {self.focus_percentage * 100}% of tests to weak categories",
            input_data={
                "batch_size": batch_size,
                "weak_categories": weak_categories,
                "focus_percentage": self.focus_percentage,
                "focus_count": focus_count
            },
            decision={
                "allocations": [{"category": a.category, "count": a.allocated_count} for a in allocations],
                "focused_on": weak_categories
            },
            phase=TestPhase.EXPLOITATION
        )

        return TestPlan(
            phase=TestPhase.EXPLOITATION,
            allocations=allocations,
            total_tests=total_allocated,
            rationale=f"Exploitation: Focus {focus_count} tests on weak categories {weak_categories}"
        )

    def _plan_validation(
        self,
        batch_size: int,
        all_categories: list[str]
    ) -> TestPlan:
        """
        Plan validation phase: final verification with untested samples.

        Args:
            batch_size: Number of tests to allocate
            all_categories: All available categories

        Returns:
            TestPlan for validation
        """
        # Distribute evenly, but only on untested samples
        categories_count = len(all_categories)
        if categories_count == 0:
            return TestPlan(
                phase=TestPhase.VALIDATION,
                allocations=[],
                total_tests=0,
                rationale="No categories available"
            )

        per_category = max(self.min_category_samples, batch_size // categories_count)
        allocations = []

        for category in all_categories:
            allocations.append(
                TestAllocation(
                    category=category,
                    allocated_count=per_category,
                    reason="Validation phase: verify with fresh samples"
                )
            )

        total_allocated = sum(a.allocated_count for a in allocations)

        # Log decision
        self._log_decision(
            decision_type="test_allocation",
            reasoning="Validation phase: test with untested samples to verify stability",
            input_data={
                "batch_size": batch_size,
                "categories": all_categories
            },
            decision={"allocations": [{"category": a.category, "count": a.allocated_count} for a in allocations]},
            phase=TestPhase.VALIDATION
        )

        return TestPlan(
            phase=TestPhase.VALIDATION,
            allocations=allocations,
            total_tests=total_allocated,
            rationale=f"Validation: {total_allocated} tests with fresh samples for final verification"
        )

    def should_terminate_early(
        self,
        round_number: int,
        max_rounds: int,
        total_tests_executed: int,
        test_budget: int,
        performance: PerformanceAnalysis,
        previous_performance: PerformanceAnalysis | None = None
    ) -> tuple[bool, str]:
        """
        AUTONOMOUS DECISION: Determine if evaluation should terminate early.

        Args:
            round_number: Current round number
            max_rounds: Maximum allowed rounds
            total_tests_executed: Tests executed so far
            test_budget: Total test budget
            performance: Current performance analysis
            previous_performance: Previous round's performance (for stability check)

        Returns:
            Tuple of (should_terminate, reason)
        """
        # Termination conditions:
        # 1. Reached max rounds
        if round_number >= max_rounds:
            reason = f"Maximum rounds ({max_rounds}) reached"
            self._log_termination_decision(True, reason, round_number, performance)
            return True, reason

        # 2. Exhausted test budget
        if total_tests_executed >= test_budget:
            reason = f"Test budget ({test_budget}) exhausted"
            self._log_termination_decision(True, reason, round_number, performance)
            return True, reason

        # 3. Performance is excellent and stable
        if previous_performance:
            if (performance.overall_f1 >= 0.9 and
                performance.performance_trend == "stable" and
                not performance.weak_categories):
                reason = "Excellent performance (F1 >= 0.9) achieved and stable with no weak categories"
                self._log_termination_decision(True, reason, round_number, performance)
                return True, reason

        # 4. No weak categories and performance stable for validation phase
        if (round_number >= 3 and
            not performance.weak_categories and
            performance.performance_trend == "stable"):
            reason = "No weak categories and performance stable after multiple rounds"
            self._log_termination_decision(True, reason, round_number, performance)
            return True, reason

        # Continue testing
        reason = "Continue testing: more rounds needed"
        self._log_termination_decision(False, reason, round_number, performance)
        return False, reason

    def _log_decision(
        self,
        decision_type: str,
        reasoning: str,
        input_data: dict[str, Any],
        decision: dict[str, Any],
        phase: TestPhase
    ) -> None:
        """
        Log an autonomous decision for transparency.

        Args:
            decision_type: Type of decision
            reasoning: Why this decision was made
            input_data: Data used for decision
            decision: The actual decision made
            phase: Testing phase when decision was made
        """
        autonomous_decision = AutonomousDecision(
            timestamp=datetime.now(),
            decision_type=decision_type,
            reasoning=reasoning,
            input_data=input_data,
            decision=decision,
            phase=phase
        )
        self.decisions.append(autonomous_decision)

    def _log_termination_decision(
        self,
        should_terminate: bool,
        reason: str,
        round_number: int,
        performance: PerformanceAnalysis
    ) -> None:
        """
        Log termination decision.

        Args:
            should_terminate: Whether to terminate
            reason: Reason for decision
            round_number: Current round
            performance: Current performance
        """
        self._log_decision(
            decision_type="early_termination",
            reasoning=reason,
            input_data={
                "round_number": round_number,
                "overall_f1": performance.overall_f1,
                "weak_categories": performance.weak_categories,
                "performance_trend": performance.performance_trend
            },
            decision={"terminate": should_terminate},
            phase=TestPhase.VALIDATION  # Default phase for termination
        )

    def get_decisions(self) -> list[AutonomousDecision]:
        """
        Get all autonomous decisions made during evaluation.

        Returns:
            List of all autonomous decisions
        """
        return self.decisions.copy()

    def reset(self) -> None:
        """Reset the planner state for a new evaluation."""
        self.decisions.clear()
