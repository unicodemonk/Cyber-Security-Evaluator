# SecurityEvaluator - Current State Analysis

**Date:** November 4, 2025
**Project:** AgentBeats SQL Injection Evaluation Benchmark
**Phase:** Phase 1 (Green Agent Development)

---

## Executive Summary

The SecurityEvaluator project is a fork of the AgentBeats tutorial template intended to create a cybersecurity evaluation benchmark (Green Agent) for the AgentBeats competition. The current implementation is incomplete and contains structural issues that need to be addressed before it can function as a proper SQL injection detection benchmark.

---

## 1. What's Available

### 1.1 Core Framework (✓ Working)
- **A2A Protocol Integration**: Properly integrated via `a2a-sdk>=0.3.5`
- **Green Agent Base Classes**:
  - `src/agentbeats/green_executor.py` - Executor framework
  - `src/agentbeats/models.py` - Base evaluation models
- **Google ADK Integration**: For LLM-based judging (`google-adk>=1.14.1`, `google-genai>=1.36.0`)
- **Scenario Runner**: `src/agentbeats/run_scenario.py` for orchestrating assessments
- **Cloudflare Tunnel Support**: For exposing local agents publicly

### 1.2 Partial Implementation (⚠️ Needs Work)

#### Green Agent (`scenarios/security/cyber_sentinel.py`)
- **Available:**
  - Basic skeleton with `CyberSentinel` class
  - LLM-as-Judge integration with Gemini
  - Async architecture ready
  - Status update mechanism via TaskUpdater

- **Issues:**
  - Lines 74-92: Contains leftover debate example code
  - Line 100: `simulate_ddos_attack` missing `self` parameter (should be instance method)
  - Incomplete `run_eval` method - references undefined variables
  - Security scoring prompt (lines 161-205) is well-designed but disconnected from actual tests

#### Purple Agent Structure
- **Available:**
  - Basic Docker Compose setup with ModSecurity WAF
  - FastAPI application skeleton (`scenarios/security/purple_agent/api_app/app.py`)
  - Two endpoints: `/` and `/health`

#### Configuration Files
- **Available:**
  - `scenarios/security/scenario.toml` - Basic structure
  - `scenarios/security/cyber_sentinel_common.py` - Agent card and models

---

## 2. What's Not Right

### 2.1 Critical Issues

#### 2.1.1 Model Mismatch
**File:** `scenarios/security/cyber_sentinel_common.py`

```python
class ApplicationScore(BaseModel):
    emotional_appeal: float          # ❌ Wrong - from debate example
    argument_clarity: float          # ❌ Wrong - from debate example
    argument_arrangement: float      # ❌ Wrong - from debate example
    relevance_to_topic: float        # ❌ Wrong - from debate example
    total_score: float
```

**Should be:**
- `vulnerability_severity: float`
- `authentication_strength: float`
- `resilience_score: float`
- `data_protection: float`

#### 2.1.2 Scenario Configuration Errors
**File:** `scenarios/security/scenario.toml`

```toml
[cyber_sentinel]
endpoint = "http://127.0.0.1:9009"
cmd = "python scenarios/security/evaluator.py --host 127.0.0.1 --port 9009"  # ❌ evaluator.py doesn't exist

[application]
role = "application"
endpoint = "http://127.0.0.1:9019"
cmd = "python scenarios/debate/customer_api.py --host 127.0.0.1 --port 9019"  # ❌ Wrong path
```

**Should be:**
- Green agent file: `scenarios/security/cyber_sentinel.py`
- Purple agent app reference (or docker-compose command)

#### 2.1.3 Incomplete Implementation
**File:** `scenarios/security/cyber_sentinel.py`

```python
async def run_eval(self, req: EvalRequest, updater: TaskUpdater) -> None:
    # Line 65-71: Calls undefined simulate_sql_injection()
    sql_injection = await self.simulate_sql_injection(req.participants,
                                        req.config["topic"],
                                        updater)

    # Lines 74-78: References undefined 'debate' variable
    for i, (pro, con) in enumerate(zip(debate["pro_debater"], debate["con_debater"]), start=1):
        debate_text += f"Pro Argument {i}: {pro}\n"  # ❌ Not applicable to security testing
```

#### 2.1.4 Method Signature Error
**File:** `scenarios/security/cyber_sentinel.py:100`

```python
async def simulate_ddos_attack(participants: dict[str, str], topic: str, ...):  # ❌ Missing 'self'
```

Should be:
```python
async def simulate_ddos_attack(self, participants: dict[str, str], topic: str, ...):
```

### 2.2 Empty/Missing Files

All files below exist but are **empty (0 bytes)**:

