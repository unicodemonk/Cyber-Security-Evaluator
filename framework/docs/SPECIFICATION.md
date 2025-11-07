# Technical Specification

**Version:** 1.0
**Date:** November 2025
**Status:** Design Phase

---

## Core Interfaces

### SecurityScenario

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pydantic import BaseModel

class SecurityScenario(ABC):
    """
    Universal interface for all security testing scenarios.
    Every scenario (SQL Injection, DDoS, MITRE techniques) implements this.
    """

    @abstractmethod
    def get_name(self) -> str:
        """Return scenario name (e.g., 'sql_injection')."""
        pass

    @abstractmethod
    def get_techniques(self) -> List[str]:
        """
        Return list of technique IDs supported by this scenario.

        Example for SQL Injection:
            ["classic_sqli", "blind_sqli", "union_based", "nosql_injection"]

        Example for MITRE T1190:
            ["T1190.001", "T1190.002", "T1190.003"]
        """
        pass

    @abstractmethod
    def get_sub_techniques(self, technique: str) -> List[str]:
        """
        Return sub-techniques for a given technique.

        Example:
            get_sub_techniques("blind_sqli")
            → ["boolean_blind", "time_blind", "error_blind"]
        """
        pass

    @abstractmethod
    def get_mutators(self) -> List['Mutator']:
        """
        Return mutators for attack transformation.

        Example for SQL Injection:
            [
                StringObfuscationMutator(),
                EncodingMutator(encodings=["unicode", "hex", "base64"]),
                CommentInjectionMutator()
            ]
        """
        pass

    @abstractmethod
    def get_validators(self) -> Dict[str, 'Validator']:
        """
        Return validators for attack validation.

        Keys must include: "syntax", "semantic", "ground_truth", "scenario"

        Example:
            {
                "syntax": PythonSyntaxValidator(),
                "semantic": SQLInjectionSemanticValidator(),
                "ground_truth": GroundTruthValidator(),
                "scenario": SQLInjectionScenarioValidator()
            }
        """
        pass

    @abstractmethod
    def validate_attack(self, attack: 'Attack') -> bool:
        """
        Scenario-specific validation.
        Called after all validators pass.

        Returns:
            True if attack is valid for this scenario, False otherwise
        """
        pass

    @abstractmethod
    def score_detection(
        self,
        ground_truth: bool,
        prediction: bool,
        confidence: float
    ) -> 'DetectionScore':
        """
        Score Purple Agent's detection.

        Args:
            ground_truth: True if actually vulnerable
            prediction: Purple Agent's verdict
            confidence: Purple Agent's confidence (0-1)

        Returns:
            DetectionScore with outcome (TP/TN/FP/FN) and confidence
        """
        pass

    def load_dataset(self, dataset_path: str) -> List['Attack']:
        """
        Load test cases from dataset.

        Default implementation loads JSON files.
        Override for custom formats.
        """
        pass
```

### Mutator

```python
class Mutator(ABC):
    """Base interface for attack mutators (transformations)."""

    @abstractmethod
    def mutate(self, attack: 'Attack') -> 'Attack':
        """
        Apply mutation to attack.

        Args:
            attack: Original attack

        Returns:
            Mutated attack (new instance)

        Example:
            Original: query = f"SELECT * FROM users WHERE id={user_id}"
            Mutated:  query = "SEL" + "ECT * FROM users WHERE id=" + str(user_id)
        """
        pass

    @abstractmethod
    def get_mutation_type(self) -> str:
        """
        Return mutation type identifier.

        Examples: "string_obfuscation", "encoding", "comment_injection"
        """
        pass

    @property
    @abstractmethod
    def mutation_rate(self) -> float:
        """
        Probability of applying this mutation (0.0-1.0).

        Used by mutation engine to determine application frequency.
        """
        pass

    def can_mutate(self, attack: 'Attack') -> bool:
        """
        Check if this mutator can be applied to attack.

        Override to add constraints (e.g., only Python code).
        """
        return True
