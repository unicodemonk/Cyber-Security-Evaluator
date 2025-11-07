# Advanced Multi-Agent Framework Architecture

**Version:** 1.0
**Date:** November 2025
**Status:** Design Phase

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Component Diagrams](#component-diagrams)
3. [Data Flow](#data-flow)
4. [Sequence Diagrams](#sequence-diagrams)
5. [Technology Stack](#technology-stack)
6. [Design Patterns](#design-patterns)

---

## System Architecture

### High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                         External Systems                            │
├─────────────────┬──────────────────────┬──────────────────────────┤
│  Purple Agent   │   LLM Providers      │   MITRE ATT&CK Database  │
│  (A2A Protocol) │  (Claude, GPT, Gemini)│   (Technique Mappings)   │
└─────────────────┴──────────────────────┴──────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────────┐
│                     A2A Server Interface                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  AgentCard   │  │ Task Handler │  │ HTTP Server  │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────────┐
│                   Master Orchestrator Layer                         │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              MasterOrchestrator                               │ │
│  │  - Evaluation coordination                                    │ │
│  │  - Budget management                                          │ │
│  │  - Phase transitions (Exploration → Exploitation → Validation)│ │
│  │  - Early termination logic                                    │ │
│  │  - Results aggregation                                        │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   Red Team       │ │   Blue Team      │ │   Judge Panel    │
│   Agent Layer    │ │   Agent Layer    │ │   Agent Layer    │
└──────────────────┘ └──────────────────┘ └──────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                   Core Engine Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  Mutation    │  │  Boundary    │  │   Fitness    │            │
│  │  Engine      │  │  Learner     │  │   Evaluator  │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────────┐
│                  Specialist Layer (Technique-Specific)              │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ SQL Injection│  │    DDoS      │  │  Phishing    │            │
│  │  Specialist  │  │  Specialist  │  │  Specialist  │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│         │                 │                 │                      │
│         └─────────────────┴─────────────────┘                      │
│                           │                                        │
│                  ┌────────┴────────┐                              │
│                  ▼                 ▼                               │
│         ┌──────────────┐  ┌──────────────┐                       │
│         │ Micro Agent  │  │ Micro Agent  │                       │
│         │  (Boolean    │  │  (Time-based │                       │
│         │   Blind)     │  │    Blind)    │                       │
│         └──────────────┘  └──────────────┘                       │
└────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────────┐
│                    Shared Services Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  Dataset     │  │     LLM      │  │   Scoring    │            │
│  │  Manager     │  │ Integration  │  │   Engine     │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  Validator   │  │   Mutator    │  │    Logger    │            │
│  │   Registry   │  │   Registry   │  │              │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└────────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────────┐
│                      Data Layer                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  Test Cases  │  │ Ground Truth │  │   Results    │            │
│  │   (JSON)     │  │   (JSON)     │  │  (Database)  │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└────────────────────────────────────────────────────────────────────┘
```

---

## Component Diagrams

### Master Orchestrator Component

```
┌───────────────────────────────────────────────────────────────────┐
│                      MasterOrchestrator                            │
├───────────────────────────────────────────────────────────────────┤
│  Attributes:                                                       │
│  - scenario: SecurityScenario                                     │
│  - red_team: AdversarialRedTeam                                   │
│  - blue_team: ValidationBlueTeam                                  │
│  - judge_panel: ConsensusJudgePanel                               │
│  - specialists: Dict[str, SpecialistAgent]                        │
│  - budget_manager: BudgetManager                                  │
│  - phase_tracker: PhaseTracker                                    │
├───────────────────────────────────────────────────────────────────┤
│  Methods:                                                          │
│  + evaluate(purple_agent) → EvaluationResult                      │
│  + _exploration_phase() → ExplorationResults                      │
│  + _exploitation_phase() → ExploitationResults                    │
│  + _validation_phase() → ValidationResults                        │
│  + _identify_weaknesses() → List[str]                            │
│  + _spawn_specialists(techniques) → Dict[str, SpecialistAgent]   │
│  + _aggregate_results() → EvaluationResult                        │
│  - _check_early_termination() → Tuple[bool, str]                 │
│  - _allocate_budget() → BudgetAllocation                          │
└───────────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│BudgetManager │  │ PhaseTracker │  │ResultsAggr.  │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Red Team Component

```
┌───────────────────────────────────────────────────────────────────┐
│                    AdversarialRedTeam                              │
├───────────────────────────────────────────────────────────────────┤
│  Attributes:                                                       │
│  - scenario: SecurityScenario                                     │
│  - mutation_engine: MutationEngine                                │
│  - boundary_learner: DecisionBoundaryLearner                      │
│  - attack_history: List[Attack]                                   │
│  - fitness_evaluator: FitnessEvaluator                            │
├───────────────────────────────────────────────────────────────────┤
│  Methods:                                                          │
│  + generate_attacks(purple_agent, technique, budget) → List[Attack]│
│  + evolve_population(population, fitness) → List[Attack]          │
│  - _evaluate_fitness(attacks, purple_agent) → List[float]         │
│  - _calculate_novelty(attack) → float                             │
│  - _probe_boundaries(purple_agent) → DecisionBoundaries          │
└───────────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Mutation    │  │  Boundary    │  │   Fitness    │
│  Engine      │  │  Learner     │  │  Evaluator   │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Blue Team Component

```
┌───────────────────────────────────────────────────────────────────┐
│                   ValidationBlueTeam                               │
├───────────────────────────────────────────────────────────────────┤
│  Attributes:                                                       │
│  - scenario: SecurityScenario                                     │
│  - validators: Dict[str, Validator]                               │
│  - validation_stats: ValidationStatistics                         │
├───────────────────────────────────────────────────────────────────┤
│  Methods:                                                          │
│  + validate_attack(attack) → ValidationResult                     │
│  + validate_all(attacks) → List[ValidatedAttack]                  │
│  - _load_validators() → Dict[str, Validator]                      │
│  - _aggregate_validations() → bool                                │
└───────────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Syntax     │  │  Semantic    │  │Ground Truth  │
│  Validator   │  │  Validator   │  │  Validator   │
└──────────────┘  └──────────────┘  └──────────────┘
```

### Judge Panel Component

```
┌───────────────────────────────────────────────────────────────────┐
│                   ConsensusJudgePanel                              │
├───────────────────────────────────────────────────────────────────┤
│  Attributes:                                                       │
│  - judges: List[LLMJudge]                                         │
│  - arbitrator: LLMJudge                                           │
│  - consensus_threshold: float = 0.2                               │
├───────────────────────────────────────────────────────────────────┤
│  Methods:                                                          │
│  + evaluate_quality(attacks) → QualityScores                      │
│  - _has_consensus(judgments) → bool                               │
│  - _average_judgments(judgments) → QualityScore                   │
│  - _spawn_arbitrator(attack, judgments) → QualityScore           │
└───────────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Claude Judge │  │  GPT-4 Judge │  │ Gemini Judge │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                 │
        └─────────────────┴─────────────────┘
                          │
                          ▼
                ┌──────────────────┐
                │    Arbitrator    │
                │  (Claude Opus)   │
                └──────────────────┘
```

### Specialist Component

```
┌───────────────────────────────────────────────────────────────────┐
│                     SpecialistAgent                                │
├───────────────────────────────────────────────────────────────────┤
│  Attributes:                                                       │
│  - technique: str                                                  │
│  - scenario: SecurityScenario                                     │
│  - red_team: AdversarialRedTeam                                   │
│  - blue_team: ValidationBlueTeam                                  │
│  - micro_agents: List[MicroAgent]                                 │
│  - domain_knowledge: TechniqueKnowledge                           │
├───────────────────────────────────────────────────────────────────┤
│  Methods:                                                          │
│  + evaluate_deep(purple_agent, budget) → SpecialistResults        │
│  - _spawn_micro_agents() → List[MicroAgent]                       │
│  - _test_attacks(purple_agent, attacks) → List[TestResult]        │
│  - _aggregate_results() → SpecialistResults                       │
└───────────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        ▼                                   ▼
┌──────────────────┐              ┌──────────────────┐
│  MicroAgent 1    │              │  MicroAgent 2    │
│ (Boolean Blind)  │              │ (Time-based)     │
└──────────────────┘              └──────────────────┘
```

---

## Data Flow

### Evaluation Data Flow

```
1. Initialization
   ┌──────────────┐
   │ User Request │
   └──────┬───────┘
          │
          ▼
   ┌──────────────────┐
   │  Load Scenario   │
   │  Configuration   │
   └──────┬───────────┘
          │
          ▼
   ┌──────────────────┐
   │ Spawn Agents     │
   │ - Red Team       │
   │ - Blue Team      │
   │ - Judge Panel    │
   │ - Specialists    │
   └──────┬───────────┘

2. Exploration Phase
          │
          ▼
   ┌──────────────────┐
   │ Sample diverse   │
   │   test cases     │
   └──────┬───────────┘
          │
          ▼
   ┌──────────────────┐
   │ Send to Purple   │
   │     Agent        │
   └──────┬───────────┘
          │
          ▼
   ┌──────────────────┐
   │ Collect results  │
   └──────┬───────────┘
          │
          ▼
   ┌──────────────────┐
   │ Identify weak    │
   │  categories      │
   └──────┬───────────┘

3. Exploitation Phase
          │
          ▼
   ┌──────────────────┐
   │ Red Team:        │
   │ Generate attacks │
   │ for weak areas   │
   └──────┬───────────┘
          │
          ▼
   ┌──────────────────┐
   │ Blue Team:       │
   │ Validate attacks │
   └──────┬───────────┘
          │
          ▼
   ┌──────────────────┐
   │ Test validated   │
   │ attacks          │
   └──────┬───────────┘
          │
          ▼
   ┌──────────────────┐
   │ Judge Panel:     │
   │ Evaluate quality │
   └──────┬───────────┘

4. Results Aggregation
          │
          ▼
   ┌──────────────────┐
   │ Aggregate all    │
   │    results       │
   └──────┬───────────┘
          │
          ▼
   ┌──────────────────┐
   │ Compute metrics  │
   │ - F1, Precision  │
   │ - Quality scores │
   │ - Robustness     │
   └──────┬───────────┘
          │
          ▼
   ┌──────────────────┐
   │ Return results   │
   └──────────────────┘
```

### Attack Generation Flow (Red Team)

```
Purple Agent ──┐
               │
               ├───► Red Team: Probe boundaries
               │           │
               │           ▼
               │     ┌──────────────────┐
               │     │ Initial population│
               │     │  (baseline tests) │
               │     └─────────┬─────────┘
               │               │
               │               ▼
               │     ┌─────────────────┐
               │     │  Generation 1   │
               │     │  Apply mutations│
               │     └─────────┬───────┘
               │               │
               ├───────────────┤ Test against Purple Agent
               │               │
               │               ▼
               │     ┌─────────────────┐
               │     │ Fitness scoring │
               │     └─────────┬───────┘
               │               │
               │               ▼
               │     ┌─────────────────┐
               │     │  Select best    │
               │     │  (top 50%)      │
               │     └─────────┬───────┘
               │               │
               │               ▼
               │     ┌─────────────────┐
               │     │  Generation 2   │
               │     │  Evolve attacks │
               │     └─────────┬───────┘
               │               │
               │               ▼
               │          ... repeat N times ...
               │               │
               │               ▼
               │     ┌─────────────────┐
               │     │  Final attacks  │
               │     │  (highest fitness)│
               │     └─────────┬───────┘
               │               │
               └───────────────┘
                               │
                               ▼
                     ┌──────────────────┐
                     │  Blue Team:      │
                     │  Validate        │
                     └──────────────────┘
```

### Validation Flow (Blue Team)

```
Attack ──────► Syntax Validator ────► Valid? ──No──► Reject
                      │                    │
                      │                   Yes
                      ▼                    │
              Semantic Validator ──────────┤
                      │                    │
                      ▼                    │
              Ground Truth Validator ──────┤
                      │                    │
                      ▼                    │
              Scenario Validator ──────────┤
                      │                    │
                      ▼                    │
              All Pass? ──────────────────┘
                      │
                     Yes
                      │
                      ▼
              Validated Attack
```

---

## Sequence Diagrams

### Full Evaluation Sequence

```
User          Orchestrator    Red Team    Blue Team    Purple Agent    Judge Panel
 │                 │              │            │              │              │
 │ Evaluate       │              │            │              │              │
 ├───────────────>│              │            │              │              │
 │                │              │            │              │              │
 │                │ Exploration  │            │              │              │
 │                ├─────────────────────────────────────────>│              │
 │                │              │            │              │              │
 │                │<─────────────────────────────────────────┤              │
 │                │ Results      │            │              │              │
 │                │              │            │              │              │
 │                │ Generate attacks          │              │              │
 │                ├────────────>│             │              │              │
 │                │              │            │              │              │
 │                │              │ Validate   │              │              │
 │                │              ├──────────>│              │              │
 │                │              │            │              │              │
 │                │              │<───────────┤              │              │
 │                │              │ Validated  │              │              │
 │                │              │            │              │              │
 │                │ Test attacks              │              │              │
 │                ├─────────────────────────────────────────>│              │
 │                │              │            │              │              │
 │                │<─────────────────────────────────────────┤              │
 │                │ Results      │            │              │              │
 │                │              │            │              │              │
 │                │ Evaluate quality                         │              │
 │                ├────────────────────────────────────────────────────────>│
 │                │              │            │              │              │
 │                │<────────────────────────────────────────────────────────┤
 │                │ Quality scores            │              │              │
 │                │              │            │              │              │
 │<───────────────┤              │            │              │              │
 │  Final Results │              │            │              │              │
```

### Red Team Attack Generation

```
Orchestrator    Red Team    Mutation Engine    Boundary Learner    Purple Agent
     │              │               │                   │                │
     │ Generate     │               │                   │                │
     ├────────────>│               │                   │                │
     │              │               │                   │                │
     │              │ Learn boundaries                  │                │
     │              ├───────────────────────────────────────────────────>│
     │              │               │                   │                │
     │              │<───────────────────────────────────────────────────┤
     │              │ Boundaries    │                   │                │
     │              │               │                   │                │
     │              │ Generate initial population       │                │
     │              ├─────────────>│                   │                │
     │              │               │                   │                │
     │              │<──────────────┤                   │                │
     │              │ Population    │                   │                │
     │              │               │                   │                │
     │              │ Test population                   │                │
     │              ├───────────────────────────────────────────────────>│
     │              │               │                   │                │
     │              │<───────────────────────────────────────────────────┤
     │              │ Responses     │                   │                │
     │              │               │                   │                │
     │              │ Evolve best   │                   │                │
     │              ├─────────────>│                   │                │
     │              │               │                   │                │
     │              │<──────────────┤                   │                │
     │              │ Next generation                   │                │
     │              │               │                   │                │
     │              │ ... repeat N times ...            │                │
     │              │               │                   │                │
     │<─────────────┤               │                   │                │
     │ Final attacks│               │                   │                │
```

### Multi-LLM Consensus

```
Orchestrator    Judge Panel    Claude    GPT-4    Gemini    Arbitrator
     │              │             │         │        │           │
     │ Evaluate     │             │         │        │           │
     ├────────────>│             │         │        │           │
     │              │             │         │        │           │
     │              │ Evaluate    │         │        │           │
     │              ├───────────>│         │        │           │
     │              ├─────────────────────>│        │           │
     │              ├───────────────────────────────>│           │
     │              │             │         │        │           │
     │              │<────────────┤         │        │           │
     │              │ Score: 0.8  │         │        │           │
     │              │<──────────────────────┤        │           │
     │              │ Score: 0.5  │         │        │           │
     │              │<────────────────────────────────┤           │
     │              │ Score: 0.7  │         │        │           │
     │              │             │         │        │           │
     │              │ Disagreement detected │        │           │
     │              │             │         │        │           │
     │              │ Arbitrate                      │           │
     │              ├─────────────────────────────────────────────>│
     │              │             │         │        │           │
     │              │<─────────────────────────────────────────────┤
     │              │ Final: 0.7  │         │        │           │
     │              │             │         │        │           │
     │<─────────────┤             │         │        │           │
     │ Quality score│             │         │        │           │
```

---

## Technology Stack

### Programming Languages
```
┌─────────────────┬──────────────────────────────────────────┐
│ Language        │ Usage                                     │
├─────────────────┼──────────────────────────────────────────┤
│ Python 3.11+    │ Primary implementation language           │
│ SQL             │ Results database (optional)               │
│ JSON/YAML       │ Configuration and data storage            │
└─────────────────┴──────────────────────────────────────────┘
```

### Core Libraries
```
┌─────────────────────┬──────────────────────────────────────┐
│ Library             │ Purpose                               │
├─────────────────────┼──────────────────────────────────────┤
│ Pydantic 2.x        │ Data validation and modeling          │
│ httpx               │ Async HTTP client                     │
│ asyncio             │ Asynchronous execution                │
│ agentbeats          │ A2A protocol framework                │
│ anthropic/openai    │ LLM provider SDKs                     │
│ numpy               │ Numerical computations                │
│ scikit-learn        │ Metrics calculations                  │
└─────────────────────┴──────────────────────────────────────┘
```

### Infrastructure
```
┌─────────────────────┬──────────────────────────────────────┐
│ Component           │ Technology                            │
├─────────────────────┼──────────────────────────────────────┤
│ Web Server          │ Uvicorn (ASGI)                        │
│ API Framework       │ Starlette                             │
│ Data Storage        │ JSON files + Optional SQLite/Postgres │
│ Logging             │ Python logging + structlog            │
│ Testing             │ pytest + pytest-asyncio               │
│ Type Checking       │ mypy                                  │
│ Code Quality        │ ruff                                  │
└─────────────────────┴──────────────────────────────────────┘
```

---

## Design Patterns

### 1. Strategy Pattern
```python
# Different mutation strategies can be swapped
class Mutator(ABC):
    @abstractmethod
    def mutate(self, attack: Attack) -> Attack:
        pass

class StringObfuscationMutator(Mutator):
    def mutate(self, attack: Attack) -> Attack:
        # Obfuscate strings in attack
        pass

class EncodingMutator(Mutator):
    def mutate(self, attack: Attack) -> Attack:
        # Apply encoding transformations
        pass

# Usage
mutation_engine.add_mutator(StringObfuscationMutator())
mutation_engine.add_mutator(EncodingMutator())
```

### 2. Template Method Pattern
```python
class SpecialistAgent(ABC):
    def evaluate_deep(self, purple_agent, budget):
        # Template method
        self._setup()
        micro_results = self._evaluate_micro_agents(purple_agent)
        adversarial = self._generate_adversarial(purple_agent, budget)
        return self._aggregate_results(micro_results, adversarial)

    @abstractmethod
    def _setup(self):
        """Subclass-specific setup"""
        pass

    @abstractmethod
    def _evaluate_micro_agents(self, purple_agent):
        """Subclass-specific evaluation"""
        pass
```

### 3. Factory Pattern
```python
class ScenarioFactory:
    @staticmethod
    def create_scenario(scenario_type: str) -> SecurityScenario:
        if scenario_type == "sql_injection":
            return SQLInjectionScenario()
        elif scenario_type == "ddos":
            return DDoSScenario()
        elif scenario_type.startswith("mitre_"):
            technique_id = scenario_type.split("_")[1]
            return MITREScenario(technique_id)
        else:
            raise ValueError(f"Unknown scenario: {scenario_type}")
```

### 4. Observer Pattern
```python
class EvaluationObserver(ABC):
    @abstractmethod
    def on_phase_change(self, new_phase: TestPhase):
        pass

    @abstractmethod
    def on_test_complete(self, result: TestResult):
        pass

class Orchestrator:
    def __init__(self):
        self.observers = []

    def attach(self, observer: EvaluationObserver):
        self.observers.append(observer)

    def _notify_phase_change(self, phase):
        for observer in self.observers:
            observer.on_phase_change(phase)
```

### 5. Chain of Responsibility Pattern
```python
class Validator(ABC):
    def __init__(self):
        self.next_validator = None

    def set_next(self, validator: 'Validator'):
        self.next_validator = validator
        return validator

    def validate(self, attack: Attack) -> ValidationResult:
        result = self._validate(attack)
        if result.is_valid and self.next_validator:
            return self.next_validator.validate(attack)
        return result

    @abstractmethod
    def _validate(self, attack: Attack) -> ValidationResult:
        pass

# Usage
syntax_validator = SyntaxValidator()
semantic_validator = SemanticValidator()
ground_truth_validator = GroundTruthValidator()

syntax_validator.set_next(semantic_validator).set_next(ground_truth_validator)
result = syntax_validator.validate(attack)
```

---

## Component Interfaces

### SecurityScenario Interface
```python
class SecurityScenario(ABC):
    """Base interface for all security scenarios."""

    @abstractmethod
    def get_techniques(self) -> List[str]:
        """Return list of technique IDs."""
        pass

    @abstractmethod
    def get_sub_techniques(self, technique: str) -> List[str]:
        """Return sub-techniques for a technique."""
        pass

    @abstractmethod
    def get_mutators(self) -> List[Mutator]:
        """Return mutators for this scenario."""
        pass

    @abstractmethod
    def get_validators(self) -> List[Validator]:
        """Return validators for this scenario."""
        pass

    @abstractmethod
    def validate_attack(self, attack: Attack) -> bool:
        """Scenario-specific validation."""
        pass

    @abstractmethod
    def score_detection(
        self,
        ground_truth: bool,
        prediction: bool
    ) -> DetectionScore:
        """Score Purple Agent's detection."""
        pass
```

### Mutator Interface
```python
class Mutator(ABC):
    """Base interface for attack mutators."""

    @abstractmethod
    def mutate(self, attack: Attack) -> Attack:
        """Apply mutation to attack."""
        pass

    @abstractmethod
    def get_mutation_type(self) -> str:
        """Return mutation type identifier."""
        pass

    @property
    @abstractmethod
    def mutation_rate(self) -> float:
        """Probability of applying this mutation (0-1)."""
        pass
```

### Validator Interface
```python
class Validator(ABC):
    """Base interface for attack validators."""

    @abstractmethod
    def validate(self, attack: Attack) -> ValidationResult:
        """Validate attack and return result."""
        pass

    @abstractmethod
    def get_validator_type(self) -> str:
        """Return validator type identifier."""
        pass
```

---

## Data Models

### Core Data Models
```python
class Attack(BaseModel):
    """Represents a test attack."""
    id: str
    code: str
    language: str
    technique: str
    ground_truth: bool  # True = vulnerable, False = safe
    metadata: Dict[str, Any] = {}
    generation: int = 0  # For evolutionary tracking
    fitness_score: float = 0.0

class ValidationResult(BaseModel):
    """Result of attack validation."""
    is_valid: bool
    validation_details: List[Tuple[str, bool]]  # (validator_name, passed)
    attack: Attack
    rejection_reason: Optional[str] = None

class TestResult(BaseModel):
    """Result of testing attack against Purple Agent."""
    test_case_id: str
    ground_truth: bool
    predicted: bool
    outcome: DetectionOutcome
    category: str
    language: str
    confidence: float
    execution_time_ms: float
    purple_agent_response: PurpleAgentResponse

class QualityScore(BaseModel):
    """Quality assessment from Judge Panel."""
    overall_score: float
    technical_correctness: float
    explanation_clarity: float
    actionability: float
    completeness: float
    reasoning: str
    identified_issues: List[str]
    strengths: List[str]
    confidence: float

class EvaluationResult(BaseModel):
    """Final evaluation results."""
    success: bool
    tests_executed: int
    execution_time_seconds: float
    metrics: Metrics
    quality_scores: Optional[QualityScores] = None
    adversarial_robustness: Optional[float] = None
    weak_techniques: List[str]
    strong_techniques: List[str]
    error_message: Optional[str] = None
```

---

**Next:** See [SPECIFICATION.md](SPECIFICATION.md) for detailed technical specifications
**Related:** See [EVOLUTION.md](EVOLUTION.md) for framework evolution roadmap
