# Quick Start: Context for New Sessions

**📅 Last Updated:** November 6, 2025
**🎯 Current Phase:** Design Phase - Framework Documentation Complete

---

## 🔍 What Is This Project?

An **Advanced Multi-Agent Security Evaluation Framework** for testing security detection tools (Purple Agents) using:
- **Adversarial Red Team** agents that find evasions
- **Validation Blue Team** agents that ensure realism
- **Multi-LLM Judge Panel** for quality assessment
- **Adaptive testing** that focuses on weaknesses
- **Extensible architecture** supporting multiple security scenarios

---

## 📂 Current State

### ✅ What's Built

**Foundation (SQL Injection):**
```
scenarios/security/
├── sql_injection_judge.py    ✅ Fully functional Green Agent
├── dataset_manager.py         ✅ Dataset management
├── scoring_engine.py          ✅ Metrics (F1, Precision, Recall)
├── adaptive_planner.py        ✅ Adaptive test allocation
└── models.py                  ✅ Data models

llm/                           ✅ Complete LLM integration
├── client.py                  ✅ OpenAI/Anthropic/Google
├── prompt_manager.py          ✅ YAML-based prompts
├── response_parser.py         ✅ Response parsing
└── prompts.yaml               ✅ 10 pre-built prompts

tests/                         ✅ 36 passing tests
```

**Documentation (THIS!):**
```
framework/docs/
├── README.md                  ✅ Documentation index
├── OVERVIEW.md                ✅ Vision and high-level architecture
├── REQUIREMENTS.md            ✅ Detailed requirements
├── SPECIFICATION.md           ✅ Technical specifications
├── ARCHITECTURE.md            ✅ Architecture diagrams
├── EVOLUTION.md               ✅ Roadmap and evolution plan
├── INTEGRATION.md             ✅ Step-by-step integration guide
└── QUICK_START.md             ✅ This file (context)
```

### 🔄 What's Next (Phase 1: Framework Abstraction)

**NOT YET BUILT:**
```
framework/
├── base.py                    🔄 Abstract interfaces
├── orchestrator.py            🔄 MasterOrchestrator
├── red_team.py                🔄 Adversarial agent
├── blue_team.py               🔄 Validation agent
├── judge_panel.py             🔄 Multi-LLM consensus
├── specialist.py              🔄 Technique specialists
└── engines/
    ├── mutation_engine.py     🔄 Evolutionary mutations
    └── boundary_learner.py    🔄 Decision boundary learning
```

---

## 🚀 To Get Context Between Sessions

### Quick Read (5 minutes)
1. **This file** - Current state
2. `OVERVIEW.md` - High-level vision
3. `EVOLUTION.md` - What phase we're in

### Deep Context (20 minutes)
1. `OVERVIEW.md` - Vision and problem statement
2. `ARCHITECTURE.md` - System design and diagrams
3. `REQUIREMENTS.md` - What to build
4. `EVOLUTION.md` - Current phase and next steps

### Full Context (1 hour)
Read all documents in order:
1. README.md → OVERVIEW.md
2. REQUIREMENTS.md → SPECIFICATION.md
3. ARCHITECTURE.md → EVOLUTION.md
4. INTEGRATION.md

---

## 📋 Key Design Decisions

### 1. Multi-Agent Architecture
```
Master Orchestrator
├── Red Team (generates attacks)
├── Blue Team (validates attacks)
└── Judge Panel (assesses quality)
    ├── Specialist Agents
    └── Micro-Agents
```

### 2. Universal Abstraction
```python
class SecurityScenario(ABC):
    def get_techniques() → List[str]
    def get_mutators() → List[Mutator]
    def get_validators() → List[Validator]
```

**Benefit:** Add new scenarios (DDoS, Phishing, MITRE) without changing framework

### 3. Evolutionary Optimization
- Red Team evolves attacks over generations
- Fitness function: Evasion + Boundary proximity + Novelty
- Blue Team filters unrealistic attacks

### 4. Extensibility First
- Pluggable mutators
- Pluggable validators
- Scenario-agnostic orchestrator
- **Goal:** New scenario in <1 day

---

## 💡 Current Phase: Design → Implementation

### Phase 1 Timeline (6 weeks)

**Weeks 1-2:** Base Abstractions
- [ ] `framework/base.py` with interfaces
- [ ] `framework/models.py` with data models
- [ ] Refactor SQLInjectionJudge to use framework

