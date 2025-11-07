# Framework Evolution Roadmap

**Version:** 1.0
**Date:** November 2025
**Status:** Design Phase

---

## Table of Contents

1. [Evolution Philosophy](#evolution-philosophy)
2. [Phase-by-Phase Roadmap](#phase-by-phase-roadmap)
3. [Scenario Extension Strategy](#scenario-extension-strategy)
4. [MITRE ATT&CK Integration](#mitre-attck-integration)
5. [Scaling Strategy](#scaling-strategy)
6. [Future Enhancements](#future-enhancements)

---

## Evolution Philosophy

###

 Design Principles

**1. Extensibility Over Feature-Complete**
```
❌ Build everything upfront
✅ Build extensible foundation → Add scenarios incrementally
```

**2. Validate with Real Scenarios**
```
❌ Theoretical perfection
✅ Ship SQL Injection → Learn → Improve → Add DDoS
```

**3. Backward Compatibility**
```
Every new scenario should work without changing existing ones
```

**4. Progressive Enhancement**
```
Core framework → Advanced features → Optimization → Scale
```

---

## Phase-by-Phase Roadmap

### **Phase 0: Foundation (CURRENT)**
**Status:** ✅ Complete
**Duration:** Completed
**Goal:** SQL Injection scenario fully functional

#### Deliverables
- ✅ SQLInjectionJudge (Green Agent)
- ✅ Dataset management
- ✅ Scoring engine (F1, Precision, Recall)
- ✅ Adaptive test allocation
- ✅ LLM integration (optional)
- ✅ A2A protocol compliance
- ✅ 36 passing tests

#### Artifacts
```
scenarios/security/
├── sql_injection_judge.py    # Main green agent
├── dataset_manager.py         # Dataset handling
├── scoring_engine.py          # Metrics calculation
├── adaptive_planner.py        # Adaptive allocation
└── models.py                  # Data models
```

---

### **Phase 1: Framework Abstraction**
**Status:** 🔄 Design Phase
**Duration:** 4-6 weeks
**Goal:** Extract reusable framework from SQL Injection

#### Week 1-2: Base Abstractions
```python
# framework/base.py
class SecurityScenario(ABC):
    """Universal interface for all scenarios"""

class Mutator(ABC):
    """Base for attack mutations"""

class Validator(ABC):
    """Base for attack validation"""

class MicroAgent(ABC):
    """Base for sub-technique agents"""
```

**Deliverables:**
- [ ] `framework/base.py` - Abstract base classes
- [ ] `framework/orchestrator.py` - MasterOrchestrator
- [ ] `framework/models.py` - Universal data models
- [ ] Refactor SQLInjectionJudge to use framework

**Success Criteria:**
- SQLInjectionJudge works using framework abstractions
- 0 breaking changes to existing functionality
- All 36 tests still pass

#### Week 3-4: Red/Blue Team Agents
```python
# framework/red_team.py
class AdversarialRedTeam:
    def generate_attacks(...)
    def evolve_population(...)

# framework/blue_team.py
class ValidationBlueTeam:
    def validate_attack(...)
    def validate_all(...)
```

**Deliverables:**
- [ ] `framework/red_team.py` - Adversarial agent
- [ ] `framework/blue_team.py` - Validation agent
- [ ] `framework/engines/mutation_engine.py`
- [ ] `framework/engines/boundary_learner.py`

**Success Criteria:**
- Red Team generates attacks with fitness > 0.7
- Blue Team validation rate > 90%

#### Week 5-6: Judge Panel & Specialists
```python
# framework/judge_panel.py
class ConsensusJudgePanel:
    def evaluate_quality(...)

# framework/specialist.py
class SpecialistAgent:
    def evaluate_deep(...)
    def spawn_micro_agents(...)
```

**Deliverables:**
- [ ] `framework/judge_panel.py`
- [ ] `framework/specialist.py`
- [ ] Multi-LLM consensus implementation
- [ ] Hierarchical specialist spawning

**Success Criteria:**
- Multi-LLM consensus > 85%
- Specialists spawn micro-agents successfully

---

### **Phase 2: Validation with Second Scenario**
**Status:** 🔄 Planned
**Duration:** 2-3 weeks
**Goal:** Prove framework extensibility with Command Injection

#### Why Command Injection?
- Similar to SQL Injection (injection attack)
- Different domain (OS commands vs database)
- Tests framework flexibility
- Reuses mutation patterns

#### Implementation
```python
# scenarios/command_injection/scenario.py
class CommandInjectionScenario(SecurityScenario):
    def get_techniques(self):
        return ["classic_command", "blind_command", "code_injection"]

    def get_mutators(self):
        return [
            ShellMetacharacterMutator(),
            CommandChaining Mutator(),
            EncodingMutator()
        ]
```

**Deliverables:**
- [ ] `scenarios/command_injection/scenario.py`
- [ ] `scenarios/command_injection/mutators.py`
- [ ] `scenarios/command_injection/validators.py`
- [ ] Dataset (50+ test cases)
- [ ] Techniques: classic, blind, code injection

**Success Criteria:**
- Scenario added in <200 lines of code
- No framework code changes required
- Both SQL and Command Injection run via same orchestrator

---

### **Phase 3: Advanced Agent Features**
**Status:** 🔄 Planned
**Duration:** 6-8 weeks
**Goal:** Implement full multi-agent capabilities

#### Advanced Features

**1. Evolutionary Mutation Engine** (Weeks 1-2)
```python
class MutationEngine:
    def evolve_population(self, population, fitness_scores):
        # Genetic algorithm
        # Selection → Crossover → Mutation → Evaluation
        pass
```

**2. Decision Boundary Learning** (Weeks 3-4)
```python
class DecisionBoundaryLearner:
    def find_boundaries(self, purple_agent):
        # Probe Purple Agent
        # Identify decision regions
        # Return boundary coordinates
        pass
```

**3. Multi-LLM Arbitration** (Weeks 5-6)
```python
class ConsensusJudgePanel:
    def evaluate_with_arbitration(self, attacks):
        # Parallel LLM evaluation
        # Detect disagreement
        # Spawn arbitrator
        # Return consensus
        pass
```

**4. Hierarchical Specialists** (Weeks 7-8)
```python
class SpecialistAgent:
    def spawn_micro_agents(self):
        # Deep technique expertise
        # Sub-pattern testing
        # Coordinated results
        pass
```

**Success Criteria:**
- Evolutionary engine improves fitness by 5% per generation
- Boundary learning finds decision regions with <10 probes
- Judge panel consensus > 85%
- Specialists provide technique-specific insights

---

### **Phase 4: Scenario Expansion**
**Status:** 🔄 Planned
**Duration:** 12 weeks (3 scenarios × 4 weeks each)
**Goal:** Expand to diverse security domains

#### Scenario 1: DDoS Detection (Weeks 1-4)
```
Techniques:
- Volumetric (UDP flood, ICMP flood, DNS amplification)
- Protocol (SYN flood, ACK flood, fragmentation)
- Application Layer (HTTP flood, Slowloris, RUDY)
```

**Deliverables:**
- [ ] DDoSScenario class
- [ ] Traffic pattern mutators
- [ ] Realistic traffic validators
- [ ] Dataset (100+ traffic patterns)

#### Scenario 2: Phishing Detection (Weeks 5-8)
```
Techniques:
- Spear phishing
- Whaling
- Clone phishing
- Business Email Compromise (BEC)
```

**Deliverables:**
- [ ] PhishingScenario class
- [ ] Email content mutators
- [ ] Realism validators
- [ ] Dataset (200+ emails)

#### Scenario 3: XSS Detection (Weeks 9-12)
```
Techniques:
- Reflected XSS
- Stored XSS
- DOM-based XSS
- Mutation XSS (mXSS)
```

**Deliverables:**
- [ ] XSSScenario class
- [ ] JavaScript mutators
- [ ] Context-aware validators
- [ ] Dataset (150+ payloads)

**Success Criteria:**
- 6 total scenarios operational
- Framework supports all without modifications
- Each scenario has >90% Blue Team validation rate

---

### **Phase 5: MITRE ATT&CK Integration**
**Status:** 🔄 Planned
**Duration:** 16-20 weeks
**Goal:** Comprehensive MITRE technique coverage

#### Strategy

**1. Technique Taxonomy Mapping** (Weeks 1-4)
```python
class MITREScenario(SecurityScenario):
    def __init__(self, technique_id: str):
        self.technique_id = technique_id  # e.g., "T1190"
        self.tactic = self._load_tactic()
        self.sub_techniques = self._load_sub_techniques()
```

**2. Automated Technique Discovery** (Weeks 5-8)
```python
class MITRERegistry:
    def discover_techniques(self):
        # Parse MITRE ATT&CK matrix
        # Generate scenario classes
        # Register techniques
        pass
```

**3. Phased Technique Coverage** (Weeks 9-20)

**Priority 1: Initial Access & Execution (Weeks 9-12)**
```
T1190: Exploit Public-Facing Application
T1059: Command and Scripting Interpreter
T1203: Exploitation for Client Execution
T1566: Phishing
```

**Priority 2: Persistence & Privilege Escalation (Weeks 13-16)**
```
T1078: Valid Accounts
T1053: Scheduled Task/Job
T1068: Exploitation for Privilege Escalation
T1548: Abuse Elevation Control Mechanism
```

**Priority 3: Defense Evasion & Discovery (Weeks 17-20)**
```
T1027: Obfuscated Files or Information
T1055: Process Injection
T1082: System Information Discovery
T1083: File and Directory Discovery
```

#### Deliverables
- [ ] `scenarios/mitre/` directory
- [ ] `MITREScenario` base class
- [ ] Technique-specific implementations (50+ techniques)
- [ ] MITRE ATT&CK coverage matrix
- [ ] Sub-technique micro-agents

**Success Criteria:**
- 50+ MITRE techniques supported
- Coverage matrix generated automatically
- Can map Purple Agent detections to MITRE matrix

---

### **Phase 6: Scale & Optimize**
**Status:** 🔄 Future
**Duration:** 12+ weeks
**Goal:** Production-grade performance and scale

#### Optimization Areas

**1. Distributed Execution** (Weeks 1-4)
```python
class DistributedOrchestrator(MasterOrchestrator):
    def spawn_agents_distributed(self, cluster):
        # Ray/Dask for distributed agents
        # Load balancing
        # Fault tolerance
        pass
```

**2. GPU Acceleration** (Weeks 5-8)
```python
class GPUMutationEngine(MutationEngine):
    def evolve_population_gpu(self, population):
        # Parallel mutation on GPU
        # Faster fitness evaluation
        pass
```

**3. Caching & Optimization** (Weeks 9-12)
```python
class CachedOrchestrator(MasterOrchestrator):
    def __init__(self):
        self.result_cache = RedisCache()
        self.llm_cache = SemanticCache()
```

**Performance Targets:**
- 10,000 tests in <10 minutes
- 1000+ concurrent agents
- <500ms per test evaluation
- 95% cache hit rate for repeated queries

---

## Scenario Extension Strategy

### Adding a New Scenario: Step-by-Step

#### Step 1: Define Scenario Class (30 minutes)
```python
# scenarios/your_scenario/scenario.py
from framework.base import SecurityScenario

class YourScenario(SecurityScenario):
    def get_techniques(self) -> List[str]:
        return ["technique1", "technique2"]

    def get_mutators(self) -> List[Mutator]:
        return [YourMutator1(), YourMutator2()]

    def get_validators(self) -> List[Validator]:
        return [YourValidator1(), YourValidator2()]
```

#### Step 2: Implement Mutators (2-4 hours)
```python
# scenarios/your_scenario/mutators.py
from framework.base import Mutator

class YourMutator1(Mutator):
    def mutate(self, attack: Attack) -> Attack:
        # Your mutation logic
        return mutated_attack
```

#### Step 3: Implement Validators (2-4 hours)
```python
# scenarios/your_scenario/validators.py
from framework.base import Validator

class YourValidator1(Validator):
    def validate(self, attack: Attack) -> ValidationResult:
        # Your validation logic
        return ValidationResult(is_valid=True)
```

#### Step 4: Create Dataset (variable)
```json
// datasets/your_scenario/test_cases.json
[
    {
        "id": "test_001",
        "code": "...",
        "is_vulnerable": true,
        "category": "technique1"
    }
]
```

#### Step 5: Register Scenario (5 minutes)
```python
# framework/registry.py
SCENARIO_REGISTRY = {
    "sql_injection": SQLInjectionScenario,
    "command_injection": CommandInjectionScenario,
    "your_scenario": YourScenario,  # ← Add here
}
```

**Total Time:** ~1 day for simple scenario

---

## MITRE ATT&CK Integration

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│               MITRE ATT&CK Framework                          │
│  (14 Tactics × ~200 Techniques × Sub-techniques)             │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│            Technique Scenario Generator                       │
│  - Parses MITRE JSON                                         │
│  - Creates scenario per technique                            │
│  - Maps sub-techniques to micro-agents                       │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│         Individual Technique Scenarios                        │
│                                                              │
│  T1190Scenario ─► Specialist ─► [Sub-technique micro-agents]│
│  T1059Scenario ─► Specialist ─► [Sub-technique micro-agents]│
│  T1566Scenario ─► Specialist ─► [Sub-technique micro-agents]│
│       ...                                                    │
└──────────────────────────────────────────────────────────────┘
```

### Implementation Phases

**Phase 1: Infrastructure** (4 weeks)
- Parse MITRE ATT&CK JSON
- Generate technique scenarios automatically
- Map tactics to test categories

**Phase 2: Initial Coverage** (12 weeks)
- Implement 50 high-priority techniques
- Focus on Initial Access, Execution, Persistence

**Phase 3: Comprehensive Coverage** (24+ weeks)
- Cover all tactics
- 200+ techniques
- Sub-technique micro-agents

### Coverage Reporting

```python
class MITRECoverageReport:
    def generate_matrix(self, evaluation_results):
        """
        Generate MITRE ATT&CK coverage matrix:

        Tactic              | Detected | Missed | Coverage
        --------------------|----------|--------|----------
        Initial Access      | 4/5      | 1/5    | 80%
        Execution           | 8/10     | 2/10   | 80%
        Persistence         | 5/8      | 3/8    | 62.5%
        ...
        """
```

---

## Scaling Strategy

### Scaling Dimensions

**1. Test Volume Scaling**
```
Current: 100 tests in 5 minutes
Target:  10,000 tests in 10 minutes
```

**Strategy:**
- Parallel agent execution
- Distributed Purple Agent calls
- Result streaming (not batching)

**2. Agent Scaling**
```
Current: 5-10 agents per evaluation
Target:  1,000+ concurrent agents
```

**Strategy:**
- Agent pooling
- Lazy agent initialization
- Resource limits per agent

**3. Scenario Scaling**
```
Current: 1 scenario (SQL Injection)
Target:  100+ scenarios (MITRE coverage)
```

**Strategy:**
- Automated scenario generation
- Scenario registry with lazy loading
- Pluggable architecture

---

## Future Enhancements

### Year 1+
- Real-time adaptive testing (continuous evaluation)
- Purple Agent learning detection (avoid overfitting to framework)
- Explainable AI for attack generation
- Integration with CI/CD pipelines
- Purple Agent marketplace

### Year 2+
- Zero-day vulnerability discovery assistance
- Automated patch validation
- Security posture trending
- Multi-vendor tool comparison dashboard
- Industry benchmarking

---

## Migration Path

### From Current SQLInjectionJudge to Framework

**Step 1: No Changes** (Week 1)
- Keep SQLInjectionJudge as-is
- Build framework alongside

**Step 2: Gradual Migration** (Weeks 2-4)
- Extract interfaces
- Implement adapters
- Run both versions in parallel

**Step 3: Full Migration** (Weeks 5-6)
- Deprecate old SQLInjectionJudge
- Use framework version
- Validate identical results

**Step 4: Enhancement** (Weeks 7+)
- Add Red/Blue team
- Enable multi-LLM judging
- Evolutionary mutations

---

**Previous:** [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
**Next:** [INTEGRATION.md](INTEGRATION.md) - How to integrate new scenarios
