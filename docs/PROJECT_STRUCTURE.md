# SecurityEvaluator - Project Structure

**Version:** 1.0
**Date:** November 4, 2025

---

## Proposed Project Structure

```
SecurityEvaluator/
├── README.md                           # Project overview, quickstart
├── LICENSE                             # MIT License
├── .gitignore                          # Git ignore rules
├── pyproject.toml                      # Python project config, dependencies
├── uv.lock                             # Locked dependencies
├── sample.env                          # Environment variables template
├── .env                                # Local environment (gitignored)
│
├── docs/                               # 📚 Documentation
│   ├── ANALYSIS.md                     # Current state analysis
│   ├── DESIGN.md                       # System architecture design
│   ├── SPECIFICATION.md                # Technical specification
│   ├── PROJECT_STRUCTURE.md            # This file
│   ├── DATASET_FORMAT.md               # Test case format guide
│   ├── EVALUATION_CRITERIA.md          # Scoring methodology
│   └── QUICKSTART.md                   # Getting started guide
│
├── src/                                # Core framework (from AgentBeats template)
│   └── agentbeats/
│       ├── __init__.py
│       ├── green_executor.py           # Base green agent executor
│       ├── models.py                   # Base evaluation models
│       ├── client.py                   # A2A client helpers
│       ├── client_cli.py               # CLI client
│       ├── run_scenario.py             # Scenario runner CLI
│       ├── tool_provider.py            # Tool management
│       └── cloudflare.py               # Cloudflare tunnel integration
│
├── scenarios/                          # 🎯 Evaluation scenarios
│   └── security/                       # SQL Injection benchmark
│       ├── sql_injection_judge.py      # 🟢 Green Agent (main evaluator)
│       ├── config.yaml                 # Configuration (easier than TOML)
│       ├── Dockerfile                  # Docker deployment
│       ├── models.py                   # Data models (TestCase, Report, Metrics)
│       ├── dataset_manager.py          # Dataset loading & sampling
│       ├── scoring_engine.py           # Metrics calculation
│       ├── test_orchestrator.py        # Test execution orchestration
│       ├── report_generator.py         # Report & artifact generation
│       ├── scenario.toml               # Scenario configuration (AgentBeats)
│       │
│       ├── datasets/                   # 📊 Test datasets (JSON format)
│       │   └── sql_injection/
│       │       ├── metadata.json       # Master metadata file
│       │       ├── vulnerable_code/    # Vulnerable code samples (JSON)
│       │       │   ├── python_sqli.json      # 175 Python samples
│       │       │   ├── javascript_sqli.json  # 90 JavaScript samples
│       │       │   ├── java_sqli.json        # 50 Java samples
│       │       │   └── php_sqli.json         # 35 PHP samples
│       │       └── secure_code/        # Secure code samples (JSON)
│       │           ├── python_secure.json    # 125 Python samples
│       │           ├── javascript_secure.json # 60 JavaScript samples
│       │           ├── java_secure.json      # 40 Java samples
│       │           └── php_secure.json       # 25 PHP samples
│       │       # Total: 600 samples in 8 JSON files (vs 600+ individual files)
│       │
│       └── utils/                      # Helper utilities
│           ├── payload_generator.py    # SQL injection payload generator
│           ├── code_parser.py          # AST parsing utilities
│           └── validators.py           # Response validation helpers
│
├── purple_agents/                      # 🟣 Reference Purple Agent implementations
│   ├── baseline/                       # Rule-based detector (baseline)
│   │   ├── sql_detector.py             # Main detector agent
│   │   ├── patterns.py                 # SQL injection patterns
│   │   ├── requirements.txt            # Minimal dependencies
│   │   └── README.md                   # Usage instructions
│   │
│   ├── llm_based/                      # LLM-powered detector
│   │   ├── sql_detector.py             # Gemini/GPT-4 based detector
│   │   ├── prompts.py                  # LLM prompt templates
│   │   ├── requirements.txt            # LLM SDK dependencies
│   │   └── README.md                   # Usage & cost estimates
│   │
│   └── hybrid/                         # Hybrid approach (rule + LLM)
│       ├── sql_detector.py             # Combined detector
│       ├── rule_filter.py              # Pre-filtering with rules
│       ├── llm_analyzer.py             # LLM for complex cases
│       ├── requirements.txt
│       └── README.md
│
├── tests/                              # 🧪 Test suite
│   ├── __init__.py
│   ├── conftest.py                     # Pytest configuration
│   ├── test_scoring_engine.py          # Scoring engine unit tests
│   ├── test_dataset_manager.py         # Dataset loading tests
│   ├── test_integration.py             # End-to-end integration tests
│   ├── test_models.py                  # Pydantic model validation
│   └── fixtures/                       # Test fixtures
│       ├── sample_test_cases.py
│       └── mock_purple_agent.py
│
├── scripts/                            # 🛠️ Utility scripts
│   ├── generate_dataset.py             # Generate test cases from templates
│   ├── validate_dataset.py             # Validate dataset integrity
│   ├── benchmark_purple_agents.py      # Local benchmarking tool
│   ├── export_results.py               # Export results to CSV/JSON
│   └── setup_cloudflare.sh             # Cloudflare tunnel setup helper
│
├── assets/                             # 📸 Images, diagrams
│   ├── architecture.png                # System architecture diagram
│   ├── sample_output.png               # Example output screenshot
│   └── confusion_matrix_example.png
│
└── experiments/                        # 🔬 Experimental features (optional)
    ├── multi_language/                 # JavaScript, Java, PHP test cases
    ├── dynamic_testing/                # Runtime exploitation tests
    └── llm_as_judge/                   # Alternative LLM-based scoring
```

