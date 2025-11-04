"""
Agent Card definition for SQL Injection Detection Benchmark.

This module defines the A2A (Agent-to-Agent) protocol card for the Green Agent,
enabling integration with the AgentBeats platform.
"""

from a2a.types import AgentCard, AgentSkill, AgentCapabilities


def sql_injection_agent_card(agent_name: str, card_url: str) -> AgentCard:
    """
    Create the AgentCard for SQL Injection Detection Benchmark (Green Agent).

    Args:
        agent_name: Name of the agent
        card_url: URL where the agent card is published

    Returns:
        AgentCard for A2A protocol
    """
    skill = AgentSkill(
        id='sql_injection_benchmark',
        name='SQL Injection Detection Benchmark',
        description=(
            'Evaluates Purple Agents on their ability to detect SQL injection vulnerabilities '
            'in code across multiple categories and languages. Supports fixed and adaptive testing modes.'
        ),
        tags=['security', 'sql-injection', 'vulnerability-detection', 'benchmark'],
        examples=["""
{
  "purple_agent_id": "baseline_sql_detector",
  "purple_agent_endpoint": "http://127.0.0.1:8000/detect",
  "config": {
    "mode": "adaptive",
    "test_budget": 100,
    "adaptive_weak_threshold": 0.6
  }
}
"""]
    )

    return AgentCard(
        name=agent_name,
        description=(
            'SQL Injection Detection Benchmark - Green Agent for evaluating security analysis agents '
            'on SQL injection detection. Features adaptive testing with autonomous decision-making.'
        ),
        url=card_url,
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )


def purple_agent_skill_template() -> AgentSkill:
    """
    Template for Purple Agent skill definition (for reference).

    Purple Agents should implement a skill with this interface to be
    evaluated by the SQL Injection Detection Benchmark.

    Returns:
        Template AgentSkill for Purple Agents
    """
    return AgentSkill(
        id="sql_injection_detector",
        name="SQL Injection Detector",
        description=(
            "Analyzes code samples to detect SQL injection vulnerabilities. "
            "Returns detection results with confidence scores and explanations."
        ),
        tags=["security", "sql-injection", "detection", "code-analysis"],
        examples=["""
{
  "test_case_id": "test_001",
  "code": "query = f\\"SELECT * FROM users WHERE id={user_id}\\"",
  "language": "python",
  "category": "classic_sqli"
}
"""]
    )
