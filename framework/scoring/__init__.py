"""
Scoring engines for security evaluation.

Provides dual-perspective scoring:
- GreenAgentScoringEngine: Measures attack effectiveness (TP/FP/FN/TN, F1)
- PurpleAgentScoringEngine: Measures security posture (CVSS, vulnerabilities)
- DualScoringEngine: Coordinates both perspectives

The same test data is evaluated from two different perspectives:
1. Green Agent perspective: How effective is the scanner/attacker?
2. Purple Agent perspective: How secure is the target/defender?
"""

from .greenagent_scoring_engine import GreenAgentScoringEngine
from .purpleagent_scoring_engine import PurpleAgentScoringEngine
from .dual_scoring_engine import DualScoringEngine
from .cvss_calculator import CVSSCalculator, CVSSVector
from .vulnerability_manager import VulnerabilityManager

__all__ = [
    'GreenAgentScoringEngine',
    'PurpleAgentScoringEngine',
    'DualScoringEngine',
    'CVSSCalculator',
    'CVSSVector',
    'VulnerabilityManager',
]