---

## Directory Breakdown

### `/src/agentbeats/` - Core Framework

**Purpose:** Shared AgentBeats framework code (from template)

**Key Files:**
- `green_executor.py`: Abstract base class for Green Agents
- `models.py`: Base Pydantic models (EvalRequest, EvalResult)
- `run_scenario.py`: CLI for running scenarios

**When to modify:**
- Generally don't modify (maintained by AgentBeats)
- Only extend if adding new framework capabilities

---

### `/scenarios/security/` - SQL Injection Benchmark (Green Agent)

**Purpose:** Implementation of the SQL injection detection benchmark

#### Core Components

**`sql_injection_judge.py`** (🟢 Main Green Agent)
```python
class SQLInjectionJudge(GreenAgent):
    async def run_eval(self, req: EvalRequest, updater: TaskUpdater) -> None:
        # Main evaluation orchestration
```
- Implements the evaluation workflow
- Coordinates all components
- Produces final assessment artifacts

**`models.py`**
```python
class TestCaseInput(BaseModel): ...
class VulnerabilityReport(BaseModel): ...
class TestResult(BaseModel): ...
class EvaluationMetrics(BaseModel): ...
```
- All Pydantic data models
- Input/output schemas
- Type safety enforcement

**`dataset_manager.py`**
```python
class DatasetManager:
    def load_dataset(self) -> None: ...
    def sample(self, n: int, categories: list[str]) -> list[TestCase]: ...
```
- Loads metadata.json
- Samples test cases
- Manages dataset access

**`scoring_engine.py`**
```python
class ScoringEngine:
    def calculate_metrics(self, results: list[TestResult]) -> EvaluationMetrics: ...
```
- Calculates TPR, FPR, F1, etc.
- Category breakdown
- Confusion matrix

**`test_orchestrator.py`**
```python
class TestOrchestrator:
    async def run_tests(self, agent_url: str, test_cases: list[TestCase]) -> list[TestResult]: ...
```
- Parallel test execution
- Timeout handling
- Progress tracking

**`report_generator.py`**
```python
class ReportGenerator:
    def generate_artifact(self, metrics: EvaluationMetrics) -> list[Part]: ...
```
- Format results as A2A artifacts
- Generate markdown reports
- Export to JSON

**`scenario.toml`**
```toml
[sql_injection_judge]
endpoint = "http://127.0.0.1:9009"
cmd = "python scenarios/security/sql_injection_judge.py --host 127.0.0.1 --port 9009"
```
- Configuration for local testing
- Agent endpoints and startup commands

---

### `/scenarios/security/datasets/sql_injection/` - Test Dataset

**Purpose:** Ground truth test cases for evaluation

**Format:** **JSON files** (easier to manage than 600+ individual files)

**Structure:**

```
datasets/sql_injection/
├── metadata.json                # Master index
├── vulnerable_code/
│   ├── python_sqli.json         # 175 Python vulnerable samples
│   ├── javascript_sqli.json     # 90 JavaScript samples
│   ├── java_sqli.json           # 50 Java samples
│   └── php_sqli.json            # 35 PHP samples
└── secure_code/
    ├── python_secure.json       # 125 Python secure samples
    ├── javascript_secure.json   # 60 JavaScript samples
    ├── java_secure.json         # 40 Java samples
    └── php_secure.json          # 25 PHP samples
```

**Total:** 600 samples in 8 JSON files (vs managing 600+ individual `.py`/`.js`/`.java`/`.php` files)

