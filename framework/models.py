"""
Data models for the Unified Adaptive Security Evaluation Framework.

This module defines all data structures used throughout the framework.
Based on UNIFIED_ARCHITECTURE.md and ENHANCED_DESIGN.md v2.1.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple
import hashlib
import json


# ============================================================================
# ENUMS
# ============================================================================

class AttackStatus(Enum):
    """Attack lifecycle status."""
    CREATED = auto()
    VALIDATED = auto()
    TESTED = auto()
    DETECTED = auto()
    EVADED = auto()
    INVALID = auto()


class TestOutcome(Enum):
    """Test result outcome."""
    TRUE_POSITIVE = auto()   # Attack detected correctly
    TRUE_NEGATIVE = auto()   # Safe input not detected
    FALSE_POSITIVE = auto()  # Safe input detected as attack
    FALSE_NEGATIVE = auto()  # Attack not detected (evasion)


class Severity(Enum):
    """Attack severity levels."""
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    CRITICAL = auto()


class AttackCategory(Enum):
    """Attack categories for different scenario types."""
    # SQL Injection categories
    CLASSIC_SQLI = auto()
    BLIND_SQLI = auto()
    UNION_BASED = auto()
    TIME_BASED = auto()

    # Prompt Injection categories
    JAILBREAK = auto()
    PROMPT_LEAK = auto()
    ROLE_MANIPULATION = auto()
    INSTRUCTION_OVERRIDE = auto()
    RESOURCE_ABUSE = auto()
    DATA_EXFILTRATION = auto()
    DELIMITER_ATTACK = auto()

    # XSS categories (placeholder)
    STORED_XSS = auto()
    REFLECTED_XSS = auto()
    DOM_XSS = auto()

    # Command Injection categories (placeholder)
    SHELL_INJECTION = auto()
    OS_COMMAND = auto()

    # Generic
    BENIGN = auto()
    UNKNOWN = auto()


# Alias for backward compatibility
class DetectionOutcome(Enum):
    """Detection outcome (alias for TestOutcome)."""
    TRUE_POSITIVE = auto()
    TRUE_NEGATIVE = auto()
    FALSE_POSITIVE = auto()
    FALSE_NEGATIVE = auto()


# ============================================================================
# CORE DATA MODELS
# ============================================================================

@dataclass
class Attack:
    """
    Represents a security attack test case.

    Universal model works for any attack type (SQL Injection, XSS, DDoS, etc.)
    """
    attack_id: str
    scenario: str  # e.g., 'sql_injection', 'xss', 'ddos'
    technique: str  # e.g., 'union_based', 'time_based'
    payload: Any  # Type varies by scenario (str, dict, bytes, etc.)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Attack properties
    is_malicious: bool = True  # False for benign test cases
    severity: Severity = Severity.MEDIUM
    expected_detection: bool = True  # Should this be detected?

    # Lifecycle
    status: AttackStatus = AttackStatus.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "unknown"  # Agent ID that created this

    # Genealogy (for mutation tracking)
    parent_attack_id: Optional[str] = None
    generation: int = 0  # 0 = baseline, 1+ = mutated
    mutation_type: Optional[str] = None

    # Validation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)

    # Test results (populated after testing)
    test_result: Optional['TestResult'] = None

    def get_hash(self) -> str:
        """
        Generate deterministic hash for this attack.

        Used for deduplication and reproducibility.
        """
        payload_str = json.dumps(self.payload, sort_keys=True)
        content = f"{self.scenario}:{self.technique}:{payload_str}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'attack_id': self.attack_id,
            'scenario': self.scenario,
            'technique': self.technique,
            'payload': self.payload,
            'metadata': self.metadata,
            'is_malicious': self.is_malicious,
            'severity': self.severity.name,
            'expected_detection': self.expected_detection,
            'status': self.status.name,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'parent_attack_id': self.parent_attack_id,
            'generation': self.generation,
            'mutation_type': self.mutation_type,
            'is_valid': self.is_valid,
            'validation_errors': self.validation_errors,
            'hash': self.get_hash()
        }


@dataclass
class TestResult:
    """
    Result of testing an attack against a purple agent.
    """
    result_id: str
    attack_id: str
    purple_agent: str  # Name of purple agent tested
    timestamp: datetime = field(default_factory=datetime.now)

    # Detection outcome
    detected: bool = False
    confidence: float = 0.0  # Detection confidence [0, 1]
    detection_reason: Optional[str] = None

    # Classification
    outcome: Optional[TestOutcome] = None  # TP, TN, FP, FN

    # Performance metrics
    latency_ms: float = 0.0
    memory_mb: float = 0.0

    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_evasion(self) -> bool:
        """Check if this is a successful evasion (False Negative)."""
        return self.outcome == TestOutcome.FALSE_NEGATIVE

    def is_correct_detection(self) -> bool:
        """Check if detection was correct (TP or TN)."""
        return self.outcome in [TestOutcome.TRUE_POSITIVE, TestOutcome.TRUE_NEGATIVE]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'result_id': self.result_id,
            'attack_id': self.attack_id,
            'purple_agent': self.purple_agent,
            'timestamp': self.timestamp.isoformat(),
            'detected': self.detected,
            'confidence': self.confidence,
            'detection_reason': self.detection_reason,
            'outcome': self.outcome.name if self.outcome else None,
            'latency_ms': self.latency_ms,
            'memory_mb': self.memory_mb,
            'metadata': self.metadata
        }


@dataclass
class BehaviorDescriptor:
    """
    Describes attack behavior for novelty search.

    Used in diversity-preserving evolution (Enhancement 2).
    """
    attack_id: str
    features: Dict[str, float]  # Feature vector
    attack_family: str  # Clustering label
    novelty_score: float = 0.0

    @staticmethod
    def extract(payload: Any, metadata: Dict[str, Any]) -> 'BehaviorDescriptor':
        """
        Extract behavior descriptor from attack.

        Override in scenario-specific implementations for better features.

        Args:
            payload: Attack payload
            metadata: Attack metadata

        Returns:
            Behavior descriptor
        """
        # Default: Basic features
        payload_str = str(payload)
        features = {
            'length': float(len(payload_str)),
            'num_special_chars': float(sum(1 for c in payload_str if not c.isalnum())),
            'num_digits': float(sum(1 for c in payload_str if c.isdigit())),
            'entropy': _calculate_entropy(payload_str),
        }

        return BehaviorDescriptor(
            attack_id=metadata.get('attack_id', 'unknown'),
            features=features,
            attack_family='unknown'
        )

    def distance(self, other: 'BehaviorDescriptor') -> float:
        """
        Calculate distance to another descriptor.

        Returns:
            Distance in [0, ∞) where 0 = identical
        """
        # Euclidean distance on normalized features
        all_keys = set(self.features.keys()) | set(other.features.keys())
        distance_sq = 0.0

        for key in all_keys:
            v1 = self.features.get(key, 0.0)
            v2 = other.features.get(key, 0.0)
            distance_sq += (v1 - v2) ** 2

        return distance_sq ** 0.5


@dataclass
class Metrics:
    """
    Evaluation metrics.
    """
    # Confusion matrix
    true_positives: int = 0
    true_negatives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    # Derived metrics
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    accuracy: float = 0.0
    false_positive_rate: float = 0.0
    false_negative_rate: float = 0.0

    # Per-technique breakdown
    per_technique: Dict[str, 'Metrics'] = field(default_factory=dict)

    # Cost metrics
    total_cost_usd: float = 0.0
    llm_calls: int = 0
    total_latency_ms: float = 0.0

    def calculate_derived_metrics(self):
        """Calculate precision, recall, F1, etc. from confusion matrix."""
        tp = self.true_positives
        tn = self.true_negatives
        fp = self.false_positives
        fn = self.false_negatives

        # Precision
        self.precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0

        # Recall
        self.recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        # F1 Score
        if self.precision + self.recall > 0:
            self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall)
        else:
            self.f1_score = 0.0

        # Accuracy
        total = tp + tn + fp + fn
        self.accuracy = (tp + tn) / total if total > 0 else 0.0

        # False Positive Rate (FPR)
        self.false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        # False Negative Rate (FNR)
        self.false_negative_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'true_positives': self.true_positives,
            'true_negatives': self.true_negatives,
            'false_positives': self.false_positives,
            'false_negatives': self.false_negatives,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'accuracy': self.accuracy,
            'false_positive_rate': self.false_positive_rate,
            'false_negative_rate': self.false_negative_rate,
            'total_cost_usd': self.total_cost_usd,
            'llm_calls': self.llm_calls,
            'total_latency_ms': self.total_latency_ms,
            'per_technique': {k: v.to_dict() for k, v in self.per_technique.items()}
        }


@dataclass
class PerspectiveAssessment:
    """
    Assessment from a specific perspective (security expert, developer, etc.)
    """
    perspective_id: str
    perspective_type: str  # 'security_expert', 'developer', 'pentester'
    agent_id: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Assessment
    quality_score: float = 0.0  # [0, 1]
    comments: str = ""
    concerns: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Metadata
    llm_model: Optional[str] = None
    cost_usd: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'perspective_id': self.perspective_id,
            'perspective_type': self.perspective_type,
            'agent_id': self.agent_id,
            'timestamp': self.timestamp.isoformat(),
            'quality_score': self.quality_score,
            'comments': self.comments,
            'concerns': self.concerns,
            'recommendations': self.recommendations,
            'llm_model': self.llm_model,
            'cost_usd': self.cost_usd
        }


@dataclass
class CounterfactualResult:
    """
    Result of counterfactual failure analysis.

    Shows minimal edits to make an evasion detectable (Enhancement 4).
    """
    attack_id: str
    original_payload: Any
    counterfactual_payload: Any
    edit_distance: int  # Number of edits
    edits: List[Dict[str, Any]]  # List of edits made
    now_detected: bool
    explanation: str
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'attack_id': self.attack_id,
            'original_payload': self.original_payload,
            'counterfactual_payload': self.counterfactual_payload,
            'edit_distance': self.edit_distance,
            'edits': self.edits,
            'now_detected': self.now_detected,
            'explanation': self.explanation,
            'confidence': self.confidence
        }


@dataclass
class CoverageReport:
    """
    Coverage report for MITRE ATT&CK or other taxonomies.

    Tracks which techniques are covered (Enhancement 7).
    """
    taxonomy: str  # 'MITRE_ATT&CK', 'OWASP_Top_10', etc.
    total_techniques: int
    covered_techniques: Set[str] = field(default_factory=set)
    coverage_percentage: float = 0.0

    # Debt tracking
    uncovered_techniques: Set[str] = field(default_factory=set)
    partially_covered: Dict[str, float] = field(default_factory=dict)  # technique -> coverage %

    # Prioritization
    priority_queue: List[Tuple[str, float]] = field(default_factory=list)  # (technique, priority)

    def calculate_coverage(self):
        """Calculate coverage percentage."""
        if self.total_techniques > 0:
            self.coverage_percentage = (len(self.covered_techniques) / self.total_techniques) * 100.0
        else:
            self.coverage_percentage = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'taxonomy': self.taxonomy,
            'total_techniques': self.total_techniques,
            'covered_techniques': list(self.covered_techniques),
            'coverage_percentage': self.coverage_percentage,
            'uncovered_techniques': list(self.uncovered_techniques),
            'partially_covered': self.partially_covered,
            'priority_queue': self.priority_queue
        }


@dataclass
class EvaluationResult:
    """
    Complete evaluation result for a purple agent.
    """
    evaluation_id: str
    purple_agent: str
    scenario: str
    start_time: datetime
    end_time: Optional[datetime] = None

    # Test data
    total_attacks_tested: int = 0
    attacks: List[Attack] = field(default_factory=list)
    test_results: List[TestResult] = field(default_factory=list)

    # Metrics
    metrics: Metrics = field(default_factory=Metrics)

    # Multi-perspective assessments
    perspective_assessments: List[PerspectiveAssessment] = field(default_factory=list)

    # Counterfactual analysis
    counterfactual_results: List[CounterfactualResult] = field(default_factory=list)

    # Coverage
    coverage_report: Optional[CoverageReport] = None

    # Agent activity
    agent_contributions: Dict[str, int] = field(default_factory=dict)  # agent_id -> num_contributions
    coalition_history: List[Dict[str, Any]] = field(default_factory=list)

    # Cost and performance
    total_cost_usd: float = 0.0
    total_time_seconds: float = 0.0
    llm_calls: int = 0

    # eBOM (Evaluation Bill of Materials) - Enhancement 8
    ebom: Dict[str, Any] = field(default_factory=dict)

    # Status
    status: str = "running"  # running, completed, failed

    def finalize(self):
        """Finalize evaluation and calculate all metrics."""
        self.end_time = datetime.now()
        self.total_time_seconds = (self.end_time - self.start_time).total_seconds()

        # Calculate metrics from test results
        for result in self.test_results:
            if result.outcome == TestOutcome.TRUE_POSITIVE:
                self.metrics.true_positives += 1
            elif result.outcome == TestOutcome.TRUE_NEGATIVE:
                self.metrics.true_negatives += 1
            elif result.outcome == TestOutcome.FALSE_POSITIVE:
                self.metrics.false_positives += 1
            elif result.outcome == TestOutcome.FALSE_NEGATIVE:
                self.metrics.false_negatives += 1

        self.metrics.calculate_derived_metrics()
        self.metrics.total_cost_usd = self.total_cost_usd
        self.metrics.llm_calls = self.llm_calls
        self.metrics.total_latency_ms = sum(r.latency_ms for r in self.test_results)

        self.status = "completed"

    def get_evasions(self) -> List[TestResult]:
        """Get all successful evasions (False Negatives)."""
        return [r for r in self.test_results if r.is_evasion()]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'evaluation_id': self.evaluation_id,
            'purple_agent': self.purple_agent,
            'scenario': self.scenario,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_attacks_tested': self.total_attacks_tested,
            'attacks': [a.to_dict() for a in self.attacks],
            'test_results': [r.to_dict() for r in self.test_results],
            'metrics': self.metrics.to_dict(),
            'perspective_assessments': [p.to_dict() for p in self.perspective_assessments],
            'counterfactual_results': [c.to_dict() for c in self.counterfactual_results],
            'coverage_report': self.coverage_report.to_dict() if self.coverage_report else None,
            'agent_contributions': self.agent_contributions,
            'coalition_history': self.coalition_history,
            'total_cost_usd': self.total_cost_usd,
            'total_time_seconds': self.total_time_seconds,
            'llm_calls': self.llm_calls,
            'ebom': self.ebom,
            'status': self.status
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# ============================================================================
# DUAL EVALUATION DATA MODELS
# ============================================================================

@dataclass
class Vulnerability:
    """
    Represents a security vulnerability discovered during testing.
    
    Used for Purple Agent security assessment with CVSS scoring.
    """
    vulnerability_id: str  # e.g., "PURP-2025-001"
    attack_id: str         # Reference to the attack that found it
    cvss_score: float      # CVSS 3.1 base score (0.0-10.0)
    severity: str          # CRITICAL, HIGH, MEDIUM, LOW
    cwe_id: str           # e.g., "CWE-77"
    cwe_name: str         # e.g., "Command Injection"
    description: str       # What the vulnerability is
    proof_of_concept: str  # How it was exploited
    remediation: str       # How to fix it
    category: str          # Attack category
    cvss_vector: Optional[str] = None  # Full CVSS vector string
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'vulnerability_id': self.vulnerability_id,
            'attack_id': self.attack_id,
            'cvss_score': self.cvss_score,
            'severity': self.severity,
            'cwe_id': self.cwe_id,
            'cwe_name': self.cwe_name,
            'description': self.description,
            'proof_of_concept': self.proof_of_concept,
            'remediation': self.remediation,
            'category': self.category,
            'cvss_vector': self.cvss_vector,
            'metadata': self.metadata
        }


@dataclass
class GreenAgentMetrics:
    """
    Green Agent effectiveness metrics.
    
    Measures how effective the Green Agent (attacker/evaluator) is at
    finding vulnerabilities. Uses ML terminology (TP/FP/FN/TN).
    """
    # Confusion matrix
    true_positives: int = 0    # Vulnerabilities found
    true_negatives: int = 0    # Correctly identified secure behavior
    false_positives: int = 0   # False alarms
    false_negatives: int = 0   # Missed vulnerabilities
    
    # Performance metrics
    precision: float = 0.0     # TP / (TP + FP)
    recall: float = 0.0        # TP / (TP + FN)
    f1_score: float = 0.0      # Harmonic mean
    accuracy: float = 0.0      # (TP + TN) / Total
    specificity: float = 0.0   # TN / (TN + FP)
    
    # Error rates
    false_positive_rate: float = 0.0  # FP / (FP + TN)
    false_negative_rate: float = 0.0  # FN / (FN + TP)
    
    # Evaluation metrics
    competition_score: float = 0.0  # F1 * 100
    grade: str = ""                 # A+, A, B+, etc.
    
    # Per-category breakdowns
    per_category: Dict[str, 'GreenAgentMetrics'] = field(default_factory=dict)
    
    # Metadata
    total_tests: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    
    def calculate_derived_metrics(self):
        """Calculate all derived metrics from confusion matrix."""
        tp = self.true_positives
        tn = self.true_negatives
        fp = self.false_positives
        fn = self.false_negatives
        
        # Precision
        self.precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        
        # Recall
        self.recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        
        # F1 Score
        if self.precision + self.recall > 0:
            self.f1_score = 2 * (self.precision * self.recall) / (self.precision + self.recall)
        else:
            self.f1_score = 0.0
        
        # Accuracy
        total = tp + tn + fp + fn
        self.accuracy = (tp + tn) / total if total > 0 else 0.0
        
        # Specificity
        self.specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        
        # False Positive Rate
        self.false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        
        # False Negative Rate
        self.false_negative_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        
        # Evaluation score
        self.competition_score = self.f1_score * 100
        
        # Grade
        self.grade = self._calculate_grade(self.competition_score)
        
        # Total tests
        self.total_tests = total
    
    def _calculate_grade(self, score: float) -> str:
        """Convert evaluation score to letter grade."""
        if score >= 97: return "A+"
        if score >= 93: return "A"
        if score >= 90: return "A-"
        if score >= 87: return "B+"
        if score >= 83: return "B"
        if score >= 80: return "B-"
        if score >= 77: return "C+"
        if score >= 73: return "C"
        if score >= 70: return "C-"
        if score >= 67: return "D+"
        if score >= 63: return "D"
        if score >= 60: return "D-"
        return "F"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'true_positives': self.true_positives,
            'true_negatives': self.true_negatives,
            'false_positives': self.false_positives,
            'false_negatives': self.false_negatives,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'accuracy': self.accuracy,
            'specificity': self.specificity,
            'false_positive_rate': self.false_positive_rate,
            'false_negative_rate': self.false_negative_rate,
            'competition_score': self.competition_score,
            'grade': self.grade,
            'per_category': {k: v.to_dict() for k, v in self.per_category.items()},
            'total_tests': self.total_tests,
            'total_cost_usd': self.total_cost_usd,
            'total_latency_ms': self.total_latency_ms
        }


@dataclass
class PurpleAgentAssessment:
    """
    Purple Agent security posture assessment.
    
    Measures how secure the Purple Agent (defender/target) is.
    Uses security terminology (CVSS, vulnerabilities, security score).
    """
    # Vulnerability summary
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    total_vulnerabilities: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    
    # Security metrics
    security_score: float = 0.0  # 0-100 (inverse of attack success rate)
    security_grade: str = ""     # A+, A, B+, etc.
    attack_success_rate: float = 0.0  # Percentage of attacks that succeeded
    defense_success_rate: float = 0.0  # Percentage of attacks blocked
    
    # Risk metrics
    average_cvss_score: float = 0.0
    max_cvss_score: float = 0.0
    risk_level: str = ""  # CRITICAL, HIGH, MEDIUM, LOW, MINIMAL
    
    # Remediation
    estimated_fix_time_hours: float = 0.0
    priority_fixes: List[str] = field(default_factory=list)  # Vuln IDs
    
    # Per-category breakdowns
    per_category: Dict[str, 'PurpleAgentAssessment'] = field(default_factory=dict)
    
    # Metadata
    total_tests: int = 0
    purple_agent_name: str = ""
    assessment_date: Optional[datetime] = None
    
    def calculate_security_metrics(self):
        """Calculate security score and risk level from vulnerabilities."""
        if not self.vulnerabilities and self.total_tests == 0:
            self.security_score = 0.0
            self.security_grade = "F"
            self.risk_level = "UNKNOWN"
            return
        
        # Count vulnerabilities by severity
        self.total_vulnerabilities = len(self.vulnerabilities)
        self.critical_count = sum(1 for v in self.vulnerabilities if v.severity == "CRITICAL")
        self.high_count = sum(1 for v in self.vulnerabilities if v.severity == "HIGH")
        self.medium_count = sum(1 for v in self.vulnerabilities if v.severity == "MEDIUM")
        self.low_count = sum(1 for v in self.vulnerabilities if v.severity == "LOW")
        
        # Attack success rate (vulnerabilities / total malicious tests)
        if self.total_tests > 0:
            self.attack_success_rate = (self.total_vulnerabilities / self.total_tests) * 100
            self.defense_success_rate = 100 - self.attack_success_rate
        
        # Security score (inverse of attack success rate)
        self.security_score = self.defense_success_rate
        
        # Security grade
        self.security_grade = self._calculate_grade(self.security_score)
        
        # CVSS analysis
        if self.vulnerabilities:
            cvss_scores = [v.cvss_score for v in self.vulnerabilities]
            self.average_cvss_score = sum(cvss_scores) / len(cvss_scores)
            self.max_cvss_score = max(cvss_scores)
        
        # Risk level
        self.risk_level = self._calculate_risk_level()
        
        # Estimated fix time (rough estimate: 2h per critical, 1h per high, 0.5h per medium, 0.25h per low)
        self.estimated_fix_time_hours = (
            self.critical_count * 2 +
            self.high_count * 1 +
            self.medium_count * 0.5 +
            self.low_count * 0.25
        )
        
        # Priority fixes (Critical and High severity, sorted by CVSS)
        priority_vulns = [v for v in self.vulnerabilities 
                         if v.severity in ["CRITICAL", "HIGH"]]
        priority_vulns.sort(key=lambda v: v.cvss_score, reverse=True)
        self.priority_fixes = [v.vulnerability_id for v in priority_vulns[:10]]  # Top 10
    
    def _calculate_grade(self, score: float) -> str:
        """Convert security score to letter grade."""
        if score >= 97: return "A+"
        if score >= 93: return "A"
        if score >= 90: return "A-"
        if score >= 87: return "B+"
        if score >= 83: return "B"
        if score >= 80: return "B-"
        if score >= 77: return "C+"
        if score >= 73: return "C"
        if score >= 70: return "C-"
        if score >= 67: return "D+"
        if score >= 63: return "D"
        if score >= 60: return "D-"
        return "F"
    
    def _calculate_risk_level(self) -> str:
        """Calculate overall risk level."""
        if self.critical_count > 0 or self.max_cvss_score >= 9.0:
            return "CRITICAL"
        elif self.high_count > 3 or self.max_cvss_score >= 7.0:
            return "HIGH"
        elif self.high_count > 0 or self.medium_count > 5:
            return "MEDIUM"
        elif self.medium_count > 0 or self.low_count > 10:
            return "LOW"
        else:
            return "MINIMAL"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'vulnerabilities': [v.to_dict() for v in self.vulnerabilities],
            'total_vulnerabilities': self.total_vulnerabilities,
            'critical_count': self.critical_count,
            'high_count': self.high_count,
            'medium_count': self.medium_count,
            'low_count': self.low_count,
            'security_score': self.security_score,
            'security_grade': self.security_grade,
            'attack_success_rate': self.attack_success_rate,
            'defense_success_rate': self.defense_success_rate,
            'average_cvss_score': self.average_cvss_score,
            'max_cvss_score': self.max_cvss_score,
            'risk_level': self.risk_level,
            'estimated_fix_time_hours': self.estimated_fix_time_hours,
            'priority_fixes': self.priority_fixes,
            'per_category': {k: v.to_dict() for k, v in self.per_category.items()},
            'total_tests': self.total_tests,
            'purple_agent_name': self.purple_agent_name,
            'assessment_date': self.assessment_date.isoformat() if self.assessment_date else None
        }


@dataclass
class DualEvaluationResult:
    """
    Combined result containing both Green and Purple perspectives.
    
    Provides dual evaluation: scanner effectiveness + target security.
    """
    evaluation_id: str
    green_agent_metrics: GreenAgentMetrics
    purple_agent_assessment: PurpleAgentAssessment
    
    # Evaluation metadata
    purple_agent_name: str
    scenario: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_time_seconds: float = 0.0
    
    # Test results reference
    total_tests: int = 0
    malicious_tests: int = 0
    benign_tests: int = 0
    
    def finalize(self):
        """Finalize the dual evaluation."""
        if self.end_time is None:
            self.end_time = datetime.now()
        self.total_time_seconds = (self.end_time - self.start_time).total_seconds()
        
        # Calculate metrics
        self.green_agent_metrics.calculate_derived_metrics()
        self.purple_agent_assessment.calculate_security_metrics()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'evaluation_id': self.evaluation_id,
            'green_agent_metrics': self.green_agent_metrics.to_dict(),
            'purple_agent_assessment': self.purple_agent_assessment.to_dict(),
            'purple_agent_name': self.purple_agent_name,
            'scenario': self.scenario,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_time_seconds': self.total_time_seconds,
            'total_tests': self.total_tests,
            'malicious_tests': self.malicious_tests,
            'benign_tests': self.benign_tests
        }


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _calculate_entropy(s: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not s:
        return 0.0

    from collections import Counter
    import math

    length = len(s)
    counts = Counter(s)
    entropy = 0.0

    for count in counts.values():
        probability = count / length
        entropy -= probability * math.log2(probability)

    return entropy


def create_attack_id(scenario: str, technique: str, timestamp: datetime) -> str:
    """
    Generate unique attack ID.

    Args:
        scenario: Scenario name
        technique: Technique name
        timestamp: Creation timestamp

    Returns:
        Unique attack ID
    """
    ts = int(timestamp.timestamp() * 1000000)  # microseconds
    return f"{scenario}_{technique}_{ts}"


def create_result_id(attack_id: str, purple_agent: str, timestamp: datetime) -> str:
    """
    Generate unique result ID.

    Args:
        attack_id: Attack ID
        purple_agent: Purple agent name
        timestamp: Test timestamp

    Returns:
        Unique result ID
    """
    ts = int(timestamp.timestamp() * 1000000)
    return f"{attack_id}_{purple_agent}_{ts}"


def calculate_outcome(attack: Attack, detected: bool) -> TestOutcome:
    """
    Calculate test outcome based on attack properties and detection.

    Args:
        attack: Attack that was tested
        detected: Whether attack was detected

    Returns:
        Test outcome (TP, TN, FP, FN)
    """
    if attack.is_malicious:
        # Malicious attack
        if detected:
            return TestOutcome.TRUE_POSITIVE  # Correctly detected
        else:
            return TestOutcome.FALSE_NEGATIVE  # Evasion!
    else:
        # Benign input
        if detected:
            return TestOutcome.FALSE_POSITIVE  # False alarm
        else:
            return TestOutcome.TRUE_NEGATIVE  # Correctly allowed