```

### Validator

```python
class Validator(ABC):
    """Base interface for attack validators."""

    @abstractmethod
    def validate(self, attack: 'Attack') -> 'ValidationResult':
        """
        Validate attack.

        Args:
            attack: Attack to validate

        Returns:
            ValidationResult with is_valid flag and details

        Example:
            SyntaxValidator checks if code compiles
            SemanticValidator checks if attack is realistic
            GroundTruthValidator verifies label is correct
        """
        pass

    @abstractmethod
    def get_validator_type(self) -> str:
        """
        Return validator type: "syntax", "semantic", "ground_truth", or "scenario"
        """
        pass
```

---

## Data Models

### Attack

```python
class Attack(BaseModel):
    """Represents a test attack/sample."""

    id: str                              # Unique identifier
    code: str                            # Code/payload to test
    language: str                        # Programming language (python, java, etc.)
    technique: str                       # Technique ID (classic_sqli, T1190, etc.)
    ground_truth: bool                   # True = vulnerable, False = safe
    metadata: Dict[str, Any] = {}        # Additional data
    generation: int = 0                  # For evolutionary tracking
    fitness_score: float = 0.0           # For evolutionary selection
    parent_ids: List[str] = []           # For tracking mutation lineage
```

### ValidationResult

```python
class ValidationResult(BaseModel):
    """Result of attack validation."""

    is_valid: bool                                    # Overall validation result
    validation_details: List[Tuple[str, bool]]        # (validator_name, passed)
    attack: Attack                                    # Original attack
    rejection_reason: Optional[str] = None            # If invalid, why?

    @property
    def passed_validators(self) -> List[str]:
        """Return list of validators that passed."""
        return [name for name, passed in self.validation_details if passed]

    @property
    def failed_validators(self) -> List[str]:
        """Return list of validators that failed."""
        return [name for name, passed in self.validation_details if not passed]
```

### DetectionScore

```python
class DetectionOutcome(str, Enum):
    TRUE_POSITIVE = "TP"   # Correctly detected vulnerable
    TRUE_NEGATIVE = "TN"   # Correctly detected safe
    FALSE_POSITIVE = "FP"  # Incorrectly flagged safe as vulnerable
    FALSE_NEGATIVE = "FN"  # Missed vulnerable code

class DetectionScore(BaseModel):
    """Score for a single detection."""

    outcome: DetectionOutcome
    confidence: float                    # Purple Agent's confidence
    ground_truth: bool
    prediction: bool
```

### TestResult

```python
class TestResult(BaseModel):
    """Result of testing an attack against Purple Agent."""

    test_case_id: str
    ground_truth: bool
    predicted: bool
    outcome: DetectionOutcome
    category: str                        # Technique category
    language: str
    confidence: float
    execution_time_ms: float
    purple_agent_response: 'PurpleAgentResponse'
```

### QualityScore

```python
class QualityScore(BaseModel):
    """Quality assessment from Judge Panel."""

    overall_score: float                 # 0.0-1.0
    technical_correctness: float         # 0.0-1.0
    explanation_clarity: float           # 0.0-1.0
    actionability: float                 # 0.0-1.0
    completeness: float                  # 0.0-1.0
    reasoning: str                       # LLM's reasoning
    identified_issues: List[str]         # Problems found
    strengths: List[str]                 # What was done well
    confidence: float                    # LLM's confidence in judgment
    judge_id: str                        # Which judge/arbitrator