**Weeks 3-4:** Red/Blue Team
- [ ] `framework/red_team.py`
- [ ] `framework/blue_team.py`
- [ ] `framework/engines/mutation_engine.py`
- [ ] `framework/engines/boundary_learner.py`

**Weeks 5-6:** Judge Panel & Specialists
- [ ] `framework/judge_panel.py`
- [ ] `framework/specialist.py`
- [ ] Multi-LLM consensus
- [ ] Hierarchical specialists

---

## 🎯 Success Criteria

Framework is **production-ready** when:
- ✅ All P0 requirements implemented
- ✅ All P1 requirements implemented
- ✅ ≥80% test coverage
- ✅ Documentation complete
- ✅ 2+ scenarios validated
- ✅ Performance benchmarks met

---

## 📊 Documentation Statistics

| Document | Lines | Purpose |
|----------|-------|---------|
| OVERVIEW.md | 449 | Vision, problem, solution |
| REQUIREMENTS.md | 694 | Functional & non-functional requirements |
| SPECIFICATION.md | 637 | Technical specifications |
| ARCHITECTURE.md | 869 | System architecture & diagrams |
| EVOLUTION.md | 632 | Roadmap & evolution |
| INTEGRATION.md | 819 | Step-by-step scenario creation |
| **Total** | **4,221** | Complete framework documentation |

---

## 🔗 Navigation Map

```
Start Here: QUICK_START.md (you are here!)
    │
    ├─► Want vision? → OVERVIEW.md
    │
    ├─► Want to understand requirements? → REQUIREMENTS.md
    │
    ├─► Want to see architecture? → ARCHITECTURE.md
    │
    ├─► Want technical details? → SPECIFICATION.md
    │
    ├─► Want to know what's next? → EVOLUTION.md
    │
    └─► Want to add a scenario? → INTEGRATION.md
```

---

## 🛠️ Next Implementation Step

**When ready to code:**

1. **Start with base abstractions:**
   ```bash
   mkdir -p framework
   touch framework/__init__.py
   touch framework/base.py
   ```

2. **Create interfaces in `framework/base.py`:**
   - SecurityScenario
   - Mutator
   - Validator
   - MicroAgent

3. **Refactor SQLInjectionJudge:**
   - Implement SecurityScenario interface
   - Extract mutators
   - Extract validators

4. **Validate:**
   - All existing tests still pass
   - SQLInjectionJudge works via framework

---

## 💬 Key Concepts to Remember

### Red Team vs Blue Team
- **Red Team:** Adversarial - tries to BREAK Purple Agent
- **Blue Team:** Validation - ensures RED Team attacks are REALISTIC
- **Judge Panel:** Quality - assesses EXPLANATION quality

### Adaptive vs Fixed
- **Fixed:** Predetermined test set (traditional benchmark)
- **Adaptive:** Focuses on weaknesses autonomously (agentic)

### Specialist vs Micro-Agent
- **Specialist:** Technique expert (e.g., SQL Injection Specialist)
- **Micro-Agent:** Sub-technique expert (e.g., Boolean Blind SQLi)

### Mutation vs Evolution
- **Mutation:** Single transformation (e.g., add encoding)
- **Evolution:** Multiple generations optimizing for fitness

---

## 📞 Questions to Ask When Resuming

1. **What phase are we in?**
   → Check `EVOLUTION.md` Phase 1-6

2. **What's the current task?**
   → Check this file's "Next Implementation Step"

3. **What was decided?**
   → Check `REQUIREMENTS.md` and `ARCHITECTURE.md`

4. **How do I add X?**
   → Check `INTEGRATION.md` for step-by-step guide

---

## 🎓 Key Files to Reference

**For understanding:**
- `OVERVIEW.md` - Why we built this
- `ARCHITECTURE.md` - How it works

**For implementation:**
- `SPECIFICATION.md` - Interfaces and contracts
- `INTEGRATION.md` - Step-by-step examples

**For planning:**
- `REQUIREMENTS.md` - What to build
- `EVOLUTION.md` - When to build it

---

## ✅ Current Status Summary

**Phase:** Design Complete ✅
**Next:** Implementation (Phase 1)
**Duration:** 6 weeks
**Goal:** Framework abstraction + Red/Blue Team agents

**Documentation:** 100% Complete ✅
- 7 comprehensive documents
- 4,221 lines of documentation
- Full architecture, requirements, specifications
- Step-by-step integration guide
- Evolution roadmap

**Ready to start implementation:** Yes ✅

---

**Last Updated:** November 6, 2025
**Phase:** Design → Implementation Transition
