"""
SQL Injection Detection Benchmark - Security Evaluator Package.

This package contains the Green Agent implementation for evaluating
SQL injection detection capabilities of Purple Agents.
"""

__version__ = "1.0.0"
__author__ = "SecurityEvaluator Team"

from .models import (
    CodeSample,
    DetectionOutcome,
    PurpleAgentResponse,
    TestResult,
    EvaluationMetrics,
    CategoryMetrics,
    EvalRequest,
    EvalResponse,
)

from .dataset_manager import DatasetManager
from .scoring_engine import ScoringEngine
from .adaptive_planner import AdaptiveTestPlanner
from .agent_card import sql_injection_agent_card

__all__ = [
    "CodeSample",
    "DetectionOutcome",
    "PurpleAgentResponse",
    "TestResult",
    "EvaluationMetrics",
    "CategoryMetrics",
    "EvalRequest",
    "EvalResponse",
    "DatasetManager",
    "ScoringEngine",
    "AdaptiveTestPlanner",
    "sql_injection_agent_card",
]
