"""
Data models for SQL Injection Detection Benchmark.

This module defines all Pydantic models used throughout the SecurityEvaluator system,
including code samples, test results, evaluation metrics, and adaptive testing structures.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Code Sample Models
# ============================================================================

class CodeSample(BaseModel):
    """Represents a code sample for SQL injection testing."""

    id: str = Field(..., description="Unique identifier for the code sample")
    category: str = Field(..., description="SQL injection category (e.g., 'classic_sqli', 'blind_sqli')")
    language: str = Field(..., description="Programming language (python, javascript, java, php, etc.)")
    code: str = Field(..., description="The actual code snippet")
    is_vulnerable: bool = Field(..., description="Ground truth: True if vulnerable, False if secure")
    severity: str | None = Field(None, description="Severity level if vulnerable (critical, high, medium, low)")
    cwe_id: str | None = Field(None, description="Common Weakness Enumeration ID (e.g., 'CWE-89')")
    description: str | None = Field(None, description="Human-readable description of the vulnerability")
    remediation: str | None = Field(None, description="How to fix the vulnerability")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('category')
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate category is a known SQL injection type."""
        valid_categories = {
            'classic_sqli', 'blind_sqli', 'union_based', 'error_based',
            'time_based', 'boolean_based', 'second_order', 'stored_procedure',
            'orm_injection', 'nosql_injection'
        }
        if v not in valid_categories:
            # Allow unknown categories but log a warning
            pass
        return v

    @field_validator('language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language is supported."""
        valid_languages = {'python', 'javascript', 'java', 'php', 'ruby', 'go', 'csharp', 'sql'}
        if v.lower() not in valid_languages:
            pass  # Allow unknown languages
        return v.lower()


# ============================================================================
# Detection and Result Models
# ============================================================================

class DetectionOutcome(str, Enum):
    """Enum for confusion matrix outcomes."""
    TRUE_POSITIVE = "true_positive"    # Correctly identified as vulnerable
    TRUE_NEGATIVE = "true_negative"    # Correctly identified as secure
    FALSE_POSITIVE = "false_positive"  # Incorrectly identified as vulnerable
    FALSE_NEGATIVE = "false_negative"  # Incorrectly identified as secure


class PurpleAgentResponse(BaseModel):
    """Response from a Purple Agent (security detector) for a single test case."""

    test_case_id: str = Field(..., description="ID of the code sample tested")
    is_vulnerable: bool = Field(..., description="Purple agent's determination: True if vulnerable detected")
    confidence: float = Field(0.5, ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)")
    vulnerability_type: str | None = Field(None, description="Type of vulnerability detected, if any")
    explanation: str | None = Field(None, description="Explanation of the detection")
    detected_patterns: list[str] = Field(default_factory=list, description="Patterns that triggered detection")
    line_numbers: list[int] = Field(default_factory=list, description="Line numbers where issues found")
    severity: str | None = Field(None, description="Assessed severity (critical, high, medium, low)")
    execution_time_ms: float | None = Field(None, description="Time taken to analyze in milliseconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional response data")


class TestResult(BaseModel):
    """Result of testing a single code sample."""

    test_case_id: str = Field(..., description="ID of the code sample")
    ground_truth: bool = Field(..., description="Actual vulnerability status")
    predicted: bool = Field(..., description="Purple agent's prediction")
    outcome: DetectionOutcome = Field(..., description="Confusion matrix classification")
    category: str = Field(..., description="SQL injection category")
    language: str = Field(..., description="Programming language")
    confidence: float = Field(0.5, description="Purple agent's confidence")
    execution_time_ms: float | None = Field(None, description="Execution time in milliseconds")
    purple_agent_response: PurpleAgentResponse | None = Field(None, description="Full purple agent response")

    @field_validator('outcome', mode='before')
    @classmethod
    def determine_outcome(cls, v: Any, info) -> DetectionOutcome:
        """Automatically determine outcome from ground_truth and predicted if not provided."""
        if isinstance(v, DetectionOutcome):
            return v

        # Access other fields from validation context
        data = info.data
        ground_truth = data.get('ground_truth')
        predicted = data.get('predicted')

        if ground_truth is None or predicted is None:
            raise ValueError("ground_truth and predicted must be provided")

        if ground_truth and predicted:
            return DetectionOutcome.TRUE_POSITIVE
        elif not ground_truth and not predicted:
            return DetectionOutcome.TRUE_NEGATIVE
        elif not ground_truth and predicted:
            return DetectionOutcome.FALSE_POSITIVE
        else:  # ground_truth and not predicted
            return DetectionOutcome.FALSE_NEGATIVE


# ============================================================================
# Evaluation Metrics Models
# ============================================================================

class ConfusionMatrix(BaseModel):
    """Confusion matrix for binary classification."""

    true_positives: int = Field(0, ge=0, description="Correctly identified vulnerabilities")
    true_negatives: int = Field(0, ge=0, description="Correctly identified secure code")
    false_positives: int = Field(0, ge=0, description="Secure code flagged as vulnerable")
    false_negatives: int = Field(0, ge=0, description="Vulnerabilities missed")

    @property
    def total(self) -> int:
        """Total number of samples."""
        return self.true_positives + self.true_negatives + self.false_positives + self.false_negatives


class EvaluationMetrics(BaseModel):
    """Comprehensive evaluation metrics for security detection."""

    f1_score: float = Field(0.0, ge=0.0, le=1.0, description="F1 score (harmonic mean of precision and recall)")
    precision: float = Field(0.0, ge=0.0, le=1.0, description="Precision (TP / (TP + FP))")
    recall: float = Field(0.0, ge=0.0, le=1.0, description="Recall/TPR (TP / (TP + FN))")
    specificity: float = Field(0.0, ge=0.0, le=1.0, description="Specificity/TNR (TN / (TN + FP))")
    accuracy: float = Field(0.0, ge=0.0, le=1.0, description="Accuracy ((TP + TN) / Total)")
    false_positive_rate: float = Field(0.0, ge=0.0, le=1.0, description="FPR (FP / (FP + TN))")
    false_negative_rate: float = Field(0.0, ge=0.0, le=1.0, description="FNR (FN / (FN + TP))")
    confusion_matrix: ConfusionMatrix = Field(..., description="Confusion matrix")
    total_samples: int = Field(0, ge=0, description="Total number of samples evaluated")


class CategoryMetrics(BaseModel):
    """Metrics for a specific category (e.g., classic_sqli, blind_sqli)."""

    category: str = Field(..., description="Category name")
    metrics: EvaluationMetrics = Field(..., description="Metrics for this category")
    sample_count: int = Field(0, ge=0, description="Number of samples in this category")


# ============================================================================
# Adaptive Testing Models
# ============================================================================

class TestPhase(str, Enum):
    """Phases of adaptive testing."""
    EXPLORATION = "exploration"    # Initial diverse sampling
    EXPLOITATION = "exploitation"  # Focus on weak areas
    VALIDATION = "validation"      # Final verification


class PerformanceAnalysis(BaseModel):
    """Analysis of purple agent's performance for adaptive decision-making."""

    overall_f1: float = Field(..., description="Overall F1 score")
    category_f1: dict[str, float] = Field(default_factory=dict, description="F1 score per category")
    weak_categories: list[str] = Field(default_factory=list, description="Categories with F1 < threshold")
    strong_categories: list[str] = Field(default_factory=list, description="Categories with F1 >= threshold")
    performance_trend: str = Field("stable", description="improving, declining, or stable")
    confidence_analysis: dict[str, Any] = Field(default_factory=dict, description="Analysis of confidence scores")


class AutonomousDecision(BaseModel):
    """Log of an autonomous decision made by the green agent."""

    timestamp: datetime = Field(default_factory=datetime.now, description="When decision was made")
    decision_type: Literal[
        "test_allocation",
        "difficulty_escalation",
        "budget_allocation",
        "early_termination",
        "weak_area_identification"
    ] = Field(..., description="Type of autonomous decision")
    reasoning: str = Field(..., description="Why this decision was made")
    input_data: dict[str, Any] = Field(default_factory=dict, description="Data used for decision")
    decision: dict[str, Any] = Field(default_factory=dict, description="The actual decision made")
    phase: TestPhase = Field(..., description="Testing phase when decision was made")


class TestAllocation(BaseModel):
    """Allocation of tests across categories."""

    category: str = Field(..., description="Category name")
    allocated_count: int = Field(0, ge=0, description="Number of tests allocated")
    reason: str = Field(..., description="Reason for this allocation")


class TestPlan(BaseModel):
    """Plan for the next batch of tests in adaptive mode."""

    phase: TestPhase = Field(..., description="Current testing phase")
    allocations: list[TestAllocation] = Field(default_factory=list, description="Test allocations per category")
    total_tests: int = Field(0, ge=0, description="Total tests in this batch")
    rationale: str = Field(..., description="Overall rationale for this plan")


class RoundResults(BaseModel):
    """Results from a single round of adaptive testing."""

    round_number: int = Field(..., ge=1, description="Round number (1-indexed)")
    phase: TestPhase = Field(..., description="Testing phase for this round")
    test_results: list[TestResult] = Field(default_factory=list, description="Test results for this round")
    metrics: EvaluationMetrics = Field(..., description="Metrics for this round")
    category_metrics: list[CategoryMetrics] = Field(default_factory=list, description="Per-category metrics")
    decisions_made: list[AutonomousDecision] = Field(default_factory=list, description="Autonomous decisions")
    tests_executed: int = Field(0, ge=0, description="Number of tests in this round")
    cumulative_tests: int = Field(0, ge=0, description="Total tests executed so far")


class AdaptiveEvaluationResult(BaseModel):
    """Complete results from an adaptive evaluation session."""

    purple_agent_id: str = Field(..., description="ID of the purple agent evaluated")
    total_rounds: int = Field(..., ge=1, description="Total number of rounds executed")
    total_tests_executed: int = Field(..., ge=0, description="Total tests across all rounds")
    test_budget: int = Field(..., ge=1, description="Allocated test budget")
    final_metrics: EvaluationMetrics = Field(..., description="Final overall metrics")
    final_category_metrics: list[CategoryMetrics] = Field(default_factory=list, description="Final per-category metrics")
    round_history: list[RoundResults] = Field(default_factory=list, description="Results from each round")
    all_decisions: list[AutonomousDecision] = Field(default_factory=list, description="All autonomous decisions made")
    termination_reason: str = Field(..., description="Why evaluation terminated")
    execution_time_seconds: float = Field(..., ge=0.0, description="Total execution time")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# ============================================================================
# Configuration Models
# ============================================================================

class EvaluationMode(str, Enum):
    """Evaluation mode: fixed or adaptive."""
    FIXED = "fixed"
    ADAPTIVE = "adaptive"


class AdaptiveConfig(BaseModel):
    """Configuration for adaptive testing."""

    initial_exploration_size: int = Field(20, ge=1, description="Number of tests in exploration phase")
    weak_threshold: float = Field(0.6, ge=0.0, le=1.0, description="F1 threshold for weak categories")
    focus_percentage: float = Field(0.6, ge=0.0, le=1.0, description="Percentage of tests for weak areas")
    max_rounds: int = Field(5, ge=1, description="Maximum number of testing rounds")
    stability_threshold: float = Field(0.05, ge=0.0, le=1.0, description="F1 change threshold for stability")
    min_category_samples: int = Field(5, ge=1, description="Minimum samples per category per round")


class EvaluationConfig(BaseModel):
    """Configuration for evaluation session."""

    mode: EvaluationMode = Field(EvaluationMode.FIXED, description="Evaluation mode")
    test_budget: int = Field(100, ge=1, description="Total number of tests allowed")
    timeout_seconds: int = Field(300, ge=1, description="Timeout for entire evaluation")
    per_test_timeout_seconds: float = Field(10.0, ge=0.1, description="Timeout per individual test")
    adaptive_config: AdaptiveConfig | None = Field(None, description="Adaptive mode configuration")
    random_seed: int | None = Field(None, description="Random seed for reproducibility")
    categories_to_test: list[str] | None = Field(None, description="Specific categories to test (None = all)")
    languages_to_test: list[str] | None = Field(None, description="Specific languages to test (None = all)")


# ============================================================================
# A2A Protocol Models (AgentBeats Integration)
# ============================================================================

class EvalRequest(BaseModel):
    """Evaluation request following A2A protocol structure."""

    purple_agent_id: str = Field(..., description="ID of purple agent to evaluate")
    purple_agent_endpoint: str = Field(..., description="URL endpoint of purple agent")
    config: dict[str, Any] = Field(default_factory=dict, description="Configuration parameters")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional request metadata")


class EvalResponse(BaseModel):
    """Evaluation response following A2A protocol structure."""

    success: bool = Field(..., description="Whether evaluation completed successfully")
    metrics: EvaluationMetrics | None = Field(None, description="Evaluation metrics if successful")
    category_metrics: list[CategoryMetrics] = Field(default_factory=list, description="Per-category metrics")
    error_message: str | None = Field(None, description="Error message if failed")
    tests_executed: int = Field(0, ge=0, description="Number of tests executed")
    execution_time_seconds: float = Field(0.0, ge=0.0, description="Total execution time")
    adaptive_results: AdaptiveEvaluationResult | None = Field(None, description="Adaptive evaluation details")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional response metadata")


# ============================================================================
# Dataset Models
# ============================================================================

class DatasetInfo(BaseModel):
    """Information about a dataset loaded from JSON."""

    language: str = Field(..., description="Programming language")
    vulnerability_type: str = Field("sql_injection", description="Type of vulnerability")
    total_samples: int = Field(0, ge=0, description="Total samples in dataset")
    vulnerable_count: int = Field(0, ge=0, description="Number of vulnerable samples")
    secure_count: int = Field(0, ge=0, description="Number of secure samples")
    categories: dict[str, int] = Field(default_factory=dict, description="Sample count per category")
    source_file: str = Field(..., description="Source JSON file path")
    loaded_at: datetime = Field(default_factory=datetime.now, description="When dataset was loaded")


class DatasetMetadata(BaseModel):
    """Metadata about all loaded datasets."""

    total_samples: int = Field(0, ge=0, description="Total samples across all datasets")
    total_vulnerable: int = Field(0, ge=0, description="Total vulnerable samples")
    total_secure: int = Field(0, ge=0, description="Total secure samples")
    languages: list[str] = Field(default_factory=list, description="Languages in datasets")
    categories: list[str] = Field(default_factory=list, description="Categories in datasets")
    datasets: list[DatasetInfo] = Field(default_factory=list, description="Info for each dataset file")
    loaded_at: datetime = Field(default_factory=datetime.now, description="When metadata was generated")