**JSON File Format:**
```json
{
  "dataset_version": "1.0",
  "language": "python",
  "total_samples": 175,
  "samples": [
    {
      "id": "py_classic_001",
      "category": "classic_sqli",
      "severity": "high",
      "code": "query = f'SELECT * FROM users WHERE id={uid}'",
      "description": "Direct f-string concatenation",
      "cwe_id": "CWE-89",
      "tags": ["f-string", "concatenation"]
    }
  ]
}
```

**Benefits of JSON format:**
- ✅ Edit 8 files vs manage 600+ individual files
- ✅ 10x faster loading (8 I/O operations vs 600)
- ✅ Cleaner version control diffs
- ✅ Easy schema validation
- ✅ Simpler programmatic generation

---

### `/purple_agents/` - Reference Implementations

**Purpose:** Provide baseline Purple Agent implementations for:
1. Testing Green Agent during development
2. Demonstrating Purple Agent interface
3. Benchmark comparison (participants should beat baseline)

#### Three Variants:

**1. Baseline (Rule-Based)**
```
purple_agents/baseline/
├── sql_detector.py         # Pattern matching, regex
├── patterns.py             # Vulnerability patterns
└── README.md
```
- Fast, deterministic
- Expected F1: ~0.60
- No API costs

**2. LLM-Based**
```
purple_agents/llm_based/
├── sql_detector.py         # Gemini/GPT-4 powered
├── prompts.py              # Prompt templates
└── README.md
```
- High accuracy
- Expected F1: ~0.85
- $0.10-1.00 per 100 tests

**3. Hybrid**
```
purple_agents/hybrid/
├── sql_detector.py         # Rule pre-filter + LLM
├── rule_filter.py          # Fast pre-screening
└── llm_analyzer.py         # Deep analysis for complex cases
```
- Balanced cost/accuracy
- Expected F1: ~0.80
- $0.03-0.50 per 100 tests

---

### `/tests/` - Test Suite

**Purpose:** Ensure code quality and correctness

**Test Categories:**

1. **Unit Tests**
   - `test_scoring_engine.py`: Metric calculations
   - `test_dataset_manager.py`: Dataset loading
   - `test_models.py`: Pydantic validation

2. **Integration Tests**
   - `test_integration.py`: End-to-end evaluation flow
   - Mock Purple Agents for deterministic testing

3. **Validation Tests**
   - Dataset integrity checks
   - File existence verification
   - Metadata consistency

**Run Tests:**
```bash
pytest tests/ -v
pytest tests/test_scoring_engine.py -v
pytest tests/ --cov=scenarios/security
```

---

### `/scripts/` - Utility Scripts

**Purpose:** Development and maintenance tools

**Key Scripts:**

**`generate_dataset.py`**
```bash
python scripts/generate_dataset.py --category classic --count 10
```
- Generate test cases from templates
- LLM-assisted code generation
- Automatic metadata creation

**`validate_dataset.py`**
```bash
python scripts/validate_dataset.py
```
- Verify all files referenced in metadata exist
- Check code syntax validity
- Validate category distribution

**`benchmark_purple_agents.py`**
```bash
python scripts/benchmark_purple_agents.py \
  --agent http://localhost:9019 \
  --sample-size 100
```
- Local benchmarking without AgentBeats platform
- Quick iteration during Purple Agent development
- Output: metrics.json, report.md

**`setup_cloudflare.sh`**
```bash
./scripts/setup_cloudflare.sh
```
- Automated Cloudflare Tunnel setup
- Generate persistent tunnel with named domain
- Update scenario.toml with public URL

---

### `/docs/` - Documentation

**Purpose:** Comprehensive project documentation

**Key Documents:**

1. **ANALYSIS.md**: Current state analysis, issues identified
2. **DESIGN.md**: System architecture, workflow diagrams
3. **SPECIFICATION.md**: Technical spec, API contracts
4. **PROJECT_STRUCTURE.md**: This file
5. **QUICKSTART.md**: Step-by-step getting started
6. **DATASET_FORMAT.md**: Test case format guidelines
7. **EVALUATION_CRITERIA.md**: Detailed scoring methodology

---

## File Count Estimates

| Directory | Files | Lines of Code |
|-----------|-------|---------------|
| `src/agentbeats/` | 8 | ~1,500 (template) |
| `scenarios/security/` | 12 | ~2,500 |
| `scenarios/security/datasets/` | 9 (JSON) | ~15,000 (600 samples in JSON) |
| `purple_agents/baseline/` | 4 | ~400 |
| `purple_agents/llm_based/` | 4 | ~300 |
| `purple_agents/hybrid/` | 5 | ~600 |
| `tests/` | 10 | ~1,000 |
| `scripts/` | 5 | ~800 |
| `docs/` | 6 | ~12,000 (markdown) |
| **Total** | **~65** | **~35,000** |