```

---

## Agent Specifications

### MasterOrchestrator

```python
class MasterOrchestrator:
    """
    Top-level coordinator for multi-agent evaluation.

    Responsibilities:
    - Coordinate Red Team, Blue Team, Judge Panel
    - Manage evaluation phases
    - Allocate budget adaptively
    - Aggregate results
    """

    def __init__(
        self,
        scenario: SecurityScenario,
        enable_red_team: bool = True,
        enable_blue_team: bool = True,
        enable_judge_panel: bool = True
    ):
        self.scenario = scenario
        self.red_team = AdversarialRedTeam(scenario) if enable_red_team else None
        self.blue_team = ValidationBlueTeam(scenario) if enable_blue_team else None
        self.judge_panel = ConsensusJudgePanel() if enable_judge_panel else None
        self.budget_manager = BudgetManager()
        self.phase_tracker = PhaseTracker()

    async def evaluate(
        self,
        purple_agent: 'PurpleAgent',
        config: 'EvaluationConfig'
    ) -> 'EvaluationResult':
        """
        Main evaluation loop.

        Phases:
        1. Exploration: Diverse sampling to identify weak techniques
        2. Exploitation: Focus on weak techniques with Red Team attacks
        3. Validation: Confirm findings with Blue Team validation
        4. Quality Assessment: Judge Panel evaluates explanations

        Returns complete evaluation results.
        """
```

### AdversarialRedTeam

```python
class AdversarialRedTeam:
    """
    Adversarial agent for attack generation.

    Goals:
    - Find Purple Agent weaknesses
    - Generate evasions
    - Optimize attack effectiveness
    """

    def __init__(self, scenario: SecurityScenario):
        self.scenario = scenario
        self.mutation_engine = MutationEngine(scenario.get_mutators())
        self.boundary_learner = DecisionBoundaryLearner()
        self.fitness_evaluator = FitnessEvaluator()

    async def generate_attacks(
        self,
        purple_agent: 'PurpleAgent',
        technique: str,
        budget: int,
        generations: int = 5
    ) -> List[Attack]:
        """
        Generate adversarial attacks using evolutionary optimization.

        Process:
        1. Probe Purple Agent decision boundaries
        2. Generate initial population
        3. Evolve over N generations:
           - Test population
           - Calculate fitness
           - Select best
           - Mutate and crossover
        4. Return highest-fitness attacks

        Fitness function:
        - Evasion success (40%): Did Purple Agent fail to detect?
        - Boundary proximity (30%): How close to decision boundary?
        - Novelty (20%): Different from previous attacks?
        - Validity (10%): Will Blue Team accept it?
        """
```

### ValidationBlueTeam

```python
class ValidationBlueTeam:
    """
    Validation agent for ensuring attack realism.

    Goals:
    - Prevent unrealistic attacks
    - Ensure ground truth correctness
    - Maintain evaluation integrity
    """

    def __init__(self, scenario: SecurityScenario):
        self.scenario = scenario
        self.validators = scenario.get_validators()
        self.validation_stats = ValidationStatistics()

    async def validate_attack(self, attack: Attack) -> ValidationResult:
        """
        Validate attack through multiple validators.

        Validation chain:
        1. Syntax: Does code compile/run?
        2. Semantic: Is it realistic/plausible?
        3. Ground Truth: Is label correct?
        4. Scenario: Fits threat model?

        ALL must pass for attack to be valid.
        """

    async def validate_all(
        self,
        attacks: List[Attack]
    ) -> List['ValidatedAttack']:
        """
        Validate all attacks in parallel.

        Returns only validated attacks.
        Logs rejection reasons for invalid attacks.
        """
```

### ConsensusJudgePanel

```python
class ConsensusJudgePanel:
    """
    Multi-LLM consensus panel for quality evaluation.

    Goals:
    - Reduce LLM bias
    - Assess explanation quality
    - Provide nuanced feedback
    """

    def __init__(
        self,
        judges: Optional[List['LLMJudge']] = None,
        consensus_threshold: float = 0.2
    ):
        self.judges = judges or [
            LLMJudge(provider="anthropic", model="claude-3-5-sonnet"),
            LLMJudge(provider="openai", model="gpt-4"),
            LLMJudge(provider="google", model="gemini-pro")
        ]
        self.arbitrator = LLMJudge(provider="anthropic", model="claude-opus")
        self.consensus_threshold = consensus_threshold

    async def evaluate_quality(
        self,
        validated_attacks: List['ValidatedAttack']
    ) -> 'QualityScores':
        """
        Evaluate Purple Agent response quality.

        Process:
        1. All judges score in parallel
        2. Check for consensus (scores within threshold)
        3. If consensus: Use average
        4. If disagreement: Spawn arbitrator for debate
        5. Return final quality scores

        Scoring dimensions:
        - Technical correctness
        - Explanation clarity
        - Actionability
        - Completeness
        """
