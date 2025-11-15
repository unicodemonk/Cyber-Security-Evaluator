# SecurityEvaluator Documentation

Welcome to the SecurityEvaluator documentation! This is a **SQL Injection Detection Benchmark** (Green Agent) for the AgentBeats competition.

---

## 📚 Documentation Overview

### Quick Navigation

1. **[🔍 DUAL_EVALUATION_GUIDE.md](./DUAL_EVALUATION_GUIDE.md)** - **START HERE FOR SCORING**
   - **Complete guide to dual evaluation framework**
   - How Security Evaluator and Security Posture scores work
   - TP/FP/TN/FN outcome correlation with scores
   - Terminology guide (Green Agent vs Security Evaluator)
   - Compatibility and integration information
   - Real examples, formulas, and FAQ

2. **[ANALYSIS.md](./ANALYSIS.md)** - Project state
   - Current state of the project
   - What's available, what's broken, what's missing
   - Critical issues and fixes needed
   - Architectural decisions

3. **[DESIGN.md](./DESIGN.md)** - System architecture
   - High-level architecture diagrams
   - Green Agent design (evaluation benchmark)
   - Purple Agent interface (security detectors)
   - Data flow and communication protocol
   - Dataset design
   - Scoring methodology

4. **[SPECIFICATION.md](./SPECIFICATION.md)** - Technical details
   - API specifications (A2A protocol)
   - Data models (Pydantic schemas)
   - File formats (metadata.json, test cases)
   - Implementation examples (code snippets)
   - Testing requirements
   - Performance requirements

5. **[PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)** - Project organization
   - Complete directory layout
   - File-by-file breakdown
   - Development workflow
   - Priority roadmap

---

## 🎯 Understanding Dual Evaluation

**New to the framework? Read this first:**

The SecurityEvaluator uses **dual scoring perspectives**:

| **Perspective** | **What It Measures** | **Key Metric** | **Audience** |
|----------------|---------------------|---------------|--------------|
| **Security Evaluator** | Attack detection effectiveness | F1 Score (0-100) | Red teams, researchers |
| **Security Posture** | System security health | Posture Score (0-100) | Blue teams, developers |

**Both perspectives analyze the same test results but ask different questions:**
- Security Evaluator: "How good is our testing?"
- Security Posture: "How secure is the system?"

👉 **[Read the complete guide](./DUAL_EVALUATION_GUIDE.md)** for formulas, examples, and integration details.

---

## 🎯 Project Summary

### What is SecurityEvaluator?

SecurityEvaluator is a **Phase 1 Green Agent** for the AgentBeats competition that evaluates AI agents' ability to detect SQL injection vulnerabilities in code.

### Key Features

- **500+ Test Cases**: Comprehensive dataset covering all SQL injection variants
- **Objective Scoring**: Automated metrics (F1, Precision, Recall, TPR, FPR)
- **Multiple Languages**: Python, JavaScript, Java, PHP code samples
- **A2A Protocol**: Full AgentBeats platform integration
- **Reference Implementations**: 3 baseline Purple Agents included

### Architecture

```
┌──────────────────────────────────────┐
│   AgentBeats Platform                │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│   Green Agent (Benchmark)            │
│   - Loads 500+ test cases            │
│   - Sends to Purple Agent            │
│   - Scores detection accuracy        │
│   - Produces detailed report         │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│   Purple Agent (Detector)            │
│   - Analyzes code for SQL injection  │
│   - Returns vulnerability report     │
└──────────────────────────────────────┘
```

---

## 🚀 Quick Start

### For First-Time Readers

**Recommended reading order:**

1. Read **[ANALYSIS.md](./ANALYSIS.md)** (15 min)
   - Understand current state
   - Identify what needs to be fixed

2. Review **[DESIGN.md](./DESIGN.md)** (30 min)
   - Understand system architecture
   - Learn about Green vs Purple agents

3. Skim **[SPECIFICATION.md](./SPECIFICATION.md)** (20 min)
   - Familiarize with data models
   - Review API contracts

4. Reference **[PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)** (10 min)
   - Understand file organization
   - See development roadmap

**Total time: ~75 minutes**

### For Developers

**I want to...**