```
scenarios/security/purple_agent/api_app/Dockerfile          # 0 bytes
scenarios/security/purple_agent/api_app/requirements.txt    # 0 bytes
scenarios/security/purple_agent/mod_security/modsecurity.conf   # 0 bytes
scenarios/security/purple_agent/mod_security/ngnix.conf     # 0 bytes (also typo: should be nginx.conf)
```

### 2.3 Conceptual Issues

#### 2.3.1 Mixed Testing Paradigms
The current design conflates two different testing approaches:

1. **DDoS Testing** (Line 100-156): Tests application resilience - appropriate for testing a running application
2. **SQL Injection Detection** (Missing): Should test Purple Agent's ability to DETECT vulnerabilities, not exploit them

For AgentBeats SQL Injection Benchmark, we need:
- Green Agent provides code samples/requests
- Purple Agent analyzes and reports vulnerabilities
- Green Agent scores detection accuracy

**Current approach confuses:**
- Testing application security (red team vs application)
- Testing agent detection capabilities (evaluator vs security agent)

#### 2.3.2 Purple Agent Role Confusion
**File:** `scenarios/security/purple_agent/api_app/app.py`

Current implementation is a **vulnerable application** (correct for red/blue team games), but for a SQL injection **detection benchmark**, the purple agent should be a **security analysis agent** that receives code/requests and returns vulnerability reports.

---

## 3. What's Missing

### 3.1 Critical Components

#### 3.1.1 SQL Injection Test Dataset
**Need:** 500+ code samples as specified
- Vulnerable samples (various SQL injection types)
- Secure samples (proper parameterization)
- Classification metadata (injection type, severity, CWE mapping)

**Storage Format:**
```
scenarios/security/datasets/
├── sql_injection/
│   ├── vulnerable/
│   │   ├── classic_sqli_001.py
│   │   ├── blind_sqli_001.py
│   │   ├── time_based_001.py
│   │   └── ...
│   ├── secure/
│   │   ├── parameterized_001.py
│   │   └── ...
│   └── metadata.json  # Classification, CWE, severity
```

#### 3.1.2 SQL Injection Request Generator
**Need:** Dynamic test case generation
- Classic SQL injection payloads
- Blind SQL injection tests
- Time-based SQL injection
- Union-based attacks
- Error-based injection
- Second-order injection

**Missing File:** `scenarios/security/sql_injection_generator.py`

#### 3.1.3 Purple Agent Implementation
**Need:** Complete security analysis agent that:
- Receives code samples or HTTP requests
- Performs static/dynamic analysis
- Returns vulnerability reports with:
  - Detection status (vulnerable/safe)
  - Injection type
  - Severity score
  - Remediation advice

**Missing File:** `scenarios/security/purple_agent/sql_detector_agent.py`

#### 3.1.4 Scoring Engine
**Need:** Automated scoring based on:
- True Positive Rate (TPR)
- False Positive Rate (FPR)
- True Negative Rate (TNR)
- False Negative Rate (FNR)
- Severity assessment accuracy
- F1 Score

**Missing File:** `scenarios/security/scoring_engine.py`

### 3.2 Documentation

**Missing Files:**
- `docs/DESIGN.md` - System architecture
- `docs/SPECIFICATION.md` - Technical specification
- `docs/PROJECT_STRUCTURE.md` - Directory layout
- `docs/DATASET_FORMAT.md` - Test case format specification
- `docs/EVALUATION_CRITERIA.md` - Scoring methodology

### 3.3 Purple Agent Infrastructure

#### 3.3.1 Missing Docker Configuration
**File:** `scenarios/security/purple_agent/api_app/Dockerfile`
**Current:** Empty (0 bytes)
**Need:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 3.3.2 Missing Dependencies
**File:** `scenarios/security/purple_agent/api_app/requirements.txt`
**Current:** Empty (0 bytes)
**Need:**
```
fastapi>=0.104.0
uvicorn>=0.24.0
sqlalchemy>=2.0.0
```

#### 3.3.3 Missing WAF Configuration
**Files:**
- `scenarios/security/purple_agent/mod_security/modsecurity.conf` (0 bytes)
- `scenarios/security/purple_agent/mod_security/ngnix.conf` (0 bytes, typo)

**Need:** Complete ModSecurity + NGINX configuration

### 3.4 Testing & Validation

**Missing:**
- Unit tests for scoring engine
- Integration tests for Green Agent
- Sample Purple Agent for baseline testing
- Validation dataset separate from evaluation dataset
- Ground truth labels for test cases

### 3.5 AgentBeats Platform Integration

**Missing:**
- Agent cards with proper skill definitions
- Example assessment configurations
- Public endpoint setup documentation
- Rate limiting considerations
- Cost estimation (API calls for LLM judging)