```

---

## Evaluation Flow

```python
async def run_evaluation(
    orchestrator: MasterOrchestrator,
    purple_agent: PurpleAgent,
    config: EvaluationConfig
) -> EvaluationResult:
    """
    Complete evaluation workflow.

    1. Exploration Phase:
       - Sample diverse tests
       - Test Purple Agent
       - Identify weak techniques

    2. Red Team Phase:
       - Generate adversarial attacks for weak techniques
       - Evolve attacks over generations
       - Select highest-fitness attacks

    3. Blue Team Phase:
       - Validate all Red Team attacks
       - Filter unrealistic attacks
       - Ensure ground truth correctness

    4. Testing Phase:
       - Test validated attacks
       - Collect Purple Agent responses
       - Record results

    5. Judge Panel Phase (if enabled):
       - Evaluate explanation quality
       - Multi-LLM consensus
       - Quality scoring

    6. Aggregation Phase:
       - Compute detection metrics (F1, Precision, Recall)
       - Compute quality metrics
       - Compute adversarial robustness
       - Identify weak/strong categories

    Returns:
        EvaluationResult with comprehensive metrics
    """
```

---

## Configuration

### EvaluationConfig

```python
class EvaluationMode(str, Enum):
    FIXED = "fixed"              # Predetermined test set
    ADAPTIVE = "adaptive"        # Adaptive allocation

class EvaluationConfig(BaseModel):
    """Configuration for evaluation."""

    mode: EvaluationMode = EvaluationMode.ADAPTIVE
    test_budget: int = 100
    timeout_seconds: int = 300
    per_test_timeout_seconds: float = 10.0

    # Red Team config
    enable_red_team: bool = True
    red_team_budget_percentage: float = 0.5   # 50% of budget for adversarial
    evolution_generations: int = 5

    # Blue Team config
    enable_blue_team: bool = True
    min_validation_rate: float = 0.9          # Warn if <90% validation rate

    # Judge Panel config
    enable_judge_panel: bool = True
    llm_providers: List[str] = ["anthropic", "openai", "google"]

    # Adaptive config
    adaptive_config: Optional[AdaptiveConfig] = None
    random_seed: Optional[int] = None
    categories_to_test: Optional[List[str]] = None
    languages_to_test: Optional[List[str]] = None
```

---

## Extension Points

### Adding a New Mutator

```python
from framework.base import Mutator, Attack

class UnicodeEscapeMutator(Mutator):
    """Mutates strings to use Unicode escapes."""

    def mutate(self, attack: Attack) -> Attack:
        mutated_code = self._unicode_escape(attack.code)
        return attack.copy(update={"code": mutated_code, "generation": attack.generation + 1})

    def get_mutation_type(self) -> str:
        return "unicode_escape"

    @property
    def mutation_rate(self) -> float:
        return 0.3  # Apply to 30% of attacks

    def _unicode_escape(self, code: str) -> str:
        # Implementation
        pass
```

### Adding a New Validator

```python
from framework.base import Validator, Attack, ValidationResult

class RealisticContextValidator(Validator):
    """Validates attacks have realistic context."""

    def validate(self, attack: Attack) -> ValidationResult:
        is_valid = self._check_realism(attack)

        return ValidationResult(
            is_valid=is_valid,
            validation_details=[("realistic_context", is_valid)],
            attack=attack,
            rejection_reason=None if is_valid else "Lacks realistic context"
        )

    def get_validator_type(self) -> str:
        return "semantic"

    def _check_realism(self, attack: Attack) -> bool:
        # Implementation
        pass
```

---

**Previous:** [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture diagrams
**Next:** [INTEGRATION.md](INTEGRATION.md) - Integration guide