**Note:** JSON dataset format reduces file count from 600+ individual files to 8 JSON files.

---

## Development Workflow

### Phase 1: Setup

```bash
# 1. Clone repository
git clone https://github.com/Mauttaram/SecurityEvaluator.git
cd SecurityEvaluator

# 2. Install dependencies
uv sync

# 3. Set up environment
cp sample.env .env
# Edit .env to add GOOGLE_API_KEY

# 4. Verify installation
uv run agentbeats-run --help
```

### Phase 2: Dataset Creation

```bash
# Generate initial dataset
python scripts/generate_dataset.py --category classic --count 100
python scripts/generate_dataset.py --category blind --count 80
# ... repeat for all categories

# Validate dataset
python scripts/validate_dataset.py

# Review metadata
cat scenarios/security/datasets/sql_injection/metadata.json
```

### Phase 3: Green Agent Development

```bash
# Run tests as you develop
pytest tests/test_scoring_engine.py -v

# Test with baseline purple agent
uv run agentbeats-run scenarios/security/scenario.toml

# View logs
uv run agentbeats-run scenarios/security/scenario.toml --show-logs
```

### Phase 4: Purple Agent Testing

```bash
# Start purple agent in separate terminal
python purple_agents/baseline/sql_detector.py --port 9019

# Run evaluation
uv run agentbeats-run scenarios/security/scenario.toml

# Benchmark locally
python scripts/benchmark_purple_agents.py \
  --agent http://localhost:9019 \
  --sample-size 100
```

### Phase 5: Platform Deployment

```bash
# Set up Cloudflare Tunnel
./scripts/setup_cloudflare.sh

# Start green agent with public URL
python scenarios/security/sql_injection_judge.py \
  --host 127.0.0.1 \
  --port 9009 \
  --card-url https://your-tunnel.trycloudflare.com

# Register on AgentBeats.org
# Navigate to https://agentbeats.org
# Register agent with public URL
```

---

## Files to Create (Priority Order)

### High Priority (MVP)

1. ✅ `docs/ANALYSIS.md`
2. ✅ `docs/DESIGN.md`
3. ✅ `docs/SPECIFICATION.md`
4. ✅ `docs/PROJECT_STRUCTURE.md`
5. ⬜ `scenarios/security/models.py` - Data models
6. ⬜ `scenarios/security/dataset_manager.py` - Dataset loading
7. ⬜ `scenarios/security/scoring_engine.py` - Metrics calculation
8. ⬜ `scenarios/security/sql_injection_judge.py` - Main green agent
9. ⬜ `scenarios/security/datasets/sql_injection/metadata.json` - Initial metadata
10. ⬜ 50 initial test case files (25 vulnerable, 25 secure)
11. ⬜ `purple_agents/baseline/sql_detector.py` - Baseline agent
12. ⬜ `tests/test_scoring_engine.py` - Core tests

### Medium Priority (Full Implementation)

13. ⬜ `scenarios/security/test_orchestrator.py` - Orchestration
14. ⬜ `scenarios/security/report_generator.py` - Reporting
15. ⬜ Complete dataset: 500+ test cases
16. ⬜ `purple_agents/llm_based/sql_detector.py` - LLM agent
17. ⬜ `tests/test_integration.py` - Integration tests
18. ⬜ `scripts/generate_dataset.py` - Dataset generator
19. ⬜ `scripts/validate_dataset.py` - Validator
20. ⬜ `docs/QUICKSTART.md` - User guide

### Low Priority (Polish)

21. ⬜ `purple_agents/hybrid/sql_detector.py` - Hybrid agent
22. ⬜ `scripts/benchmark_purple_agents.py` - Local benchmark
23. ⬜ `scripts/setup_cloudflare.sh` - Automation
24. ⬜ Complete test coverage (all modules)
25. ⬜ `docs/EVALUATION_CRITERIA.md` - Detailed methodology
26. ⬜ Performance optimization
27. ⬜ Visualization tools

---

## Git Workflow

### Branch Strategy

```
main                    # Stable releases
├── dev                 # Active development
│   ├── feature/dataset         # Dataset creation
│   ├── feature/green-agent     # Green agent implementation
│   ├── feature/purple-agents   # Purple agent examples
│   └── feature/docs            # Documentation
```

### Commit Conventions

```
feat: Add scoring engine with F1 calculation
fix: Correct dataset metadata validation
docs: Update DESIGN.md with workflow diagrams
test: Add integration tests for green agent
refactor: Simplify test orchestration logic
```

---

**Document Version:** 1.0
**Last Updated:** November 4, 2025