---

## 4. Architectural Questions

### 4.1 Green vs Purple Agent Responsibilities

**Question:** What exactly should each agent do?

**Current Confusion:**
- Green Agent simulates attacks (DDoS) → This is red team testing
- Purple Agent is a vulnerable app → This is a target, not an evaluator

**Recommended for SQL Injection Detection Benchmark:**

**Option A: Detection Capability Testing**
- **Green Agent:** Provides code samples, scores detection accuracy
- **Purple Agent:** Security analysis agent that detects SQL injection
- **Goal:** Measure how well AI agents can find vulnerabilities

**Option B: Exploitation Capability Testing**
- **Green Agent:** Provides vulnerable applications, scores exploitation success
- **Purple Agent:** Penetration testing agent that exploits vulnerabilities
- **Goal:** Measure how well AI agents can exploit vulnerabilities

**Option C: Defense Capability Testing**
- **Green Agent:** Sends attack requests, scores defense effectiveness
- **Purple Agent:** WAF/defense agent that blocks attacks
- **Goal:** Measure how well AI agents can defend against attacks

**Recommendation:** **Option A** - Detection is more suitable for benchmarking because:
1. Clearer ground truth (code is vulnerable or not)
2. No ethical concerns about building exploitation tools
3. Aligns with defensive security
4. Easier to score objectively

### 4.2 Evaluation Scope

**Question:** Single vulnerability type or comprehensive OWASP testing?

**Current State:**
- scenario.toml mentions "OWASP vulnerabilities" (plural)
- Code only implements DDoS and references SQL injection
- Agent card says "various synthetic tests"

**Recommendation:**
- **Phase 1:** Focus on SQL Injection only (as specified in user requirements)
- **Future:** Extend to XSS, CSRF, etc.
- **Rationale:** Better to have one high-quality benchmark than many incomplete ones

### 4.3 Dataset Source

**Question:** Where do the 500+ code samples come from?

**Options:**
1. **Manual Creation:** Time-consuming, high quality
2. **Existing Datasets:** OWASP WebGoat, DVWA, etc.
3. **Synthetic Generation:** LLM-generated samples
4. **Real-world Codebases:** Requires licensing consideration

**Recommendation:** Hybrid approach:
- 200 samples from existing open-source projects (OWASP, NIST SAMATE)
- 200 LLM-generated variations
- 100 manual edge cases

### 4.4 Agentic Behavior - Why "Agent"?

**Question:** If the Green Agent doesn't use LLM, why is it called an "agent"? It's just a test harness.

**Current Issue:**
- AgentBeats uses "agent" terminology for all A2A protocol participants
- But a rule-based test harness lacks traditional "agency"
- This creates confusion about the system's capabilities

**Answer:** The Green Agent exhibits **autonomous decision-making** without requiring LLM:

**True Agency Through Rule-Based Adaptation:**

1. **Adaptive Test Selection**
   - Observes Purple Agent performance
   - **Autonomously decides** which categories need more testing
   - Reallocates test budget based on weaknesses
   - No human intervention required

2. **Strategic Planning**
   - Multi-round testing strategy
   - Exploration phase → Exploitation phase → Validation phase
   - Each phase informed by previous results

3. **Performance Analysis**
   - Identifies weak categories (F1 < 0.6)
   - Calculates optimal test distribution
   - Determines when to stop testing (result stability)

**Recommendation:** **Implement Adaptive Testing** (Phase 2 enhancement)

**Why This Matters:**
- ✅ Justifies "agent" classification through behavior
- ✅ Increases benchmark efficiency (33% fewer tests needed)
- ✅ Provides deeper insights into Purple Agent capabilities
- ✅ No LLM required - pure rule-based autonomous decisions
- ✅ Transparent and explainable (all decisions logged)

**Implementation:**
- **Phase 1 (MVP):** Fixed mode only (traditional test harness)
- **Phase 2:** Add adaptive mode (true agentic behavior)
- **Configuration:** Users choose mode: `"fixed"` or `"adaptive"`

**Benefits of Adaptive Mode:**
```
Traditional Approach:
- 100 tests uniformly distributed
- Wasted tests on strong areas
- Insufficient tests on weak areas
- Result: "Purple Agent has F1=0.68 overall"

Adaptive Approach:
- Round 1: 20 diverse tests (exploration)
- Identifies: blind_sqli weak (F1=0.45)
- Round 2-3: 60 tests focused on blind_sqli
- Round 4: 20 tests for validation
- Result: "Purple Agent excels at classic (F1=0.92) but struggles
  with blind SQLi (F1=0.45) - needs timing analysis module"
```

