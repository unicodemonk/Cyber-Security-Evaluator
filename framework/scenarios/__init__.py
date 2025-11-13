"""
Scenario implementations for the Unified Framework.

Attack-type based scenarios (not agent-specific):
- Prompt Injection (LLM attacks, jailbreaks, etc.)
- SQL Injection (coming soon)
- XSS attacks (coming soon)
- Command Injection (coming soon)

Each scenario is generic and works with ANY Purple Agent.
Scenarios provide attack templates that are sent to the target via A2A protocol.
"""

from .prompt_injection import PromptInjectionScenario

__all__ = [
    'PromptInjectionScenario',
]