- **Fix existing code issues** → See [ANALYSIS.md - Section 5.1](./ANALYSIS.md#51-immediate-required-for-mvp)
- **Implement Green Agent** → See [DESIGN.md - Section 3](./DESIGN.md#3-green-agent-design)
- **Create test dataset** → See [DESIGN.md - Section 6](./DESIGN.md#6-dataset-design)
- **Build Purple Agent** → See [DESIGN.md - Section 4](./DESIGN.md#4-purple-agent-design)
- **Understand data models** → See [SPECIFICATION.md - Section 2](./SPECIFICATION.md#2-data-models)
- **See file organization** → See [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)

---

## 📊 Project Status

### Current State (Nov 4, 2025)

**Completed:**
- ✅ Core AgentBeats framework integrated
- ✅ Basic project structure
- ✅ Comprehensive documentation (Analysis, Design, Specification)

**In Progress:**
- ⏳ Green Agent implementation (cyber_sentinel.py needs rework)
- ⏳ Test dataset creation (0/500+ test cases)
- ⏳ Purple Agent baseline implementation

**Not Started:**
- ⬜ Scoring engine implementation
- ⬜ Test orchestration
- ⬜ Platform deployment

### Next Steps

**Immediate (Week 1):**
1. Fix `cyber_sentinel_common.py` models
2. Implement `sql_injection_judge.py` (Green Agent)
3. Create minimal dataset (50 test cases)
4. Implement `scoring_engine.py`
5. Build baseline Purple Agent

**See [PROJECT_STRUCTURE.md - Files to Create](./PROJECT_STRUCTURE.md#files-to-create-priority-order) for full roadmap**

---

## 🏗️ Key Architectural Decisions

### 1. Detection vs Exploitation

**Decision:** Focus on **detection capability testing**
- Green Agent provides code samples
- Purple Agent detects vulnerabilities
- Scoring based on detection accuracy (not exploitation)

**Rationale:**
- Clearer ground truth
- No ethical concerns
- Aligns with defensive security
- Easier to score objectively

### 2. Single Vulnerability Focus

**Decision:** SQL Injection only (not full OWASP Top 10)
- Deep coverage of SQL injection variants
- 500+ test cases across 6 categories

**Rationale:**
- Better to have one excellent benchmark than many mediocre ones
- Easier to achieve high quality
- Can extend to other vulnerabilities later

### 3. Separate Green and Purple Projects?

**Decision:** Single repository with separate directories
- `scenarios/security/` - Green Agent (benchmark)
- `purple_agents/` - Reference Purple Agents

**Rationale:**
- Simplifies development and testing
- Green Agent submission includes reference Purple Agents
- Participants fork and modify Purple Agents only

### 4. Dataset Source

**Decision:** Hybrid approach
- 200 samples from existing open-source projects
- 200 LLM-generated variations
- 100 manual edge cases

**Rationale:**
- Balance of quality, diversity, and speed
- Leverage existing resources
- Add unique challenging cases

---

## 🎯 Competition Context

### AgentBeats Phase 1: Green Agents (Oct 16 – Dec 20, 2025)

**Goal:** Build evaluation benchmarks (green agents) that measure AI agent capabilities

**SecurityEvaluator Position:**
- **Domain:** Cybersecurity
- **Specific Capability:** SQL Injection Detection
- **Evaluation Method:** Code analysis accuracy
- **Target Participants:** Security analysis AI agents

**Evaluation Criteria for Phase 1:**
1. **Benchmark Quality** - Dataset diversity and realism
2. **Scoring Fairness** - Objective, reproducible metrics
3. **Documentation** - Clear setup instructions
4. **Reproducibility** - Others can easily run assessments
5. **Innovation** - Novel approaches (e.g., LLM-as-Judge for security)

**Prize Pool:** $1M+ distributed across winning benchmarks

---

## 📈 Success Metrics

### For Green Agent (Benchmark Quality)

- **Dataset Size:** 500+ test cases ✅ Target
- **Category Coverage:** 6 SQL injection variants ✅ Comprehensive
- **Language Diversity:** 4 languages (Python, JS, Java, PHP) ✅ Broad
- **Ground Truth Quality:** 100% accuracy in labels ✅ Critical
- **Reproducibility:** Deterministic scoring ✅ Required

### For Purple Agents (Detection Performance)

**Baseline Targets:**
- Rule-based: F1 ≥ 0.60
- LLM-based: F1 ≥ 0.85
- Hybrid: F1 ≥ 0.80

**Evaluation Metrics:**
- Primary: **F1 Score** (balance of precision and recall)
- Secondary: Precision (minimize false alarms)
- Tertiary: Recall (catch vulnerabilities)
- Tiebreaker: Response time

---

## 🛠️ Technology Stack

### Green Agent
- **Language:** Python 3.11+
- **Framework:** A2A SDK, AgentBeats
- **LLM:** Google Gemini (optional, for LLM-as-Judge)
- **Dependencies:** Pydantic, aiohttp, uvicorn

### Purple Agents
- **Baseline:** Regex, pattern matching
- **LLM-based:** Google ADK (Gemini) or OpenAI SDK (GPT-4)
- **Hybrid:** Rule-based + LLM

### Dataset
- **Format:** Python/JS/Java/PHP code files
- **Metadata:** JSON
- **Version Control:** Git

### Testing
- **Framework:** pytest
- **Coverage:** pytest-cov
- **Integration:** Docker (optional)

---

## 📞 Getting Help

### Resources

- **AgentBeats Platform:** https://agentbeats.org
- **A2A Protocol Docs:** https://a2a-protocol.org
- **AgentBeats Tutorial:** [README.md](../README.md)
- **Competition Info:** https://rdi.berkeley.edu/agentx-agentbeats

### Document Feedback

Found an issue or have suggestions?
- Open an issue on GitHub
- Submit a pull request
- Contact the maintainers

---

## 📝 Document Versions

| Document | Version | Last Updated | Status |
|----------|---------|--------------|--------|
| README.md | 1.0 | 2025-11-04 | Complete |
| ANALYSIS.md | 1.0 | 2025-11-04 | Complete |
| DESIGN.md | 1.0 | 2025-11-04 | Complete |
| SPECIFICATION.md | 1.0 | 2025-11-04 | Complete |
| PROJECT_STRUCTURE.md | 1.0 | 2025-11-04 | Complete |

---

**Happy Building! 🚀**

Let's create an excellent SQL Injection Detection Benchmark for the AgentBeats community!