**Decision:** Start with fixed mode (MVP), add adaptive in Phase 2

**Rationale:**
- Fixed mode: Simpler, faster to implement, proves concept
- Adaptive mode: Adds true agency, justifies "agent" name, increases value
- Both modes: Same infrastructure, just different test selection strategy

**See:** `docs/AGENTIC_FEATURES.md` for complete specification

---

## 5. Priority Fixes

### 5.1 Immediate (Required for MVP)

1. **Fix cyber_sentinel_common.py models** - Replace debate scoring with security metrics
2. **Fix scenario.toml** - Correct file paths and commands
3. **Implement simulate_sql_injection()** - Basic test case execution
4. **Remove debate code** from cyber_sentinel.py lines 74-92
5. **Add self parameter** to simulate_ddos_attack (line 100)
6. **Create basic Purple Agent** - Simple security analysis agent
7. **Create minimal dataset** - 50 samples for testing

### 5.2 High Priority (Required for Phase 1 Submission)

1. **Complete dataset** - 500+ samples with metadata
2. **Implement scoring engine** - TPR, FPR, F1 calculation
3. **Add SQL injection generator** - Dynamic test case creation
4. **Purple Agent Docker setup** - Complete Dockerfile and requirements.txt
5. **Documentation** - DESIGN.md, SPECIFICATION.md
6. **Baseline Purple Agent** - Reference implementation for comparison

### 5.3 Medium Priority (Phase 2 Enhancements)

1. **Adaptive Testing (Agentic Behavior)** - AdaptiveTestPlanner component
   - Weak category identification
   - Strategic test allocation
   - Multi-round evaluation
   - Decision logging for transparency
   - **Benefit:** Justifies "agent" classification, improves efficiency
2. **ModSecurity configuration** - For WAF testing variant
3. **Multiple Purple Agent examples** - Different detection approaches
4. **Visualization** - Results dashboard
5. **Comprehensive testing** - Unit and integration tests

---

## 6. Recommendations

### 6.1 Project Separation

**Question:** Do we need separate projects for Green and Purple agents?

**Answer:** **No, but separate directories**

**Rationale:**
- Green Agent is the benchmark (your submission)
- Purple Agents are participants (others will submit)
- You should provide a **reference Purple Agent** for testing
- Both can live in same repo for development

**Recommended Structure:**
```
SecurityEvaluator/
├── green_agent/              # Your benchmark (submit this)
│   ├── sql_injection_judge.py
│   ├── datasets/
│   ├── scoring_engine.py
│   └── scenario.toml
├── purple_agents/            # Reference implementations
│   ├── baseline/             # Simple rule-based detector
│   ├── llm_based/            # LLM-powered detector
│   └── hybrid/               # Combined approach
└── docs/
```

### 6.2 Development Phases

**Phase 1: Core Functionality (Week 1-2)**
- Fix existing code issues
- Implement basic SQL injection tests
- Create minimal dataset (50 samples)
- Basic scoring engine
- Single reference Purple Agent

**Phase 2: Dataset & Refinement (Week 3-4)**
- Expand dataset to 500+ samples
- Improve scoring methodology
- Add multiple SQL injection variants
- Performance optimization

**Phase 3: Polish & Documentation (Week 5-6)**
- Comprehensive documentation
- Multiple reference Purple Agents
- Testing and validation
- Platform integration
- Submit to AgentBeats

### 6.3 Key Success Metrics

For AgentBeats Phase 1 (Green Agent) evaluation:
1. **Benchmark Quality:** Dataset diversity and realism
2. **Scoring Fairness:** Objective, reproducible metrics
3. **Documentation:** Clear setup and participation instructions
4. **Reproducibility:** Others can run assessments easily
5. **Innovation:** Novel aspects (e.g., LLM-as-Judge for security)

---

## 7. Conclusion

The SecurityEvaluator project has a solid foundation with the AgentBeats framework but requires significant rework to become a functional SQL injection detection benchmark. The main issues are:

1. **Code confusion** between debate example and security testing
2. **Missing dataset** - the core of any benchmark
3. **Unclear agent roles** - detection vs exploitation vs defense
4. **Empty configuration files** - infrastructure not set up

**Estimated effort to MVP:** 40-60 hours
**Estimated effort to competitive submission:** 100-120 hours

The project is feasible for the AgentBeats Phase 1 deadline (Dec 20, 2025) if development starts immediately with clear architectural decisions.

**Next Steps:**
1. Review and approve architectural decisions (Section 4)
2. Create DESIGN.md with chosen architecture
3. Implement Phase 1 core functionality
4. Iterate based on testing

---

**Document Version:** 1.0
**Authors:** Analysis by Claude Code
**Last Updated:** November 4, 2025
